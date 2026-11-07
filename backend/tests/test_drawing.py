"""Raster engineering drawing -> extruded mesh test."""
from __future__ import annotations

import uuid
from pathlib import Path

import trimesh
from PIL import Image, ImageDraw

from backend.app.image3d.drawing import DrawingProvider
from backend.app.image3d.types import GenerationRequest

ROOT = Path(__file__).resolve().parents[2]


def test_drawing_contour_extrudes_to_closed_mesh():
    work = ROOT / "runtime" / f"test-drawing-{uuid.uuid4().hex}"
    work.mkdir(parents=True, exist_ok=True)
    src = work / "drawing.png"
    try:
        im = Image.new("RGB", (600, 400), "white")
        d = ImageDraw.Draw(im)
        d.rectangle((80, 80, 520, 320), outline="black", width=5)
        im.save(src)
        r = DrawingProvider().generate(GenerationRequest(
            job_id=f"test-drawing-{uuid.uuid4().hex}", image_path=str(src),
            options={"width_mm": 80, "height_mm": 3},
        ))
        assert r.output_format == "glb"
        assert r.geometry_status == "DRAWING_EXTRUDE"
        mesh = trimesh.load(ROOT / r.local_path, force="mesh", process=True)
        assert mesh.is_watertight
        assert mesh.volume > 0
        assert abs(max(mesh.extents) - 80) < 0.5
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
