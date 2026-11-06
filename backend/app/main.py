"""FastAPI application for the PrintVerse virtual print loop."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from . import db
from .access import public_status, resolve_user
from .image3d import router as image3d_router
from .image3d import store as image3d_store
from .mesh_router import router as mesh_router
from .slicer import SliceError, slice_stl
from .step_import import StepImportError, convert_step
from .dxf_import import DxfImportError, convert_dxf

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "runtime"
UPLOADS = RUNTIME / "uploads"
JOBS = RUNTIME / "jobs"
for p in (RUNTIME, UPLOADS, JOBS):
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PrintVerse API", version="0.2.0")
_cors = os.environ.get("PRINTVERSE_CORS_ORIGINS", "http://127.0.0.1:4173,http://localhost:4173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/runtime", StaticFiles(directory=RUNTIME), name="runtime")
app.include_router(image3d_router.router)
app.include_router(mesh_router)


class CompleteRequest(BaseModel):
    user_id: str = db.DEMO_USER


class CollectionRequest(BaseModel):
    job_id: str
    user_id: str = db.DEMO_USER


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    image3d_store.init_db()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "printverse-api", "version": "0.2.0"}


@app.get("/api/machine")
def machine() -> dict:
    p = ROOT / "manifests" / "mechanical-parameters.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    profile = json.loads((ROOT / "configs/machine/voron-v2.4r2-300-0.4.json").read_text(encoding="utf-8"))
    return {
        "machine": data["machine"],
        "resolution": data["resolution"],
        "parameters": data["parameters"],
        "orca_printable_area": profile["printable_area"],
        "orca_printable_height": profile["printable_height"],
    }


@app.get("/api/access")
def access(request: Request) -> dict:
    return public_status(request)


@app.get("/api/wallet")
def wallet(request: Request) -> dict:
    user_id = resolve_user(request)
    try:
        return db.wallet(user_id)
    except KeyError:
        raise HTTPException(404, "unknown user")


def _job_response(job: dict) -> dict:
    job_id = job["id"]
    return {
        "id": job_id,
        "name": job["name"],
        "status": job["status"],
        "mass_g": round(job["mass_mg"] / 1000, 4),
        "layers": job["layers"],
        "time_s": job["estimated_time_s"],
        "free_print": bool(job["free_print"]),
        "reserved_g": round(job["reserved_mg"] / 1000, 4),
        "warnings": job["warnings"],
        "toolpath_url": f"/runtime/jobs/{job_id}/toolpath.json",
        "model_url": f"/runtime/jobs/{job_id}/display.stl" if (JOBS / job_id / "display.stl").exists() else f"/runtime/jobs/{job_id}/{Path(job['stl_path']).name}",
        "color_url": f"/runtime/jobs/{job_id}/color.glb" if job.get("color_path") else None,
        "gcode_url": f"/runtime/jobs/{job_id}/model.gcode",
    }


@app.post("/api/jobs")
async def create_job(request: Request, file: UploadFile = File(...), color_url: str = Form("")) -> dict:
    user_id = resolve_user(request)
    name = file.filename or "upload.stl"
    suffix = Path(name).suffix.lower()
    if suffix not in {".stl", ".3mf", ".obj", ".glb", ".gltf", ".step", ".stp", ".dxf"}:
        raise HTTPException(415, "支持 STL/3MF/OBJ/GLB/STEP/DXF")
    data = await file.read()
    if len(data) < 84:
        raise HTTPException(422, "模型文件过小")
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "模型超过 50 MB")
    job_id = uuid.uuid4().hex
    job_dir = JOBS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    model = job_dir / f"model{suffix}"
    model.write_bytes(data)
    if suffix in {".step", ".stp"}:
        try:
            convert_step(model, job_dir / "display.stl")
        except StepImportError as exc:
            raise HTTPException(422, f"STEP 无法转换: {exc}")
    elif suffix == ".dxf":
        try:
            convert_dxf(model, job_dir / "display.stl")
        except DxfImportError as exc:
            raise HTTPException(422, f"DXF 无法拉伸: {exc}")
    elif suffix in {".3mf", ".obj", ".glb", ".gltf"}:
        try:
            import trimesh
            display = trimesh.load(model, force="mesh", process=True)
            display.export(job_dir / "display.stl")
        except Exception as exc:
            raise HTTPException(422, f"{suffix[1:].upper()} 无法读取: {exc}")
    db.create_job(user_id, name, str(model.relative_to(ROOT)).replace("\\", "/"), job_id)
    # Preserve the generated colour GLB; STL remains the slicer geometry.
    if color_url.startswith("/runtime/image3d/"):
        source = (ROOT / color_url.lstrip("/")).resolve()
        allowed = (RUNTIME / "image3d").resolve()
        if source.is_file() and (source == allowed or allowed in source.parents):
            target = job_dir / "color.glb"
            shutil.copy2(source, target)
            db.set_job_color(job_id, str(target.relative_to(ROOT)).replace("\\", "/"))
    try:
        slice_input = job_dir / "display.stl" if suffix in {".obj", ".glb", ".gltf", ".step", ".stp", ".dxf"} else model
        sliced = await run_in_threadpool(slice_stl, slice_input, job_dir, job_id)
        mass_mg = max(1, round(sliced["mass_g"] * 1000))
        job = db.set_job_sliced(
            job_id, sliced["gcode_path"], sliced["toolpath_path"], mass_mg,
            sliced["time_s"], sliced["layers"], sliced["warnings"],
        )
        job = await run_in_threadpool(db.reserve_for_job, job_id, user_id, mass_mg)
        return {**_job_response(job), "wallet": db.wallet(user_id)}
    except db.InsufficientFilament as exc:
        with db.connect() as conn:
            conn.execute("UPDATE jobs SET status='payment_required' WHERE id=?", (job_id,))
        raise HTTPException(402, str(exc))
    except SliceError as exc:
        with db.connect() as conn:
            conn.execute("UPDATE jobs SET status='slice_failed', warnings=? WHERE id=?", (str(exc)[-2000:], job_id))
        raise HTTPException(422, f"slicing failed: {exc}")


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, request: Request) -> dict:
    user_id = resolve_user(request)
    try:
        job = db.get_job(job_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    if job["user_id"] != user_id:
        raise HTTPException(404, "unknown job")
    return {**_job_response(job), "wallet": db.wallet(user_id)}


@app.post("/api/jobs/{job_id}/complete")
def complete(job_id: str, request: Request) -> dict:
    user_id = resolve_user(request)
    try:
        job = db.complete_job(job_id, user_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    return {**_job_response(job), "wallet": db.wallet(user_id)}


@app.post("/api/jobs/{job_id}/cancel")
def cancel(job_id: str, request: Request) -> dict:
    user_id = resolve_user(request)
    try:
        job = db.cancel_job(job_id, user_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    return {**_job_response(job), "wallet": db.wallet(user_id)}


@app.get("/api/collection")
def collection(request: Request) -> dict:
    user_id = resolve_user(request)
    return {"items": db.list_collection(user_id), "wallet": db.wallet(user_id)}


@app.post("/api/collection")
def add_collection(body: CollectionRequest, request: Request) -> dict:
    user_id = resolve_user(request)
    try:
        job = db.get_job(body.job_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    if job["user_id"] != user_id:
        raise HTTPException(404, "unknown job")
    if job["status"] != "completed":
        raise HTTPException(409, "only completed prints can be collected")
    preferred = job.get("color_path") or str((JOBS / body.job_id / "model.stl").relative_to(ROOT)).replace("\\", "/")
    display_name = (job["name"].rsplit(".", 1)[0] + "（彩色）") if job.get("color_path") else job["name"]
    item = db.add_collection(user_id, body.job_id, display_name, job["mass_mg"], preferred)
    return {"item": item, "wallet": db.wallet(user_id)}
