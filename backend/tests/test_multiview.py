"""Deterministic three-view silhouette provider test."""
from __future__ import annotations

import uuid
from pathlib import Path

import trimesh
from PIL import Image, ImageDraw

from backend.app.image3d.multiview import MultiViewProvider
from backend.app.image3d.types import GenerationRequest

ROOT = Path(__file__).resolve().parents[2]


def test_multiview_visual_hull_is_watertight_glb():
    work = ROOT / "runtime" / f"test-mv-{uuid.uuid4().hex}"
    work.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in ("front", "side", "top"):
        im = Image.new("RGB", (256, 256), "white")
        d = ImageDraw.Draw(im)
        d.rectangle((64, 48, 192, 208), fill=(60, 120, 200), outline="black", width=2)
        p = work / f"{name}.png"
        im.save(p)
        paths.append(str(p))
    try:
        r = MultiViewProvider().generate(GenerationRequest(
            job_id=f"test-mv-{uuid.uuid4().hex}", image_path=paths[0],
            options={"image_paths": paths},
        ))
        assert r.output_format == "glb"
        assert r.geometry_status == "MULTIVIEW_VISUAL_HULL"
        assert r.local_path.endswith(".glb")
        mesh = trimesh.load(ROOT / r.local_path, force="mesh", process=True)
        assert mesh.is_watertight
        assert mesh.volume > 0
        assert mesh.visual.kind == "vertex"
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
        # Provider output lives in runtime/image3d; leave it as evidence for this run.
