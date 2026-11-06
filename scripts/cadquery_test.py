#!/usr/bin/env python3
"""Verify the isolated CadQuery 2.8 / OCP 7.9 environment."""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "assets/processed/cadquery_test.step"
box = cq.Workplane("XY").box(10, 20, 30)
cq.exporters.export(box, str(out))
bb = box.val().BoundingBox()
report = {
    "ok": out.exists(),
    "cadquery": cq.__version__,
    "volume_mm3": round(box.val().Volume(), 3),
    "bbox": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
    "step": str(out.relative_to(ROOT)).replace("\\", "/"),
    "step_bytes": out.stat().st_size if out.exists() else 0,
}
(ROOT / "docs/reports/cadquery_test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
