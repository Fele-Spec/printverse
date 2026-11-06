#!/usr/bin/env python3
"""Resolve OrcaSlicer's layered Voron profiles into flat, CLI-loadable JSON files.

Orca ships machine/process/filament presets as small child JSON files with `inherits`
chains. The CLI expects each tab's exported (fully resolved) preset. This script walks
the official chain, merges parent -> child, and records provenance in a sidecar.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCA = ROOT / "tools" / "OrcaSlicer-2.4.2"
PROFILES = ORCA / "resources" / "profiles"


def load_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for path in PROFILES.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = data.get("name")
        if isinstance(name, str) and name not in index:
            index[name] = path
    return index


INDEX = load_index()


def resolve(name: str, seen: tuple[str, ...] = ()) -> dict:
    if name in seen:
        raise RuntimeError(f"inheritance cycle: {' -> '.join(seen + (name,))}")
    if name not in INDEX:
        raise KeyError(f"profile not found: {name}")
    path = INDEX[name]
    data = json.loads(path.read_text(encoding="utf-8"))
    parent = data.get("inherits")
    base = resolve(parent, seen + (name,)) if parent else {}
    merged = dict(base)
    merged.update(data)
    merged["_resolved_path"] = str(path.relative_to(ROOT)).replace("\\", "/")
    return merged


def write_profile(name: str, out: Path, kind: str) -> dict:
    data = resolve(name)
    # CLI-only identity keys that the loader rejects as overrides are fine in a file,
    # but strip path-only bookkeeping.
    data.pop("_resolved_path", None)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    meta = {
        "kind": kind,
        "name": name,
        "output": str(out.relative_to(ROOT)).replace("\\", "/"),
        "source_root": "tools/OrcaSlicer-2.4.2/resources/profiles",
        "orca_version": "2.4.2",
        "verification": "UNVERIFIED_AGAINST_PHYSICAL_MACHINE",
        "note": "Values are the official OrcaSlicer Voron preset values, not measured on a real printer.",
        "key_count": len(data),
    }
    return meta


def main() -> int:
    jobs = [
        ("Voron 2.4 300 0.4 nozzle", ROOT / "configs/machine/voron-v2.4r2-300-0.4.json", "machine"),
        ("0.20mm Standard @Voron", ROOT / "configs/process/voron-0.20mm-standard.json", "process"),
        ("Generic PLA @System", ROOT / "configs/filament/generic-pla.json", "filament"),
    ]
    metas = []
    for name, path, kind in jobs:
        try:
            meta = write_profile(name, path, kind)
            metas.append(meta)
            print(f"OK {kind}: {name} -> {path.relative_to(ROOT)} ({meta['key_count']} keys)")
        except Exception as exc:
            print(f"FAIL {kind}: {name}: {exc}", file=sys.stderr)
            return 1
    (ROOT / "configs" / "orca-profile-manifest.json").write_text(
        json.dumps(metas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
