"""Toolpath conversion checks against the real cube slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reports/toolpath_test.json"
GCODE = ROOT / "assets/test-models/cube.gcode"
TOOLPATH = ROOT / "assets/test-models/cube.toolpath.json"


def main() -> int:
    if not TOOLPATH.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/gcode_to_toolpath.py"), str(GCODE), "--out", str(TOOLPATH)], check=True)
    data = json.loads(TOOLPATH.read_text(encoding="utf-8"))
    meta = data["meta"]
    assert meta["layers"] == 100, meta
    assert abs(meta["mass_g"] - 3.978) < 0.02, meta
    assert meta["move_count"] > 7000, meta
    assert "Outer wall" in meta["types"], meta["types"]
    assert len(data["moves"]) == meta["move_count"]
    summary = {
        "ok": True,
        "layers": meta["layers"],
        "mass_g": meta["mass_g"],
        "filament_mm": meta["filament_mm"],
        "move_count": meta["move_count"],
        "types": meta["types"],
        "bounds": meta["bounds"],
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
