"""OrcaSlicer CLI adapter for uploaded STL files."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCA = ROOT / "tools" / "OrcaSlicer-2.4.2" / "orca-slicer.exe"
MACHINE = ROOT / "configs" / "machine" / "voron-v2.4r2-300-0.4.json"
PROCESS = ROOT / "configs" / "process" / "voron-0.20mm-standard.json"
FILAMENT = ROOT / "configs" / "filament" / "generic-pla.json"
PARSER = ROOT / "scripts" / "gcode_to_toolpath.py"


class SliceError(RuntimeError):
    pass


def _tail(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-limit:]


def slice_stl(stl_path: Path, job_dir: Path, job_id: str) -> dict:
    if not ORCA.exists():
        raise SliceError(f"OrcaSlicer missing: {ORCA}")
    job_dir.mkdir(parents=True, exist_ok=True)
    log = ROOT / "logs" / f"orca-{job_id}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    settings = f"{PROCESS};{MACHINE}"
    cmd = [
        str(ORCA), str(stl_path),
        "--load-settings", settings,
        "--load-filaments", str(FILAMENT),
        "--slice", "0",
        "--outputdir", str(job_dir),
        "--export-3mf", "model.3mf",
        "--datadir", str(ROOT / ".cache" / "orca-data"),
        "--logfile", str(log),
        "--debug", "3",
    ]
    with log.open("ab") as out:
        proc = subprocess.run(
            cmd, cwd=str(ROOT), stdout=out, stderr=subprocess.STDOUT,
            timeout=240, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    gcodes = sorted(job_dir.glob("*.gcode"))
    if not gcodes:
        raise SliceError(f"OrcaSlicer did not produce G-code (exit {proc.returncode}).\n{_tail(log)}")
    gcode = gcodes[0]
    canonical = job_dir / "model.gcode"
    if gcode != canonical:
        gcode.replace(canonical)
        gcode = canonical
    toolpath = job_dir / "toolpath.json"
    parser = subprocess.run(
        [sys.executable, str(PARSER), str(gcode), "--out", str(toolpath)],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120,
    )
    if parser.returncode != 0 or not toolpath.exists():
        raise SliceError(f"G-code parser failed: {parser.stderr.decode(errors='replace')[-2000:]}")
    import json
    meta = json.loads(toolpath.read_text(encoding="utf-8"))["meta"]
    return {
        "gcode_path": str(gcode.relative_to(ROOT)).replace("\\", "/"),
        "toolpath_path": str(toolpath.relative_to(ROOT)).replace("\\", "/"),
        "mass_g": meta["mass_g"],
        "time_s": meta["time_s"],
        "layers": meta["layers"],
        "warnings": "" if proc.returncode == 0 else f"Orca exit {proc.returncode}; G-code exists; see {log.name}",
        "log_path": str(log.relative_to(ROOT)).replace("\\", "/"),
    }
