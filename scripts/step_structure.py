#!/usr/bin/env python3
"""Extract assembly structure statistics from the official STEP file without a full CAD load."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
OUT = ROOT / "docs" / "reports" / "step_structure.json"

text = STEP.read_text(encoding="latin-1", errors="replace")
product_names = re.findall(r"PRODUCT\s*\(\s*'([^']*)'", text)
counts = {
    "PRODUCT": len(re.findall(r"=\s*PRODUCT\s*\(", text)),
    "NEXT_ASSEMBLY_USAGE_OCCURRENCE": len(re.findall(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE", text)),
    "MANIFOLD_SOLID_BREP": len(re.findall(r"MANIFOLD_SOLID_BREP", text)),
    "ADVANCED_BREP_SHAPE_REPRESENTATION": len(re.findall(r"ADVANCED_BREP_SHAPE_REPRESENTATION", text)),
    "CARTESIAN_POINT": len(re.findall(r"CARTESIAN_POINT", text)),
    "AXIS2_PLACEMENT_3D": len(re.findall(r"AXIS2_PLACEMENT_3D", text)),
}
report = {
    "file": str(STEP.relative_to(ROOT)).replace("\\", "/"),
    "bytes": STEP.stat().st_size,
    "header": text[:400].splitlines()[:8],
    "counts": counts,
    "product_name_count": len(product_names),
    "product_names_sample": product_names[:40],
    "interpretation": "Text-level STEP structure only. Not a substitute for a completed CAD assembly import.",
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("bytes", "counts", "product_name_count")}, indent=2))
