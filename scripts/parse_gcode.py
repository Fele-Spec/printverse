#!/usr/bin/env python3
"""Parse OrcaSlicer G-code and reconstruct motion/material statistics.

Supports G0/G1/G2/G3, G90/G91, M82/M83, layer comments, feedrate, relative E and
filament diameter/density from the header. Arc lengths are approximated analytically.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

WORD = re.compile(r"([A-Za-z])([-+]?(?:\d+\.?\d*|\.\d+))")


def parse_time(text: str) -> float | None:
    # "1h 2m 3s" / "19m 0s" / "42s"
    if not text:
        return None
    seconds = 0.0
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([hms])", text):
        seconds += float(value) * {"h": 3600, "m": 60, "s": 1}[unit]
    return seconds or None


def arc_length(x0, y0, x1, y1, params, clockwise):
    i = params.get("I", 0.0)
    j = params.get("J", 0.0)
    r = params.get("R")
    if r is not None and "I" not in params and "J" not in params:
        chord = math.hypot(x1 - x0, y1 - y0)
        if chord == 0:
            return 0.0
        ratio = min(1.0, chord / (2 * abs(r)))
        angle = 2 * math.asin(ratio)
        # Minor/major arc selection.
        if clockwise and r > 0:
            angle = 2 * math.pi - angle
        if not clockwise and r < 0:
            angle = 2 * math.pi - angle
        return abs(angle * r)
    cx, cy = x0 + i, y0 + j
    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    if clockwise:
        while a1 >= a0:
            a1 -= 2 * math.pi
        sweep = a0 - a1
    else:
        while a1 <= a0:
            a1 += 2 * math.pi
        sweep = a1 - a0
    return abs(sweep) * math.hypot(x0 - cx, y0 - cy)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("gcode")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expected-size", default="20,20,20")
    args = ap.parse_args()
    path = Path(args.gcode)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    header = {}
    for line in lines:
        if line.startswith(";"):
            body = line[1:].strip()
            if ":" in body:
                k, v = body.split(":", 1)
                header[k.strip().lower()] = v.strip()
            elif "=" in body:
                k, v = body.split("=", 1)
                header[k.strip().lower()] = v.strip()
    diameter = float(header.get("filament_diameter", 1.75))
    density = float(header.get("filament_density", 1.24))

    x = y = z = 0.0
    e = 0.0
    absolute_xyz = True
    absolute_e = False  # Orca uses M83 relative E
    feed = 3000.0
    layer = 0
    layer_z = 0.0
    current_type = "Unknown"
    extents_min = [math.inf] * 3
    extents_max = [-math.inf] * 3
    extrude_min = [math.inf] * 3
    extrude_max = [-math.inf] * 3
    commands = Counter()
    types = Counter()
    intervals = Counter()
    extrusion_mm = 0.0
    retraction_mm = 0.0
    travel_mm = 0.0
    path_mm = 0.0
    arc_count = 0
    move_count = 0
    feed_seconds = 0.0
    layer_extrusion: dict[int, float] = {}
    layer_z_map: dict[int, float] = {}
    last_xy = (0.0, 0.0)

    def update_extents(px, py, pz, extruding):
        nonlocal extents_min, extents_max, extrude_min, extrude_max
        for arr, val in ((extents_min, px), (extrude_min, px)):
            pass
        vals = (px, py, pz)
        for i, v in enumerate(vals):
            extents_min[i] = min(extents_min[i], v)
            extents_max[i] = max(extents_max[i], v)
            if extruding:
                extrude_min[i] = min(extrude_min[i], v)
                extrude_max[i] = max(extrude_max[i], v)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            comment = line[1:].strip()
            if comment == "LAYER_CHANGE":
                layer += 1
                layer_z = 0.0
            elif comment.startswith("Z:"):
                try:
                    layer_z = float(comment[2:])
                    if layer == 0:
                        layer = 1
                    layer_z_map[layer] = layer_z
                except ValueError:
                    pass
            elif comment.startswith("TYPE:"):
                current_type = comment[5:].strip()
                types[current_type] += 1
            continue
        if ";" in line:
            line = line.split(";", 1)[0].strip()
        if not line or line.startswith(";"):
            continue
        parts = line.split()
        cmd = parts[0].upper()
        if cmd not in {"G0", "G1", "G2", "G3"}:
            if cmd == "G90":
                absolute_xyz = True
            elif cmd == "G91":
                absolute_xyz = False
            elif cmd == "M82":
                absolute_e = True
            elif cmd == "M83":
                absolute_e = False
            elif cmd == "G92":
                vals = dict(WORD.findall(line))
                if "E" in vals:
                    e = float(vals["E"])
                if "X" in vals:
                    x = float(vals["X"]) if absolute_xyz else x + float(vals["X"])
                if "Y" in vals:
                    y = float(vals["Y"]) if absolute_xyz else y + float(vals["Y"])
                if "Z" in vals:
                    z = float(vals["Z"]) if absolute_xyz else z + float(vals["Z"])
            continue
        commands[cmd] += 1
        params = {k.upper(): float(v) for k, v in WORD.findall(line)}
        if "F" in params:
            feed = params["F"] if params["F"] > 0 else feed
        nx, ny, nz = x, y, z
        if "X" in params:
            nx = params["X"] if absolute_xyz else x + params["X"]
        if "Y" in params:
            ny = params["Y"] if absolute_xyz else y + params["Y"]
        if "Z" in params:
            nz = params["Z"] if absolute_xyz else z + params["Z"]
        de = 0.0
        if "E" in params:
            de = params["E"] - e if absolute_e else params["E"]
            e = params["E"] if absolute_e else e + params["E"]
        moved = math.hypot(nx - x, ny - y)
        dz = abs(nz - z)
        seg = moved if moved > 0 else dz
        if cmd in {"G2", "G3"}:
            seg = arc_length(x, y, nx, ny, params, cmd == "G2")
            arc_count += 1
        extruding = de > 0 and (moved > 0 or seg > 0)
        if extruding:
            path_mm += seg
            extrusion_mm += de
            layer_extrusion[layer] = layer_extrusion.get(layer, 0.0) + de
        elif de < 0:
            retraction_mm += -de
        elif moved > 0:
            travel_mm += moved
        if seg > 0:
            move_count += 1
            intervals[cmd] += seg
            feed_seconds += seg / (feed / 60.0)
            update_extents(nx, ny, nz, extruding)
            last_xy = (nx, ny)
        x, y, z = nx, ny, nz

    filament_area = math.pi * (diameter / 2.0) ** 2
    volume_mm3 = extrusion_mm * filament_area
    mass_g = volume_mm3 * density / 1000.0
    # This naive estimate ignores acceleration and cannot replace the slicer estimate.
    expected = [float(v) for v in args.expected_size.split(",")]
    gcode_size = [extrude_max[i] - extrude_min[i] for i in range(3)]
    size_delta = [round(gcode_size[i] - expected[i], 3) for i in range(3)]
    bbox = {
        "motion_min": [round(v, 4) if math.isfinite(v) else None for v in extents_min],
        "motion_max": [round(v, 4) if math.isfinite(v) else None for v in extents_max],
        "extrusion_min": [round(v, 4) if math.isfinite(v) else None for v in extrude_min],
        "extrusion_max": [round(v, 4) if math.isfinite(v) else None for v in extrude_max],
        "extrusion_size_mm": [round(v, 4) for v in gcode_size],
        "expected_model_size_mm": expected,
        "size_delta_mm": size_delta,
        "diameter_matches_model_within_1mm": all(abs(d) <= 1.0 for d in size_delta),
    }
    summary = {
        "file": str(path).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "lines": len(lines),
        "header": header,
        "layers": layer,
        "layer_z_first_last": [layer_z_map.get(min(layer_z_map), None), layer_z_map.get(max(layer_z_map), None)],
        "layer_count_with_z": len(layer_z_map),
        "commands": dict(commands),
        "move_count": move_count,
        "arc_count": arc_count,
        "feature_types": dict(types),
        "bounds": bbox,
        "filament": {
            "diameter_mm": diameter,
            "density_g_cm3": density,
            "extrusion_length_mm": round(extrusion_mm, 3),
            "retraction_length_mm": round(retraction_mm, 3),
            "volume_mm3": round(volume_mm3, 3),
            "mass_g": round(mass_g, 3),
            "path_length_mm": round(path_mm, 2),
        },
        "travel_mm": round(travel_mm, 2),
        "time": {
            "slicer_estimate_seconds": parse_time(header.get("estimated printing time (normal mode)") or ""),
            "naive_feedrate_seconds": round(feed_seconds, 1),
            "note": "naive_feedrate_seconds ignores acceleration/jerk; use slicer estimate for planning",
        },
        "per_layer_extrusion_mm": {str(k): round(v, 3) for k, v in sorted(layer_extrusion.items())},
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("layers", "commands", "filament", "bounds")}, ensure_ascii=False, indent=2))
    print(f"wrote {out}")
    return 0 if summary["layers"] > 0 and summary["filament"]["mass_g"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
