"""FastAPI application for the PrintVerse virtual print loop."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from . import db
from .image3d import router as image3d_router
from .image3d import store as image3d_store
from .slicer import SliceError, slice_stl

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "runtime"
UPLOADS = RUNTIME / "uploads"
JOBS = RUNTIME / "jobs"
for p in (RUNTIME, UPLOADS, JOBS):
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PrintVerse API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:4173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/runtime", StaticFiles(directory=RUNTIME), name="runtime")
app.include_router(image3d_router.router)


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


@app.get("/api/wallet")
def wallet(user_id: str = db.DEMO_USER) -> dict:
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
        "model_url": f"/runtime/jobs/{job_id}/model.stl",
        "gcode_url": f"/runtime/jobs/{job_id}/model.gcode",
    }


@app.post("/api/jobs")
async def create_job(file: UploadFile = File(...)) -> dict:
    name = file.filename or "upload.stl"
    if not name.lower().endswith(".stl"):
        raise HTTPException(415, "only STL is supported in phase 2")
    data = await file.read()
    if len(data) < 84:
        raise HTTPException(422, "STL file is too small")
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "STL exceeds 50 MB")
    job_id = uuid.uuid4().hex
    job_dir = JOBS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    stl = job_dir / "model.stl"
    stl.write_bytes(data)
    db.create_job(db.DEMO_USER, name, str(stl.relative_to(ROOT)).replace("\\", "/"), job_id)
    try:
        sliced = await run_in_threadpool(slice_stl, stl, job_dir, job_id)
        mass_mg = max(1, round(sliced["mass_g"] * 1000))
        job = db.set_job_sliced(
            job_id, sliced["gcode_path"], sliced["toolpath_path"], mass_mg,
            sliced["time_s"], sliced["layers"], sliced["warnings"],
        )
        job = await run_in_threadpool(db.reserve_for_job, job_id, db.DEMO_USER, mass_mg)
        return {**_job_response(job), "wallet": db.wallet()}
    except db.InsufficientFilament as exc:
        with db.connect() as conn:
            conn.execute("UPDATE jobs SET status='payment_required' WHERE id=?", (job_id,))
        raise HTTPException(402, str(exc))
    except SliceError as exc:
        with db.connect() as conn:
            conn.execute("UPDATE jobs SET status='slice_failed', warnings=? WHERE id=?", (str(exc)[-2000:], job_id))
        raise HTTPException(422, f"slicing failed: {exc}")


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    try:
        job = db.get_job(job_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    return {**_job_response(job), "wallet": db.wallet()}


@app.post("/api/jobs/{job_id}/complete")
def complete(job_id: str, body: CompleteRequest) -> dict:
    try:
        job = db.complete_job(job_id, body.user_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    return {**_job_response(job), "wallet": db.wallet(body.user_id)}


@app.post("/api/jobs/{job_id}/cancel")
def cancel(job_id: str, body: CompleteRequest) -> dict:
    try:
        job = db.cancel_job(job_id, body.user_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    return {**_job_response(job), "wallet": db.wallet(body.user_id)}


@app.get("/api/collection")
def collection(user_id: str = db.DEMO_USER) -> dict:
    return {"items": db.list_collection(user_id), "wallet": db.wallet(user_id)}


@app.post("/api/collection")
def add_collection(body: CollectionRequest) -> dict:
    try:
        job = db.get_job(body.job_id)
    except KeyError:
        raise HTTPException(404, "unknown job")
    if job["status"] != "completed":
        raise HTTPException(409, "only completed prints can be collected")
    item = db.add_collection(body.user_id, body.job_id, job["name"], job["mass_mg"],
                             str((JOBS / body.job_id / "model.stl").relative_to(ROOT)).replace("\\", "/"))
    return {"item": item, "wallet": db.wallet(body.user_id)}
