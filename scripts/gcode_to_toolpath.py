#!/usr/bin/env python3
"""Convert a real OrcaSlicer G-code file into a compact, animation-ready toolpath.

Output moves are arrays for the browser:
  [x0, y0, x1, y1, z, de, dt_s, type_index, is_travel, layer_index]
Coordinates remain in printer millimetres (0..300); the frontend centres them.
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
    if not text:
        return None
    total = 0.0
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([hms])", text):
        total += float(value) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total or None


def arc_length(x0, y0, x1, y1, p, clockwise):
    if "R" in p and "I" not in p and "J" not in p:
        r = abs(p["R"])
        chord = math.hypot(x1 - x0, y1 - y0)
        if chord <= 0:
            return 0.0
        angle = 2 * math.asin(min(1.0, chord / (2 * r)))
        if (clockwise and p["R"] > 0) or (not clockwise and p["R"] < 0):
            angle = 2 * math.pi - angle
        return angle * r
    cx, cy = x0 + p.get("I", 0.0), y0 + p.get("J", 0.0)
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
    args = ap.parse_args()
    path = Path(args.gcode)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    header = {}
    zmap = {}
    layer = 0
    layer_z = 0.0
    current_type = "Unknown"
    type_map: dict[str, int] = {}
    types: list[str] = []

    x = y = z = e = 0.0
    absolute_xyz = True
    absolute_e = False
    feed = 3000.0
    t = 0.0
    moves = []
    ext_bounds = [[math.inf, math.inf, math.inf], [-math.inf, -math.inf, -math.inf]]
    commands = Counter()
    extrusion_e = 0.0

    def type_index(name: str) -> int:
        if name not in type_map:
            type_map[name] = len(types)
            types.append(name)
        return type_map[name]

    def touch(px, py, pz, extruding):
        if not extruding:
            return
        for i, v in enumerate((px, py, pz)):
            ext_bounds[0][i] = min(ext_bounds[0][i], v)
            ext_bounds[1][i] = max(ext_bounds[1][i], v)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            c = line[1:].strip()
            if c == "LAYER_CHANGE":
                layer += 1
            elif c.startswith("Z:"):
                try:
                    layer_z = float(c[2:])
                    if layer <= 0:
                        layer = 1
                    zmap[layer] = layer_z
                except ValueError:
                    pass
            elif c.startswith("TYPE:"):
                current_type = c[5:].strip()
                type_index(current_type)
            else:
                body = c
                if ":" in body:
                    k, v = body.split(":", 1)
                    header.setdefault(k.strip().lower(), v.strip())
                elif "=" in body:
                    k, v = body.split("=", 1)
                    header.setdefault(k.strip().lower(), v.strip())
            continue
        if ";" in line:
            line = line.split(";", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].upper()
        if cmd == "G90":
            absolute_xyz = True
            continue
        if cmd == "G91":
            absolute_xyz = False
            continue
        if cmd == "M82":
            absolute_e = True
            continue
        if cmd == "M83":
            absolute_e = False
            continue
        if cmd == "G92":
            p = {k.upper(): float(v) for k, v in WORD.findall(line)}
            if "E" in p:
                e = p["E"]
            if "X" in p:
                x = p["X"] if absolute_xyz else x + p["X"]
            if "Y" in p:
                y = p["Y"] if absolute_xyz else y + p["Y"]
            if "Z" in p:
                z = p["Z"] if absolute_xyz else z + p["Z"]
            continue
        if cmd not in {"G0", "G1", "G2", "G3"}:
            continue
        commands[cmd] += 1
        p = {k.upper(): float(v) for k, v in WORD.findall(line)}
        if "F" in p and p["F"] > 0:
            feed = p["F"]
        nx, ny, nz = x, y, z
        if "X" in p:
            nx = p["X"] if absolute_xyz else x + p["X"]
        if "Y" in p:
            ny = p["Y"] if absolute_xyz else y + p["Y"]
        if "Z" in p:
            nz = p["Z"] if absolute_xyz else z + p["Z"]
        de = 0.0
        if "E" in p:
            de = p["E"] - e if absolute_e else p["E"]
            e = p["E"] if absolute_e else e + p["E"]
        if cmd in {"G2", "G3"}:
            length = arc_length(x, y, nx, ny, p, cmd == "G2")
        else:
            length = math.hypot(nx - x, ny - y)
        dt = length / (feed / 60.0) if feed > 0 and length > 0 else 0.0
        extruding = de > 0 and length > 0
        if extruding:
            extrusion_e += de
            touch(nx, ny, layer_z if layer > 0 else nz, True)
        t += dt
        if length > 0 or abs(de) > 1e-9:
            moves.append([
                round(x, 4), round(y, 4), round(nx, 4), round(ny, 4),
                round(layer_z if layer > 0 else nz, 4), round(de, 6),
                round(dt, 6), type_index("Travel" if not extruding else current_type),
                int(not extruding), layer,
            ])
        x, y, z = nx, ny, nz

    diameter = float(header.get("filament_diameter", 1.75))
    density = float(header.get("filament_density", 1.24))
    volume = extrusion_e * math.pi * (diameter / 2.0) ** 2
    mass = volume * density / 1000.0
    if not math.isfinite(ext_bounds[0][0]):
        ext_bounds = [[0, 0, 0], [300, 300, 0]]
    meta = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "layers": len(zmap) or layer,
        "layer_z": {str(k): v for k, v in sorted(zmap.items())},
        "mass_g": round(mass, 4),
        "filament_mm": round(extrusion_e, 3),
        "volume_mm3": round(volume, 3),
        "diameter_mm": diameter,
        "density_g_cm3": density,
        "time_s": parse_time(header.get("estimated printing time (normal mode)", "")) or round(t, 2),
        "computed_time_s": round(t, 2),
        "bounds": {
            "min": [round(v, 3) for v in ext_bounds[0]],
            "max": [round(v, 3) for v in ext_bounds[1]],
        },
        "commands": dict(commands),
        "move_count": len(moves),
        "types": types,
        "source": str(path).replace("\\", "/"),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"meta": meta, "moves": moves}, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("layers", "mass_g", "filament_mm", "time_s", "move_count", "bounds")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
