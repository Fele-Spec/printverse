#!/usr/bin/env python3
"""Audit STL meshes without trusting the slicer: topology, normals, scale, repairs."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reports"
OUT.mkdir(parents=True, exist_ok=True)


def edge_stats(mesh: trimesh.Trimesh) -> dict:
    edges = np.sort(mesh.edges_sorted, axis=1)
    unique, counts = np.unique(edges, axis=0, return_counts=True)
    return {
        "boundary_edges": int(np.sum(counts == 1)),
        "nonmanifold_edges": int(np.sum(counts != 2)),
        "edges_over_two_faces": int(np.sum(counts > 2)),
        "unique_edges": int(len(unique)),
    }


def audit(path: Path) -> dict:
    # process=True merges coincident STL vertices before topology checks; otherwise every
    # triangle looks disconnected and falsely reports 100% boundary edges.
    mesh = trimesh.load(path, force="mesh", process=True)
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"not a single mesh: {type(mesh)}")
    bounds = mesh.bounds
    extents = mesh.extents
    stats = edge_stats(mesh)
    degenerate = int(np.sum(mesh.area_faces < 1e-12))
    duplicate = 0
    try:
        duplicate = int(len(trimesh.grouping.group_rows(np.sort(mesh.faces, axis=1), require_count=2)))
    except Exception:
        pass
    self_intersect = None
    try:
        if hasattr(trimesh.intersections, "mesh_self_intersection"):
            self_intersect = int(len(trimesh.intersections.mesh_self_intersection(mesh)))
    except Exception as exc:
        self_intersect = f"error: {exc}"
    result = {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "euler_number": int(mesh.euler_number),
        "body_count": int(mesh.body_count),
        "volume_mm3": round(float(abs(mesh.volume)), 4),
        "area_mm2": round(float(mesh.area), 4),
        "extents_mm": [round(float(x), 4) for x in extents],
        "bounds_mm": [[round(float(x), 4) for x in bounds[0]], [round(float(x), 4) for x in bounds[1]]],
        "degenerate_faces": degenerate,
        "duplicate_face_pairs": duplicate,
        "self_intersections": self_intersect,
        **stats,
    }
    result["print_preflight_pass"] = bool(
        mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
        and stats["nonmanifold_edges"] == 0 and degenerate == 0
    )
    return result


def repair_copy(path: Path, record: dict) -> dict | None:
    if record["print_preflight_pass"]:
        return None
    mesh = trimesh.load(path, force="mesh", process=True)
    trimesh.repair.fix_normals(mesh, multibody=True)
    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_winding(mesh)
    target = ROOT / "assets" / "processed" / f"{path.stem}_repaired.stl"
    target.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(target)
    return {"source": record["file"], "repaired": str(target.relative_to(ROOT)).replace("\\", "/"),
            "watertight": bool(mesh.is_watertight), "winding_consistent": bool(mesh.is_winding_consistent)}


def main() -> int:
    paths = [
        ROOT / "assets/test-models/cube.stl",
        ROOT / "assets/source/voron-v2.4r2-300/STLs/Test_Prints/Filament_Card.stl",
        ROOT / "assets/source/voron-v2.4r2-300/STLs/Tools/MGN9_rail_guide_x2.stl",
        ROOT / "assets/source/voron-v2.4r2-300/STLs/Gantry/X_Axis/X_Carriage.stl",
        ROOT / "tools/OrcaSlicer-2.4.2/resources/profiles/Voron/Voron_300_build_plate.stl",
    ]
    # Pick a real gantry part even if the historical name changed.
    if not paths[3].exists():
        candidates = sorted((ROOT / "assets/source/voron-v2.4r2-300/STLs/Gantry/X_Axis").rglob("*.stl"),
                            key=lambda p: p.stat().st_size, reverse=True)
        if candidates:
            paths[3] = candidates[0]
    records = []
    repairs = []
    for path in paths:
        if not path.exists():
            records.append({"file": str(path), "error": "missing"})
            continue
        try:
            record = audit(path)
            records.append(record)
            repair = repair_copy(path, record)
            if repair:
                repairs.append(repair)
            print(f"{'PASS' if record['print_preflight_pass'] else 'CHECK'} {path.name}: "
                  f"watertight={record['watertight']} nonmanifold={record['nonmanifold_edges']} "
                  f"faces={record['faces']} extents={record['extents_mm']}")
        except Exception as exc:
            records.append({"file": str(path), "error": repr(exc)})
            print(f"ERROR {path}: {exc}", file=sys.stderr)
    report = {
        "tool": f"trimesh {trimesh.__version__}",
        "unit_assumption": "STL coordinates treated as millimetres",
        "records": records,
        "repairs": repairs,
    }
    (OUT / "mesh_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "mesh_audit.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "vertices", "faces", "watertight", "winding_consistent", "is_volume",
                         "nonmanifold_edges", "boundary_edges", "degenerate_faces", "duplicate_face_pairs",
                         "extents_x_mm", "extents_y_mm", "extents_z_mm", "volume_mm3", "print_preflight_pass"])
        for r in records:
            writer.writerow([r.get("file"), r.get("vertices"), r.get("faces"), r.get("watertight"),
                             r.get("winding_consistent"), r.get("is_volume"), r.get("nonmanifold_edges"),
                             r.get("boundary_edges"), r.get("degenerate_faces"), r.get("duplicate_face_pairs"),
                             (r.get("extents_mm") or [None, None, None])[0],
                             (r.get("extents_mm") or [None, None, None])[1],
                             (r.get("extents_mm") or [None, None, None])[2],
                             r.get("volume_mm3"), r.get("print_preflight_pass")])
    print(f"wrote {OUT / 'mesh_audit.json'} and mesh_audit.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
