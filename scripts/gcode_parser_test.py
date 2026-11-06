#!/usr/bin/env python3
"""Synthetic parser test for G2/G3 arcs, relative extrusion and layer markers."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tmp = ROOT / ".cache" / "arc_test.gcode"
tmp.parent.mkdir(exist_ok=True)
tmp.write_text("""
; HEADER_BLOCK_START
; filament_density: 1.24
; filament_diameter: 1.75
; total layer number: 2
; HEADER_BLOCK_END
G90
M83
G1 X100 Y100 Z0.2 F3000
;LAYER_CHANGE
;Z:0.2
;HEIGHT:0.2
G1 X110 Y100 E1.0
G2 X110 Y110 I0 J5 E1.0
G3 X100 Y110 I-5 J0 E1.0
;LAYER_CHANGE
;Z:0.4
;HEIGHT:0.2
G1 X105 Y105 E1.0
""".strip() + "\n", encoding="utf-8")
out = ROOT / "docs" / "reports" / "gcode_parser_unit.json"
cmd = [sys.executable, str(ROOT / "scripts" / "parse_gcode.py"), str(tmp), "--out", str(out), "--expected-size", "20,20,10"]
proc = subprocess.run(cmd, capture_output=True, text=True)
print(proc.stdout)
print(proc.stderr, file=sys.stderr)
if proc.returncode != 0:
    raise SystemExit(proc.returncode)
data = json.loads(out.read_text(encoding="utf-8"))
assert data["arc_count"] == 2, data["arc_count"]
assert data["layers"] == 2, data["layers"]
summary = {"ok": True, "arc_count": data["arc_count"], "layers": data["layers"],
           "commands": data["commands"], "filament": data["filament"], "source": str(tmp)}
(ROOT / "docs" / "reports" / "gcode_parser_unit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
