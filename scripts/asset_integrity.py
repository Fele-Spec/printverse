#!/usr/bin/env python3
"""Whole-collection integrity sweep for Voron CAD/STL/DXF/PDF assets."""
from __future__ import annotations

import csv
import json
import time
import zipfile
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "assets/source/voron-v2.4r2-300"


def stl_record(path: Path) -> dict:
    t0 = time.time()
    try:
        mesh = trimesh.load(path, force="mesh", process=True)
        return {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "format": "STL",
            "ok": bool(len(mesh.faces) > 0),
            "faces": int(len(mesh.faces)),
            "vertices": int(len(mesh.vertices)),
            "watertight": bool(mesh.is_watertight),
            "winding_consistent": bool(mesh.is_winding_consistent),
            "extents_mm": [round(float(x), 3) for x in mesh.extents],
            "seconds": round(time.time() - t0, 3),
            "error": None,
        }
    except Exception as exc:
        return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "format": "STL", "ok": False,
                "faces": 0, "vertices": 0, "watertight": False, "winding_consistent": False,
                "extents_mm": [], "seconds": round(time.time() - t0, 3), "error": repr(exc)}


def header_record(path: Path, fmt: str) -> dict:
    raw = path.read_bytes()[:4096]
    text = raw.decode("latin-1", errors="replace")
    ok = True
    detail = ""
    if fmt == "DXF":
        ok = "SECTION" in text and ("ENTITIES" in text or "HEADER" in text)
        detail = "SECTION/ENTITIES header" if ok else "missing DXF section markers"
    elif fmt == "PDF":
        ok = text.startswith("%PDF-")
        detail = text.splitlines()[0][:40] if text else "empty"
    elif fmt == "STEP":
        ok = text.lstrip().startswith("ISO-10303-21")
        detail = text.lstrip().splitlines()[0][:60] if text else "empty"
    elif fmt == "F3D":
        ok = raw[:2] == b"PK"
        detail = "ZIP container" if ok else "not a ZIP container"
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "format": fmt, "ok": ok,
            "bytes": path.stat().st_size, "detail": detail}


def main() -> int:
    records = []
    for path in sorted((BASE / "STLs").rglob("*.stl")):
        records.append(stl_record(path))
    headers = []
    for path in sorted((BASE / "DXF").rglob("*")):
        if path.suffix.lower() == ".dxf":
            headers.append(header_record(path, "DXF"))
    for path in sorted((BASE / "Manual").rglob("*.pdf")):
        headers.append(header_record(path, "PDF"))
    for path in sorted((BASE / "CAD").glob("*.step")):
        headers.append(header_record(path, "STEP"))
    for path in sorted((BASE / "CAD").glob("*.f3d")):
        headers.append(header_record(path, "F3D"))
    for path in sorted((BASE / "CAD").glob("*.step.zip")):
        try:
            with zipfile.ZipFile(path) as z:
                bad = z.testzip()
                headers.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "format": "ZIP",
                                "ok": bad is None, "bytes": path.stat().st_size,
                                "detail": f"{len(z.namelist())} entries; testzip={bad}"})
        except Exception as exc:
            headers.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "format": "ZIP",
                            "ok": False, "bytes": path.stat().st_size, "detail": repr(exc)})
    summary = {
        "stl_count": len(records),
        "stl_ok": sum(r["ok"] for r in records),
        "stl_watertight": sum(r["watertight"] for r in records),
        "stl_not_watertight": sum(1 for r in records if not r["watertight"]),
        "stl_errors": [r for r in records if not r["ok"]],
        "header_count": len(headers),
        "header_ok": sum(r["ok"] for r in headers),
        "headers": headers,
        "records": records,
    }
    out = ROOT / "docs" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "asset_integrity.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "all_stl_validation.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["path", "ok", "faces", "vertices", "watertight", "winding_consistent", "extents_x", "extents_y", "extents_z", "seconds", "error"])
        for r in records:
            e = r["extents_mm"] + [None] * (3 - len(r["extents_mm"]))
            w.writerow([r["path"], r["ok"], r["faces"], r["vertices"], r["watertight"], r["winding_consistent"],
                        e[0], e[1], e[2], r["seconds"], r["error"]])
    print(json.dumps({k: summary[k] for k in ("stl_count", "stl_ok", "stl_watertight", "stl_not_watertight", "header_count", "header_ok")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
