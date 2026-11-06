"""Mesh inspection/repair API: colour GLB plus derived slicer formats."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import trimesh
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .mesh_prep import export_bundle, inspect_mesh, repair_and_scale

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runtime" / "mesh"
OUT.mkdir(parents=True, exist_ok=True)
router = APIRouter(prefix="/api/mesh", tags=["mesh"])

ALLOWED = {".stl", ".3mf", ".glb", ".gltf", ".obj"}


def _load(upload: UploadFile, data: bytes) -> tuple[Path, Path]:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(415, "支持 STL/3MF/GLB/GLTF/OBJ")
    if len(data) > 80 * 1024 * 1024:
        raise HTTPException(413, "模型超过 80 MB")
    work = OUT / uuid.uuid4().hex
    work.mkdir(parents=True, exist_ok=True)
    src = work / f"input{suffix}"
    src.write_bytes(data)
    try:
        mesh = trimesh.load(src, force="mesh", process=True)
    except Exception as exc:
        raise HTTPException(422, f"无法读取模型: {exc}")
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise HTTPException(422, "模型没有可用三角面")
    return work, src


@router.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    work, src = _load(file, data)
    mesh = trimesh.load(src, force="mesh", process=True)
    return {"name": file.filename, "inspection": inspect_mesh(mesh), "input": str(src.relative_to(ROOT)).replace("\\", "/")}


@router.post("/repair")
async def repair(file: UploadFile = File(...), target_mm: float = Form(80.0)) -> dict:
    if target_mm < 10 or target_mm > 400:
        raise HTTPException(422, "target_mm 必须在 10–400 mm")
    data = await file.read()
    work, src = _load(file, data)
    mesh = trimesh.load(src, force="mesh", process=True)
    fixed, stats = repair_and_scale(mesh, target_mm=target_mm)
    paths = export_bundle(fixed, work, "repaired")
    return {
        "inspection": stats,
        "assets": {k: f"/runtime/mesh/{work.name}/{Path(v).name}" for k, v in paths.items()},
        "note": "GLB 是彩色展示主资产；STL/3MF/OBJ 为派生文件",
    }
