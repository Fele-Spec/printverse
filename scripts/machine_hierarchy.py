#!/usr/bin/env python3
"""Categorize the full STEP product list into the PrintVerse mechanical hierarchy."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
OUT = ROOT / "manifests/machine-hierarchy.json"
TEXT = STEP.read_text(encoding="latin-1", errors="replace")
NAMES = re.findall(r"PRODUCT\s*\(\s*'([^']*)'", TEXT)

GROUPS = {
    "FRAME": ["frame", "extrusion", "panel", "2020", "corner", "brace", "skirt", "din rail"],
    "CORE_XY_GANTRY": ["gantry", "a drive", "b drive", "a/b", "x axis", "y axis", "idler", "belt", "gt2", "pulley", "carriage"],
    "Z_AXIS": ["z drive", "z idler", "z belt", "z joint", "bed", "mic6", "heater", "lead screw", "z motor"],
    "TOOLHEAD": ["printhead", "toolhead", "extruder", "hotend", "stealthburner", "afterburner", "revo", "dragon", "fan", "duct"],
    "ELECTRONICS_BAY": ["electronics", "controller", "psu", "power", "octopus", "skr", "raspberry", "din", "ssr", "wago"],
    "MOTION_HARDWARE": ["nema", "motor", "bearing", "shaft", "rail", "mgn", "screw", "nut", "washer", "shim", "f695", "625"],
}


def category(name: str) -> str:
    low = name.lower()
    for group, words in GROUPS.items():
        if any(w in low for w in words):
            return group
    return "OTHER"


groups: dict[str, list[str]] = {k: [] for k in GROUPS}
groups["OTHER"] = []
for name in NAMES:
    groups[category(name)].append(name)

hierarchy = {
    "root": "_VORON2.4_Assembly",
    "source": "assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step",
    "step_product_count": len(NAMES),
    "note": "Named STEP products are grouped for the digital twin. Positions in the Web scene are nominal, verified kinematic relationships, not claimed exact STEP transforms.",
    "groups": [
        {
            "id": group,
            "parent": "VORON_V2_4R2_300",
            "count": len(names),
            "sample": names[:18],
            "motion": {
                "FRAME": "static",
                "CORE_XY_GANTRY": "Y carriage + X carriage (CoreXY)",
                "Z_AXIS": "bed moves in -Z; 4 lead screws rotate",
                "TOOLHEAD": "X/Y with gantry; nozzle at fixed world Z",
                "ELECTRONICS_BAY": "static",
                "MOTION_HARDWARE": "distributed",
                "OTHER": "static/instance",
            }.get(group, "static"),
        }
        for group, names in groups.items()
    ],
    "links": [
        {"parent": "FRAME", "child": "CORE_XY_GANTRY", "type": "linear rail / extrusion"},
        {"parent": "CORE_XY_GANTRY", "child": "TOOLHEAD", "type": "X carriage"},
        {"parent": "FRAME", "child": "Z_AXIS", "type": "4-point Z drive"},
        {"parent": "Z_AXIS", "child": "PRINTED_OBJECT", "type": "bed-local detachable object"},
        {"parent": "FRAME", "child": "ELECTRONICS_BAY", "type": "static mount"},
    ],
}
OUT.write_text(json.dumps(hierarchy, indent=2), encoding="utf-8")
print(json.dumps({g: len(v) for g, v in groups.items()}, indent=2))
print("wrote", OUT)
