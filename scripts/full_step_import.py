"""One-shot full STEP assembly import with build123d/OCP.

The 267 MB file is heavy; this script records elapsed time, solid count, bbox and
memory. It is intentionally run once, not in the frontend request path.
"""
import json
import time
import tracemalloc
from pathlib import Path

from build123d import import_step

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
OUT = ROOT / "docs/reports/full_step_import.json"

t0 = time.time()
tracemalloc.start()
print("IMPORT_START", STEP.stat().st_size, flush=True)
shape = import_step(str(STEP))
t1 = time.time()
print("IMPORT_SHAPE_DONE", round(t1 - t0, 2), flush=True)
solids = shape.solids()
t2 = time.time()
bb = shape.bounding_box()
t3 = time.time()
current, peak = tracemalloc.get_traced_memory()
report = {
    "ok": True,
    "file": str(STEP.relative_to(ROOT)).replace("\\", "/"),
    "bytes": STEP.stat().st_size,
    "import_seconds": round(t1 - t0, 2),
    "solid_query_seconds": round(t2 - t1, 2),
    "bbox_seconds": round(t3 - t2, 2),
    "solid_count": len(solids),
    "volume_mm3": round(float(shape.volume), 2),
    "bbox_mm": {
        "min": [round(v, 3) for v in (bb.min.X, bb.min.Y, bb.min.Z)],
        "max": [round(v, 3) for v in (bb.max.X, bb.max.Y, bb.max.Z)],
        "size": [round(v, 3) for v in (bb.size.X, bb.size.Y, bb.size.Z)],
    },
    "python_peak_bytes": peak,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
