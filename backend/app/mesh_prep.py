"""Colour-aware mesh preparation and export for PrintVerse.

GLB is the primary visual asset. STL/3MF/OBJ are derived from the same mesh so
the coloured display and the slicer input cannot silently diverge.
"""
from __future__ import annotations

from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[2]


def inspect_mesh(mesh: trimesh.Trimesh) -> dict:
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_mm3": round(float(mesh.volume), 3),
        "area_mm2": round(float(mesh.area), 2),
        "extents_mm": [round(float(v), 3) for v in mesh.extents],
        "body_count": int(mesh.body_count) if hasattr(mesh, "body_count") else None,
    }


def repair_and_scale(mesh: trimesh.Trimesh, target_mm: float = 80.0) -> tuple[trimesh.Trimesh, dict]:
    """Repair a copy, normalize longest side, keep colour visual intact."""
    out = mesh.copy()
    raw_stats = inspect_mesh(out)
    max_extent = float(max(out.extents)) if len(out.extents) else 0.0
    scale = target_mm / max_extent if max_extent > 0 else 1.0
    if abs(scale - 1.0) > 1e-9:
        out.apply_scale(scale)
    out.fix_normals()
    if not out.is_watertight:
        out.fill_holes()
    trimesh.repair.fix_winding(out)
    trimesh.repair.fix_normals(out)
    if out.volume < 0:
        out.invert()
    return out, {
        "raw": raw_stats,
        "scale_to_mm": round(scale, 6),
        "repaired": inspect_mesh(out),
        "visual_kind": getattr(out.visual, "kind", None),
    }


def export_bundle(mesh: trimesh.Trimesh, out_dir: Path, stem: str = "model") -> dict:
    """Export colour GLB plus geometry formats from the same repaired mesh."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for fmt in ("glb", "stl", "3mf", "obj"):
        p = out_dir / f"{stem}.{fmt}"
        try:
            mesh.export(p, file_type=fmt)
            paths[fmt] = p
        except Exception:
            # Keep going: a missing optional exporter must not hide a successful GLB.
            if p.exists():
                p.unlink()
    if "glb" not in paths:
        raise RuntimeError("GLB export failed; colour primary asset is mandatory")
    return {k: str(v.relative_to(ROOT)).replace("\\", "/") for k, v in paths.items()}
