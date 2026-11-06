"""Phase-3 FreeCAD placement audit and trial module export.

Imports the 267 MB STEP once, records all FreeCAD objects with parent paths and
global placements, saves the document for reuse, and meshes selected modules to
per-part STLs.  GLB assembly happens in the normal project venv with trimesh.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

import FreeCAD
import Import
import MeshPart

ROOT = Path(r"C:\Users\someb\Desktop\printverse")
STEP = ROOT / "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
CACHE = ROOT / ".cache" / "cad_parts"
PLACEMENTS = ROOT / "manifests" / "placements.json"
MODULE_PARTS = ROOT / "manifests" / "module-parts.json"
FCSTD = ROOT / ".cache" / "voron_full.FCStd"
TRIAL_MODULES = {"FRAME", "XY_GANTRY", "TOOLHEAD", "BUILD_PLATFORM"}


def matrix_of(placement):
    m = placement.toMatrix()
    return [
        [round(m.A11, 6), round(m.A12, 6), round(m.A13, 6), round(m.A14, 6)],
        [round(m.A21, 6), round(m.A22, 6), round(m.A23, 6), round(m.A24, 6)],
        [round(m.A31, 6), round(m.A32, 6), round(m.A33, 6), round(m.A34, 6)],
        [0, 0, 0, 1],
    ]


def classify(path: str, label: str) -> str:
    p = f"{path} / {label}".lower()
    if any(k in p for k in ("toolheads", "x carriage", "clockwork", "extruder", "hotend", "dragon", "revo", "mosquito", "fan assembly", "printhead")):
        return "TOOLHEAD"
    if "gantry" in p:
        return "XY_GANTRY"
    if "z assembly" in p or "z drive" in p or "z idler" in p or "z joint" in p:
        return "Z_DRIVE"
    if any(k in p for k in ("bed components", "10in bed", "bed heater", "mic6", "flex sheet", "magnet sheet", "build plate")):
        return "BUILD_PLATFORM"
    if any(k in p for k in ("electronics", "controller", "psu", "octopus", "skr", "raspberry", "ssr", "wago")):
        return "ELECTRONICS"
    if any(k in p for k in ("cable chain", "wiring", "wire", "ptfe", "cable")):
        return "WIRING"
    if any(k in p for k in ("panels", "panel", "skirt", "door", "enclosure")):
        return "ENCLOSURE"
    if any(k in p for k in ("frame", "extrusion", "spool holder", "exhaust filter")):
        return "FRAME"
    return "FRAME"


def main() -> int:
    t0 = time.time()
    print("IMPORT_START", STEP.stat().st_size, flush=True)
    doc = FreeCAD.newDocument("phase3_full")
    Import.insert(str(STEP), doc.Name)
    print("INSERT_DONE", round(time.time() - t0, 2), flush=True)
    doc.recompute()
    print("RECOMPUTE_DONE", round(time.time() - t0, 2), flush=True)

    objects = list(doc.Objects)
    path_cache = {}

    def path_of(obj, depth=0):
        if obj.Name in path_cache:
            return path_cache[obj.Name]
        if depth > 12:
            return obj.Label
        parents = list(getattr(obj, "InList", []) or [])
        if not parents:
            path = obj.Label
        else:
            path = path_of(parents[0], depth + 1) + " / " + obj.Label
        path_cache[obj.Name] = path
        return path

    records = []
    for i, obj in enumerate(objects):
        try:
            global_p = obj.getGlobalPlacement() if hasattr(obj, "getGlobalPlacement") else obj.Placement
        except Exception:
            global_p = obj.Placement
        shape = getattr(obj, "Shape", None)
        has_shape = bool(shape is not None and not shape.isNull())
        dims = []
        volume = 0.0
        bb = None
        if has_shape:
            try:
                world_shape = shape.copy()
                world_shape.transformShape(global_p.toMatrix())
                b = world_shape.BoundBox
                bb = [round(b.XMin, 4), round(b.YMin, 4), round(b.ZMin, 4),
                      round(b.XMax, 4), round(b.YMax, 4), round(b.ZMax, 4)]
                dims = [round(b.XLength, 4), round(b.YLength, 4), round(b.ZLength, 4)]
                volume = float(world_shape.Volume)
            except Exception:
                pass
        path = path_of(obj)
        module = classify(path, obj.Label)
        pid = f"F{i+1:04d}"
        records.append({
            "placement_id": pid,
            "part_id": obj.Name,
            "part_name": obj.Label,
            "source_document": "VORON2.4_Assembly.step",
            "source_object": obj.Name,
            "geometry_reference": f"FreeCAD:{obj.Name}",
            "parent_id": (f"F{objects.index(obj.InList[0])+1:04d}" if getattr(obj, "InList", None) else None),
            "parent_name": (obj.InList[0].Label if getattr(obj, "InList", None) else None),
            "path": path,
            "module": module,
            "type": obj.TypeId,
            "local_transform": matrix_of(obj.Placement),
            "world_transform": matrix_of(global_p),
            "dimensions_mm": dims,
            "bounding_box_mm": bb,
            "volume_mm3": round(volume, 3),
            "has_geometry": has_shape,
            "movable": module in {"XY_GANTRY", "TOOLHEAD", "Z_DRIVE", "BUILD_PLATFORM"},
            "material": "UNASSIGNED",
            "verification_status": "GEOMETRY_PRESENT" if has_shape else "CONSTRUCTION_NO_SHAPE",
        })

    # Duplicate and zero-volume checks.
    from collections import Counter
    dup_names = [k for k, v in Counter(r["part_id"] for r in records).items() if v > 1]
    zero = [r["placement_id"] for r in records if r["has_geometry"] and r["volume_mm3"] <= 1e-6]
    audit = {
        "source": str(STEP.relative_to(ROOT)).replace("\\", "/"),
        "total_objects": len(objects),
        "records": len(records),
        "with_geometry": sum(r["has_geometry"] for r in records),
        "construction": sum(not r["has_geometry"] for r in records),
        "duplicate_part_ids": dup_names,
        "zero_volume": zero,
        "unit": "mm",
        "elapsed_import_s": round(time.time() - t0, 2),
    }
    PLACEMENTS.write_text(json.dumps({"audit": audit, "placements": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PLACEMENTS_WRITTEN", len(records), audit["with_geometry"], audit["construction"], flush=True)

    try:
        doc.saveAs(str(FCSTD))
        print("FCSTD_SAVED", FCSTD.stat().st_size, flush=True)
    except Exception as exc:
        print("FCSTD_SAVE_FAILED", repr(exc), flush=True)

    # Trial module mesh export: keep each part separate for metadata/selection.
    module_parts: dict[str, list[dict]] = {}
    for rec, obj in zip(records, objects):
        if not rec["has_geometry"] or rec["module"] not in TRIAL_MODULES:
            continue
        out_dir = CACHE / rec["module"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{rec['placement_id']}.stl"
        try:
            world_shape = obj.Shape.copy()
            world_shape.transformShape((obj.getGlobalPlacement() if hasattr(obj, "getGlobalPlacement") else obj.Placement).toMatrix())
            mesh = MeshPart.meshFromShape(Shape=world_shape, LinearDeflection=0.8, AngularDeflection=0.55, Relative=False)
            if mesh.CountFacets == 0:
                continue
            mesh.write(str(out))
            rec["mesh_file"] = str(out.relative_to(ROOT)).replace("\\", "/")
            rec["mesh_faces"] = int(mesh.CountFacets)
            module_parts.setdefault(rec["module"], []).append({
                "placement_id": rec["placement_id"], "part_name": rec["part_name"],
                "path": rec["path"], "mesh_file": rec["mesh_file"], "faces": rec["mesh_faces"],
            })
        except Exception as exc:
            rec["mesh_error"] = repr(exc)
        if len(module_parts.get(rec["module"], [])) % 25 == 0:
            print("MESH", rec["module"], len(module_parts.get(rec["module"], [])), flush=True)

    MODULE_PARTS.write_text(json.dumps(module_parts, ensure_ascii=False, indent=2), encoding="utf-8")
    PLACEMENTS.write_text(json.dumps({"audit": audit, "placements": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MODULE_PARTS", {k: len(v) for k, v in module_parts.items()}, flush=True)
    print("DONE", round(time.time() - t0, 2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
