"""Colour asset export tests: GLB primary + derived STL/3MF/OBJ."""
from __future__ import annotations

from pathlib import Path
import uuid

import trimesh

from backend.app.mesh_prep import export_bundle, inspect_mesh, repair_and_scale


def test_export_bundle_keeps_glb_and_geometry():
    mesh = trimesh.creation.box((20, 20, 20))
    d = Path(__file__).resolve().parents[2] / "runtime" / f"test-export-{uuid.uuid4().hex}"
    try:
        paths = export_bundle(mesh, d, "cube")
        assert set(paths) == {"glb", "stl", "3mf", "obj"}
        assert all((d / Path(p).name).exists() for p in paths.values())
        loaded = trimesh.load(paths["glb"], force="mesh", process=True)
        assert loaded.is_watertight and len(loaded.faces) == 12
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def test_repair_scales_and_preserves_positive_volume():
    mesh = trimesh.creation.box((2, 2, 2))
    fixed, stats = repair_and_scale(mesh, 80)
    assert abs(max(fixed.extents) - 80) < 1e-6
    assert fixed.is_watertight
    assert fixed.volume > 0
    assert stats["repaired"]["volume_mm3"] > 0
    info = inspect_mesh(fixed)
    assert info["winding_consistent"] is True
    assert info["wall_thickness_min_mm"] is not None
    assert info["support_required_approx"] is False
