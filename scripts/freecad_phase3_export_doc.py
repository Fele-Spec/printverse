"""Phase-3 export from the saved FCStd document.

Placement semantics verified on the actual document:
  obj.Shape already includes obj.Placement;
  therefore the world shape = obj.Shape * parent.getGlobalPlacement()
  (never global placement again).

The 4,526 placements are all non-Origin objects: 1,686 Part::Feature solids,
355 App::Part assembly nodes, and 2,485 Line/Plane/Point construction objects.
Only Part::Feature is meshed for GLB; construction stays in the audit database.
"""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import FreeCAD
import MeshPart

ROOT = Path(r"C:\Users\someb\Desktop\printverse")
DOC = ROOT / ".cache" / "voron_full.FCStd"
CACHE = ROOT / ".cache" / "cad_parts"
PLACEMENTS = ROOT / "manifests" / "placements.json"
MODULE_PARTS = ROOT / "manifests" / "module-parts.json"
AUDIT_OUT = ROOT / "docs" / "reports" / "placements_audit.json"
TRIAL_MODULES = {"FRAME", "ENCLOSURE", "XY_GANTRY", "Z_DRIVE", "TOOLHEAD", "BUILD_PLATFORM", "ELECTRONICS", "WIRING"}
MATERIAL_RULES = [
    (("gt2", "belt", "timing"), "rubber_belt"),
    (("panel", "acrylic", "door"), "acrylic_panel"),
    (("bed", "mic6", "flex sheet", "magnet"), "brushed_aluminum"),
    (("nozzle", "hotend", "heater", "dragon", "revo", "mosquito"), "brass_nozzle"),
    (("screw", "bolt", "nut", "shim", "washer", "bearing", "m5", "m3", "m4", "m2"), "stainless_steel"),
    (("extrusion", "2020", "frame", "gantry", "rail", "mgn"), "anodized_aluminum"),
    (("fan", "blower", "duct", "printed", "abs", "asa"), "engineering_plastic"),
    (("wire", "cable", "chain", "ptfe"), "silicone_cable"),
]


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
    return "FRAME"


def material_for(label: str) -> str:
    low = label.lower()
    for keys, material in MATERIAL_RULES:
        if any(k in low for k in keys):
            return material
    return "engineering_plastic"


