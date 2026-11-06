"""Basic DXF engineering-drawing import: closed 2D contours -> extruded mesh.

This is a deterministic extrusion of closed DXF profiles, not a parametric CAD
feature reconstruction. It is intentionally labelled DXF_EXTRUDE in the API.
"""
from __future__ import annotations

from pathlib import Path

import ezdxf
import trimesh
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]


class DxfImportError(RuntimeError):
    pass


def _profiles(src: Path) -> list[Polygon]:
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    polygons: list[Polygon] = []
    for entity in msp:
        kind = entity.dxftype()
        if kind == "LWPOLYLINE" and entity.closed:
            pts = [(float(p[0]), float(p[1])) for p in entity.get_points("xy")]
            if len(pts) >= 3:
                polygons.append(Polygon(pts))
        elif kind == "POLYLINE" and entity.is_closed:
            pts = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in entity.vertices]
            if len(pts) >= 3:
                polygons.append(Polygon(pts))
        elif kind == "CIRCLE":
            c = entity.dxf.center
            polygons.append(Point(float(c.x), float(c.y)).buffer(float(entity.dxf.radius), resolution=64))
    return [p for p in polygons if p.is_valid and p.area > 0]


def convert_dxf(src: Path, dst: Path, height_mm: float = 3.0) -> dict:
    try:
        profiles = _profiles(src)
    except Exception as exc:
        raise DxfImportError(f"DXF read failed: {exc}") from exc
    if not profiles:
        raise DxfImportError("DXF has no closed LWPOLYLINE/POLYLINE/CIRCLE profiles")
    merged = unary_union(profiles)
    if merged.is_empty:
        raise DxfImportError("DXF profiles are empty after union")
    # MultiPolygon / Polygon both work with trimesh's extrude_polygon.
    mesh = trimesh.creation.extrude_polygon(merged, height=height_mm)
    mesh.export(dst, file_type="stl")
    return {"profiles": len(profiles), "height_mm": height_mm,
            "bounds": [round(float(v), 3) for v in mesh.extents],
            "triangles": int(len(mesh.faces))}
