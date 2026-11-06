"""Build InstancedMesh data for repeated standard parts.

A group is only formed when part base name, module, sorted dimensions and volume
match. This prevents different SOLID/COMPOUND shapes from being instanced as if
they were one part.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PLACEMENTS = ROOT / "manifests/placements.json"
MODULE_PARTS = ROOT / "manifests/module-parts.json"
OUT = ROOT / "frontend/public/models/voron/fasteners"
INSTANCES = ROOT / "frontend/public/models/voron/instances.json"
SKIP = ROOT / "frontend/public/models/voron/instanced-ids.json"

FASTENER = re.compile(r"(m[2345]|screw|bolt|nut|shim|washer|bearing|gt2|idler|magnet|vhb|insert|t-nut|hammerhead|f695|625)", re.I)


def base_name(name: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", name).strip()


def mat(v):
    return np.array(v, dtype=float)


def main() -> int:
    data = json.loads(PLACEMENTS.read_text(encoding="utf-8"))
    parts = json.loads(MODULE_PARTS.read_text(encoding="utf-8"))
    by_id = {}
    for module, items in parts.items():
        for p in items:
            by_id[p["placement_id"]] = p
    groups = defaultdict(list)
    for p in data["placements"]:
        if not p["has_geometry"] or p["placement_id"] not in by_id:
            continue
        if not FASTENER.search(p["part_name"]):
            continue
        key = (
            p["module"], base_name(p["part_name"]),
            tuple(round(v, 2) for v in sorted(p["dimensions_mm"])),
            round(p["volume_mm3"], 1),
        )
        groups[key].append(p)

    OUT.mkdir(parents=True, exist_ok=True)
    result = []
    skip = []
    for idx, (key, items) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1]))):
        if len(items) < 4:
            continue
        module, base, dims, volume = key
        rep = items[0]
        rep_part = by_id[rep["placement_id"]]
        src = ROOT / rep_part["mesh_file"]
        if not src.exists():
            continue
        # The exported STL is already in world coordinates and includes the
        # representative object's own Placement. The target mapping is therefore
        # target_world * inverse(representative_world), not a parent-only delta.
        rep_world_inv = np.linalg.inv(mat(rep["world_transform"]))
        matrices = []
        ids = []
        for p in items:
            delta = mat(p["world_transform"]) @ rep_world_inv
            matrices.extend([round(float(x), 7) for row in delta for x in row])
            ids.append(p["placement_id"])
            skip.append(p["placement_id"])
        safe = re.sub(r"[^A-Za-z0-9]+", "_", base)[:48]
        name = f"{module}_{idx:03d}_{safe}.stl"
        dst = OUT / name
        shutil.copy2(src, dst)
        result.append({
            "id": f"{module}_{idx:03d}",
            "base_name": base,
            "module": module,
            "dimensions_mm": list(dims),
            "volume_mm3": volume,
            "count": len(items),
            "geometry": f"/models/voron/fasteners/{name}",
            "placement_ids": ids,
            "matrices": matrices,
        })

    INSTANCES.write_text(json.dumps({"groups": result}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    SKIP.write_text(json.dumps(sorted(set(skip)), separators=(",", ":")), encoding="utf-8")
    print("groups", len(result), "instances", len(skip), "bytes", INSTANCES.stat().st_size)
    for g in result[:12]:
        print(g["count"], g["base_name"], g["module"], g["dimensions_mm"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