def main() -> int:
    t0 = time.time()
    doc = FreeCAD.openDocument(str(DOC))
    raw = list(doc.Objects)
    # App::Origin is an internal frame, not one of the 4,526 placements.
    objects = [o for o in raw if o.TypeId != "App::Origin"]
    print("OPENED", len(raw), "placements", len(objects), flush=True)

    path_cache = {}
    def path_of(obj, depth=0):
        if obj.Name in path_cache:
            return path_cache[obj.Name]
        if depth > 14:
            return obj.Label
        parents = list(getattr(obj, "InList", []) or [])
        path = (path_of(parents[0], depth + 1) + " / " + obj.Label) if parents else obj.Label
        path_cache[obj.Name] = path
        return path

    pid_by_name = {o.Name: f"F{i+1:04d}" for i, o in enumerate(objects)}
    records = []
    for i, obj in enumerate(objects):
        pid = f"F{i+1:04d}"
        parent = obj.InList[0] if getattr(obj, "InList", None) else None
        while parent is not None and parent.TypeId == "App::Origin":
            parent = parent.InList[0] if getattr(parent, "InList", None) else None
        parent_global = parent.getGlobalPlacement() if parent is not None else FreeCAD.Placement()
        shape = getattr(obj, "Shape", None)
        is_part = obj.TypeId == "Part::Feature"
        has_shape = bool(shape is not None and not shape.isNull())
        dims = []
        volume = 0.0
        bb = None
        if is_part and has_shape:
            try:
                # Shape already carries obj.Placement; apply only the parent chain.
                world_shape = shape.copy()
                if parent is not None:
                    world_shape.transformShape(parent_global.toMatrix())
                b = world_shape.BoundBox
                bb = [round(b.XMin, 4), round(b.YMin, 4), round(b.ZMin, 4),
                      round(b.XMax, 4), round(b.YMax, 4), round(b.ZMax, 4)]
                dims = [round(b.XLength, 4), round(b.YLength, 4), round(b.ZLength, 4)]
                volume = float(world_shape.Volume)
            except Exception:
                pass
        path = path_of(obj)
        module = classify(path, obj.Label)
        kind = "solid" if is_part else ("assembly" if obj.TypeId == "App::Part" else "construction")
        records.append({
            "placement_id": pid,
            "part_id": obj.Name,
            "part_name": obj.Label,
            "source_document": "VORON2.4_Assembly.step",
            "source_object": obj.Name,
            "geometry_reference": f"FreeCAD:{obj.Name}",
            "parent_id": pid_by_name.get(parent.Name) if parent is not None else None,
            "parent_name": parent.Label if parent is not None else None,
            "path": path,
            "module": module,
            "type": obj.TypeId,
            "geometry_kind": kind,
            "local_transform": matrix_of(obj.Placement),
            "world_transform": matrix_of(obj.getGlobalPlacement() if hasattr(obj, "getGlobalPlacement") else obj.Placement),
            "shape_embeds_local_placement": True,
            "dimensions_mm": dims,
            "bounding_box_mm": bb,
            "volume_mm3": round(volume, 3),
            "has_geometry": is_part and has_shape,
            "movable": module in {"XY_GANTRY", "TOOLHEAD", "Z_DRIVE", "BUILD_PLATFORM"},
            "material": material_for(obj.Label),
            "verification_status": ("GEOMETRY_PRESENT" if is_part and has_shape and volume > 1e-6
                                     else "ZERO_VOLUME" if is_part
                                     else "CONSTRUCTION_ONLY"),
        })

    solids = [r for r in records if r["has_geometry"]]
    zero = [r["placement_id"] for r in solids if r["volume_mm3"] <= 1e-6]
    dup = [k for k, v in Counter(r["part_id"] for r in records).items() if v > 1]
    modules = Counter(r["module"] for r in records)
    solids_by_module = Counter(r["module"] for r in solids)
    audit = {
        "source": str(DOC.relative_to(ROOT)).replace("\\", "/"),
        "source_step": "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step",
        "total_objects_in_document": len(raw),
        "placements": len(records),
        "part_features": len(solids),
        "assembly_nodes": sum(1 for r in records if r["geometry_kind"] == "assembly"),
        "construction_objects": sum(1 for r in records if r["geometry_kind"] == "construction"),
        "duplicate_part_ids": dup,
        "zero_volume_count": len(zero),
        "zero_volume_ids": zero[:40],
        "modules": dict(modules),
        "solids_by_module": dict(solids_by_module),
        "unit": "mm",
        "gltf_unit": "m",
        "scale_factor": 0.001,
        "shape_embeds_local_placement": True,
        "parent_placement_applied_once": True,
        "elapsed_s": round(time.time() - t0, 2),
    }
    PLACEMENTS.write_text(json.dumps({"audit": audit, "placements": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PLACEMENTS", len(records), "solids", len(solids), "zero", len(zero), dict(solids_by_module), flush=True)

    CACHE.mkdir(parents=True, exist_ok=True)
    module_parts: dict[str, list[dict]] = {}
    for rec, obj in zip(records, objects):
        if not rec["has_geometry"] or rec["module"] not in TRIAL_MODULES:
            continue
        out_dir = CACHE / rec["module"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{rec['placement_id']}.stl"
        try:
            parent = obj.InList[0] if getattr(obj, "InList", None) else None
            while parent is not None and parent.TypeId == "App::Origin":
                parent = parent.InList[0] if getattr(parent, "InList", None) else None
            world_shape = obj.Shape.copy()
            if parent is not None:
                world_shape.transformShape(parent.getGlobalPlacement().toMatrix())
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
        if len(module_parts.get(rec["module"], [])) and len(module_parts[rec["module"]]) % 25 == 0:
            print("MESH", rec["module"], len(module_parts[rec["module"]]), flush=True)

    MODULE_PARTS.write_text(json.dumps(module_parts, ensure_ascii=False, indent=2), encoding="utf-8")
    PLACEMENTS.write_text(json.dumps({"audit": audit, "placements": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MODULE_PARTS", {k: len(v) for k, v in module_parts.items()}, flush=True)
    print("DONE", round(time.time() - t0, 2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
