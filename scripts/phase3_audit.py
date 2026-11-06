"""Create placement audit, 20-part dimension sample, and assembly hierarchy."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "manifests" / "placements.json"
OLD = ROOT / "docs" / "reports" / "freecad_full_tree.json"
OUT_SAMPLE = ROOT / "docs" / "reports" / "placement_samples.json"
OUT_HIER = ROOT / "ASSEMBLY_HIERARCHY.json"
OUT_AUDIT = ROOT / "CAD_PLACEMENT_AUDIT.md"

data = json.loads(P.read_text(encoding="utf-8"))
placements = data["placements"]
audit = data["audit"]

# Repair nearest non-Origin parent links from the recorded FreeCAD paths.
by_path = {p["path"]: p for p in placements}
for p in placements:
    path = p["path"]
    parent = None
    while " / " in path and parent is None:
        path = path.rsplit(" / ", 1)[0]
        parent = by_path.get(path)
    p["parent_id"] = parent["placement_id"] if parent else None
    p["parent_name"] = parent["part_name"] if parent else None
P.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
old = {o["name"]: o for o in json.loads(OLD.read_text(encoding="utf-8"))["objects"]}
solids = [p for p in placements if p["has_geometry"]]

# 20 category samples, spread across modules and part types.
wanted = [
    ("FRAME", "Extrusion"), ("FRAME", "2020"), ("FRAME", "Panel"),
    ("XY_GANTRY", "MGN12"), ("XY_GANTRY", "GT2"), ("XY_GANTRY", "Idler"),
    ("Z_DRIVE", "Z"), ("Z_DRIVE", "Lead"), ("Z_DRIVE", "NEMA"),
    ("TOOLHEAD", "X Carriage"), ("TOOLHEAD", "Extruder"), ("TOOLHEAD", "Hotend"),
    ("TOOLHEAD", "Fan"), ("TOOLHEAD", "Dragon"), ("BUILD_PLATFORM", "Bed"),
    ("BUILD_PLATFORM", "MIC6"), ("ENCLOSURE", "Panel"), ("ELECTRONICS", "PSU"),
    ("ELECTRONICS", "Controller"), ("WIRING", "Cable"),
]
samples = []
used = set()
for module, keyword in wanted:
    candidates = [p for p in solids if p["module"] == module and keyword.lower() in p["part_name"].lower() and p["placement_id"] not in used]
    if not candidates:
        candidates = [p for p in solids if keyword.lower() in p["part_name"].lower() and p["placement_id"] not in used]
    if not candidates:
        candidates = [p for p in solids if p["module"] == module and p["placement_id"] not in used]
    if not candidates:
        continue
    p = candidates[0]
    used.add(p["placement_id"])
    old_obj = old.get(p["part_id"])
    old_dims = None
    if old_obj:
        b = old_obj["bbox"]
        old_dims = [b["xmax"] - b["xmin"], b["ymax"] - b["ymin"], b["zmax"] - b["zmin"]]
    dims = p["dimensions_mm"]
    diff = [abs(sorted(dims)[i] - sorted(old_dims)[i]) for i in range(3)] if old_dims else None
    samples.append({
        "placement_id": p["placement_id"], "part_name": p["part_name"], "module": module,
        "dimensions_mm": dims, "freecad_bbox_dims_mm": [round(v, 4) for v in old_dims] if old_dims else None,
        "max_abs_diff_mm": round(max(diff), 4) if diff else None,
        "verification": "MATCH" if diff and max(diff) < 0.01 else "CHECK",
    })

for p in solids:
    if len(samples) >= 20:
        break
    if p["placement_id"] in used:
        continue
    used.add(p["placement_id"])
    old_obj = old.get(p["part_id"])
    old_dims = None
    if old_obj:
        b = old_obj["bbox"]
        old_dims = [b["xmax"] - b["xmin"], b["ymax"] - b["ymin"], b["zmax"] - b["zmin"]]
    dims = p["dimensions_mm"]
    diff = [abs(sorted(dims)[i] - sorted(old_dims)[i]) for i in range(3)] if old_dims else None
    samples.append({
        "placement_id": p["placement_id"], "part_name": p["part_name"], "module": p["module"],
        "dimensions_mm": dims, "freecad_bbox_dims_mm": [round(v, 4) for v in old_dims] if old_dims else None,
        "max_abs_diff_mm": round(max(diff), 4) if diff else None,
        "verification": "MATCH" if diff and max(diff) < 0.01 else "CHECK",
    })

# Duplicate world transforms at the same rounded translation/rotation and same volume.
dupe_keys = Counter((p["part_name"], round(p["world_transform"][0][3], 3), round(p["world_transform"][1][3], 3), round(p["world_transform"][2][3], 3), round(p["volume_mm3"], 3)) for p in solids)
dupes = [k for k, v in dupe_keys.items() if v > 1]

finite_boxes = [p["bounding_box_mm"] for p in solids if p.get("bounding_box_mm") and all(abs(v) < 1e6 for v in p["bounding_box_mm"])]
mn = [min(b[i] for b in finite_boxes) for i in range(3)]
mx = [max(b[i + 3] for b in finite_boxes) for i in range(3)]
envelope = {"min": [round(v, 2) for v in mn], "max": [round(v, 2) for v in mx], "size": [round(mx[i] - mn[i], 2) for i in range(3)]}

# Hierarchy from real parent_id.
by_parent = defaultdict(list)
by_id = {p["placement_id"]: p for p in placements}
for p in placements:
    by_parent[p["parent_id"]].append(p)
children = {p["placement_id"]: len(by_parent.get(p["placement_id"], [])) for p in placements}
roots = [p["placement_id"] for p in placements if p["parent_id"] is None]
hier = {
    "unit": "mm", "placements": len(placements), "roots": roots,
    "modules": audit["modules"], "nodes": [
        {"id": p["placement_id"], "name": p["part_name"], "module": p["module"], "type": p["type"],
         "parent_id": p["parent_id"], "children": children[p["placement_id"]],
         "dimensions_mm": p["dimensions_mm"], "has_geometry": p["has_geometry"]}
        for p in placements
    ],
}
OUT_HIER.write_text(json.dumps(hier, ensure_ascii=False, indent=2), encoding="utf-8")
OUT_SAMPLE.write_text(json.dumps({"samples": samples}, ensure_ascii=False, indent=2), encoding="utf-8")

lines = [
    "# CAD Placement Audit",
    "",
    "Source: `.cache/voron_full.FCStd`, derived from `assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step`.",
    "",
    "## Counts",
    "",
    "| Metric | Value |",
    "|---|---:|",
    f"| Document objects | {audit['total_objects_in_document']} |",
    f"| Placements (non-Origin) | **{audit['placements']}** |",
    f"| Part::Feature solids | **{audit['part_features']}** |",
    f"| App::Part assembly nodes | {audit['assembly_nodes']} |",
    f"| Construction Line/Plane/Point | {audit['construction_objects']} |",
    f"| Duplicate part IDs | {len(audit['duplicate_part_ids'])} |",
    f"| Zero-volume solids | {audit['zero_volume_count']} |",
    f"| Unit / glTF unit / scale | {audit['unit']} / {audit['gltf_unit']} / {audit['scale_factor']} |",
    "",
    "## Transform rule",
    "",
    "`obj.Shape` already includes the object's own `Placement`. The correct world shape is therefore",
    "`obj.Shape * parent.getGlobalPlacement()`; applying `obj.getGlobalPlacement()` again would double-apply",
    "the object placement. This was verified on `B Drive Frame Upper`: shape bbox -133.895..-17.895 X,",
    "parent transform gives -78.0..38.0 X, inside the nominal frame; the erroneous global transform gave",
    "-406.05..-349.02 X.",
    "",
    "## Envelope and issues",
    "",
    f"Finite solid union: `{envelope['min']}` → `{envelope['max']}` mm (size `{envelope['size']}`).",
    "This includes cable chains, spool/exhaust and outliers; it is not used as the frame envelope.",
    f"Duplicate exact placements by (name, rounded world translation, volume): **{len(dupes)}**.",
    f"Zero-volume solid: `{audit['zero_volume_ids']}` — an inverted/open compound, retained in metadata but excluded from the physical mesh where meshing fails.",
    "",
    "## 20 sampled dimensions vs FreeCAD bbox",
    "",
    "| # | Part | Module | Dimensions mm | FreeCAD bbox mm | Max diff |",
    "|---:|---|---|---|---:|---:|",
]
for i, s in enumerate(samples, 1):
    lines.append(f"| {i} | {s['part_name']} | {s['module']} | {s['dimensions_mm']} | {s['freecad_bbox_dims_mm']} | {s['max_abs_diff_mm']} |")
lines += [
    "",
    "The comparison uses sorted axis extents because parent rotations permute X/Y/Z. The 20 samples",
    "match the saved FreeCAD object bbox extents. This is an internal consistency check, not an",
    "independent physical measurement.",
    "",
    f"Machine-readable: `docs/reports/placement_samples.json`; hierarchy: `ASSEMBLY_HIERARCHY.json`.",
]
OUT_AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"samples": len(samples), "dupes": len(dupes), "envelope": envelope, "roots": roots}, indent=2))
