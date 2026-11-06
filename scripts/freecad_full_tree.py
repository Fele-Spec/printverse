"""Full FreeCAD import with object labels and placements.

This is a background-only audit: it may take many minutes for the 267 MB assembly.
It writes docs/reports/freecad_full_tree.json only after import finishes.
"""
import json
import time
from pathlib import Path

import FreeCAD
import Import

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
OUT = ROOT / "docs/reports/freecad_full_tree.json"

print("FREECAD_IMPORT_START", STEP.stat().st_size, flush=True)
t0 = time.time()
doc = FreeCAD.newDocument("full_assembly")
Import.insert(str(STEP), doc.Name)
print("FREECAD_INSERT_DONE", round(time.time() - t0, 2), flush=True)
doc.recompute()
print("FREECAD_RECOMPUTE_DONE", round(time.time() - t0, 2), flush=True)

objects = []
for obj in doc.Objects:
    try:
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        bb = shape.BoundBox
        p = obj.Placement
        objects.append({
            "label": obj.Label,
            "name": obj.Name,
            "type": obj.TypeId,
            "placement": {
                "x": round(p.Base.x, 4), "y": round(p.Base.y, 4), "z": round(p.Base.z, 4),
                "axis": [round(p.Rotation.Axis.x, 5), round(p.Rotation.Axis.y, 5), round(p.Rotation.Axis.z, 5)],
                "angle_deg": round(p.Rotation.Angle * 180.0 / 3.141592653589793, 4),
            },
            "bbox": {
                "xmin": round(bb.XMin, 4), "ymin": round(bb.YMin, 4), "zmin": round(bb.ZMin, 4),
                "xmax": round(bb.XMax, 4), "ymax": round(bb.YMax, 4), "zmax": round(bb.ZMax, 4),
            },
        })
    except Exception:
        continue

report = {
    "ok": True,
    "file": str(STEP.relative_to(ROOT)).replace("\\", "/"),
    "elapsed_s": round(time.time() - t0, 2),
    "object_count": len(objects),
    "objects": objects,
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("FREECAD_TREE_WRITTEN", len(objects), OUT, flush=True)
