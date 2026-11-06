"""DXF engineering profile -> extruded mesh test."""
from __future__ import annotations

import uuid
from pathlib import Path

import ezdxf
import trimesh

from backend.app.dxf_import import convert_dxf

ROOT = Path(__file__).resolve().parents[2]


def test_dxf_profile_extrudes_to_closed_mesh():
    work = ROOT / "runtime" / f"test-dxf-{uuid.uuid4().hex}"
    work.mkdir(parents=True, exist_ok=True)
    src = work / "profile.dxf"
    dst = work / "profile.stl"
    try:
        doc = ezdxf.new()
        doc.modelspace().add_lwpolyline([(0, 0), (40, 0), (40, 20), (0, 20)], close=True)
        doc.saveas(src)
        info = convert_dxf(src, dst)
        assert info["profiles"] == 1
        mesh = trimesh.load(dst, force="mesh", process=True)
        assert mesh.is_watertight
        assert mesh.volume > 0
        assert abs(max(mesh.extents) - 40) < 0.01
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
