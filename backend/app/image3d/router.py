"""HTTP API for the Image-to-3D provider architecture."""
from __future__ import annotations

import io
from contextlib import closing
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from PIL import Image

from .. import db
from ..access import resolve_user, share_mode
from . import registry, store
from .types import GenerationRequest, ProviderError

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "runtime" / "image3d"
RUNTIME.mkdir(parents=True, exist_ok=True)
router = APIRouter(prefix="/api/image3d", tags=["image3d"])


def _public_job(job: dict) -> dict:
    return {
        "id": job["id"], "provider": job["provider"], "model": job["model"],
        "status": job["status"], "task_id": job["task_id"],
        "output_format": job["output_format"], "output_url": job["output_url"],
        "local_path": job["local_path"], "generation_cost": job["generation_cost"],
        "cost_currency": job["cost_currency"], "cost_basis": job["cost_basis"],
        "texture_status": job["texture_status"], "geometry_status": job["geometry_status"],
        "task_status": job["task_status"], "authorized": bool(job["authorized"]),
        "prompt": job["prompt"], "error": job["error"], "metadata": job["metadata"],
        "created_at": job["created_at"],
    }


@router.get("/providers")
def list_providers() -> dict:
    return {"providers": [p.to_dict() for p in registry.providers()]}


@router.get("/jobs")
def list_jobs(request: Request) -> dict:
    return {"jobs": [_public_job(j) for j in store.list_jobs(resolve_user(request))]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        return _public_job(store.get_job(job_id))
    except KeyError:
        raise HTTPException(404, "unknown image3d job")


@router.post("/jobs")
async def create_job(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    provider: str = Form("auto"),
    prompt: str = Form(""),
    authorized: bool = Form(False),
    budget_cny: float = Form(0.0),
    width_mm: float = Form(0.0),
    height_mm: float = Form(3.0),
) -> dict:
    user_id = resolve_user(request)
    if provider != "auto":
        try:
            info = registry.get_provider(provider).info()
        except KeyError:
            raise HTTPException(404, "unknown provider")
        if info.kind == "analysis":
            raise HTTPException(422, "Kimi analysis is not a mesh provider")
        if share_mode() and user_id != "owner" and info.kind == "cloud":
            raise HTTPException(403, "guest members cannot authorize cloud generation; ask the owner")
        if not info.available:
            raise HTTPException(409, info.reason)
        try:
            registry.authorize(provider, authorized, budget_cny)
        except ProviderError as exc:
            raise HTTPException(402 if exc.status == "authorization_required" else 409, str(exc))
    else:
        provider = registry.choose_auto()
    name = (file.filename or "input.png").lower()
    if not name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        raise HTTPException(415, "PNG/JPEG/WebP image required")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "image exceeds 20 MB")
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
    except Exception:
        raise HTTPException(422, "invalid image")
    job = store.create_job(user_id=user_id, provider=provider, model=registry.get_provider(provider).model,
                           input_path="", prompt=prompt, authorized=authorized)
    job_id = job["id"]
    job_dir = RUNTIME / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "input.png").suffix.lower() or ".png"
    input_path = job_dir / f"input{suffix}"
    input_path.write_bytes(data)
    store.update_job(job_id, status="queued", metadata={"input": str(input_path.relative_to(ROOT)).replace("\\", "/")})
    with closing(db.connect()) as conn, conn:
        conn.execute("UPDATE image3d_jobs SET input_path=? WHERE id=?",
                     (str(input_path.relative_to(ROOT)).replace("\\", "/"), job_id))
    options = {"width_mm": width_mm, "height_mm": height_mm} if provider == "drawing_local" and width_mm > 0 else {}
    background.add_task(_execute, job_id, str(input_path), prompt, authorized, budget_cny, provider, options)
    return _public_job(store.get_job(job_id))


@router.post("/multiview")
async def create_multiview_job(
    request: Request,
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
    prompt: str = Form(""),
) -> dict:
    if len(files) != 3:
        raise HTTPException(422, "需要正面、侧面、顶面三张图片")
    user_id = resolve_user(request)
    provider = "multiview_local"
    job = store.create_job(user_id=user_id, provider=provider, model=registry.get_provider(provider).model,
                           input_path="", prompt=prompt, authorized=False)
    job_id = job["id"]
    job_dir = RUNTIME / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for index, upload in enumerate(files):
        data = await upload.read()
        if len(data) > 20 * 1024 * 1024:
            raise HTTPException(413, "单张图片超过 20 MB")
        suffix = Path(upload.filename or f"view{index}.png").suffix.lower() or ".png"
        path = job_dir / f"view{index}{suffix}"
        path.write_bytes(data)
        paths.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        if index == 0:
            with closing(db.connect()) as conn, conn:
                conn.execute("UPDATE image3d_jobs SET input_path=? WHERE id=?", (paths[0], job_id))
    store.update_job(job_id, status="queued",
                     metadata={"views": ["front", "side", "top"], "image_paths": paths})
    background.add_task(_execute_multiview, job_id, paths, prompt)
    return _public_job(store.get_job(job_id))


def _execute_multiview(job_id: str, image_paths: list[str], prompt: str) -> None:
    store.update_job(job_id, status="running", task_status="running")
    req = GenerationRequest(job_id=job_id, image_path=image_paths[0], prompt=prompt,
                            options={"image_paths": image_paths})
    try:
        result = registry.run("multiview_local", req)
        store.update_job(job_id, status="completed", **result.to_dict())
    except ProviderError as exc:
        store.update_job(job_id, status=exc.status, error=str(exc), task_status=exc.status)
    except Exception as exc:  # noqa: BLE001
        store.update_job(job_id, status="failed", error=str(exc)[-4000:], task_status="failed")


def _execute(job_id: str, image_path: str, prompt: str, authorized: bool, budget_cny: float, provider_id: str, options: dict | None = None) -> None:
    store.update_job(job_id, status="running", task_status="running")
    req = GenerationRequest(job_id=job_id, image_path=image_path, prompt=prompt,
                            authorized=authorized, budget_cny=budget_cny, options=options or {})
    try:
        result = registry.run(provider_id, req, allow_free_fallback=provider_id == "auto")
        store.update_job(job_id, status="completed", **result.to_dict())
    except ProviderError as exc:
        store.update_job(job_id, status=exc.status, error=str(exc), task_status=exc.status,
                         generation_cost=exc.cost, cost_basis="actual" if exc.cost is not None else "unknown")
    except Exception as exc:  # noqa: BLE001
        store.update_job(job_id, status="failed", error=str(exc)[-4000:], task_status="failed")


@router.post("/analyze")
async def analyze(file: UploadFile = File(...), prompt: str = Form("")) -> dict:
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "image exceeds 20 MB")
    tmp = RUNTIME / "_analysis"
    tmp.mkdir(parents=True, exist_ok=True)
    p = tmp / "input.png"
    p.write_bytes(data)
    try:
        return registry.analyze(str(p), prompt)
    except Exception as exc:
        raise HTTPException(502, f"Kimi analysis failed: {exc}")
