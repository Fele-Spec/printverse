"""Colour-aware mesh preparation and export for PrintVerse.

GLB is the primary visual asset. STL/3MF/OBJ are derived from the same mesh so
the coloured display and the slicer input cannot silently diverge.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]


def _wall_thickness(mesh: trimesh.Trimesh, samples: int = 64) -> float | None:
    """Approximate local wall thickness by inward ray casting.

    This is a geometric screening value, not a slicer-calibrated wall test. Open
    meshes return None rather than a made-up number.
    """
    if not mesh.is_watertight or len(mesh.faces) == 0:
        return None
    count = min(samples, len(mesh.faces))
    idx = np.linspace(0, len(mesh.faces) - 1, count).astype(np.int64)
    distances: list[float] = []
    for i in idx:
        origin = mesh.triangles_center[i] - mesh.face_normals[i] * 0.01
        direction = -mesh.face_normals[i]
        try:
            locations, _, _ = mesh.ray.intersects_location(
                ray_origins=[origin], ray_directions=[direction], multiple_hits=False
            )
        except Exception:
            continue
        if len(locations):
            distances.append(float(np.linalg.norm(locations[0] - origin)))
    if not distances:
        return None
    distances = np.asarray(distances, dtype=float)
    distances = distances[np.isfinite(distances) & (distances > 0.05)]
    if len(distances) == 0:
        return None
    # The 10th percentile avoids a few grazing/edge hits dominating the result.
    return round(float(np.percentile(distances, 10)), 3)


def inspect_mesh(mesh: trimesh.Trimesh) -> dict:
    min_z = float(mesh.bounds[0][2]) if len(mesh.bounds) else 0.0
    normals = mesh.face_normals
    centers = mesh.triangles_center
    # Exclude the bed-facing bottom; an overhang above the bed is the useful signal.
    overhang = (normals[:, 2] < -0.7) & (centers[:, 2] > min_z + 1.2)
    overhang_area = float(mesh.area_faces[overhang].sum()) if len(mesh.faces) else 0.0
    thickness = _wall_thickness(mesh)
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_mm3": round(float(mesh.volume), 3),
        "area_mm2": round(float(mesh.area), 2),
        "extents_mm": [round(float(v), 3) for v in mesh.extents],
        "body_count": int(mesh.body_count) if hasattr(mesh, "body_count") else None,
        "overhang_area_mm2": round(overhang_area, 2),
        "support_required_approx": bool(overhang_area > max(50.0, float(mesh.area) * 0.02)),
        "wall_thickness_min_mm": thickness,
        "wall_method": "inward_ray_10th_percentile" if thickness is not None else "NOT_PERFORMED",
        "thin_wall_suspect": bool(thickness is not None and thickness < 1.2),
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
