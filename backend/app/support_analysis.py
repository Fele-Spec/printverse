"""Real OrcaSlicer support analysis: slice with support enabled, parse G-code."""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCA = ROOT / "tools" / "OrcaSlicer-2.4.2" / "orca-slicer.exe"
MACHINE = ROOT / "configs/machine/voron-v2.4r2-300-0.4.json"
PROCESS = ROOT / "configs/process/voron-0.20mm-standard.json"
FILAMENT = ROOT / "configs/filament/generic-pla.json"
PARSER = ROOT / "scripts/gcode_to_toolpath.py"
SUPPORT_TYPES = {"Support", "Support interface", "Support transition"}


class SupportAnalysisError(RuntimeError):
    pass


def analyze_supports(mesh_path: Path, timeout: int = 240) -> dict:
    if not ORCA.exists():
        raise SupportAnalysisError("OrcaSlicer missing")
    work = ROOT / "runtime" / "mesh" / f"support-{uuid.uuid4().hex}"
    work.mkdir(parents=True, exist_ok=True)
    profile = json.loads(PROCESS.read_text(encoding="utf-8"))
    profile.update({
        "enable_support": "1",
        "support_type": "normal(auto)",
        "support_threshold_angle": "30",
        "support_on_build_plate_only": "0",
        "support_top_z_distance": "0.2",
        "support_style": "default",
    })
    support_profile = work / "support-process.json"
    support_profile.write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
    log = ROOT / "logs" / f"orca-support-{work.name}.log"
    cmd = [
        str(ORCA), str(mesh_path),
        "--load-settings", f"{support_profile};{MACHINE}",
        "--load-filaments", str(FILAMENT),
        "--slice", "0", "--outputdir", str(work),
        "--datadir", str(ROOT / ".cache" / "orca-support-data"),
        "--logfile", str(log), "--debug", "3",
    ]
    with log.open("ab") as out:
        proc = subprocess.run(cmd, cwd=str(ROOT), stdout=out, stderr=subprocess.STDOUT,
                              timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    gcodes = sorted(work.glob("*.gcode"))
    if not gcodes:
        raise SupportAnalysisError(f"Orca produced no support G-code (exit {proc.returncode})")
    gcode = gcodes[0]
    toolpath = work / "support-toolpath.json"
    parsed = subprocess.run([sys.executable, str(PARSER), str(gcode), "--out", str(toolpath)],
                            cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    if parsed.returncode != 0:
        raise SupportAnalysisError((parsed.stderr or parsed.stdout)[-2000:])
    data = json.loads(toolpath.read_text(encoding="utf-8"))
    meta = data["meta"]
    area = 3.141592653589793 * (float(meta["diameter_mm"]) / 2) ** 2
    density = float(meta["density_g_cm3"])
    types = meta["types"]
    support_g = 0.0
    total_g = 0.0
    for move in data["moves"]:
        de = float(move[5])
        if move[8] or de <= 0:
            continue
        grams = de * area * density / 1000.0
        total_g += grams
        if types[move[7]] in SUPPORT_TYPES:
            support_g += grams
    return {
        "support_mass_g": round(support_g, 4),
        "total_mass_g": round(total_g, 4),
        "support_percent": round((support_g / total_g * 100.0) if total_g else 0.0, 2),
        "support_required": support_g > 0,
        "types": types,
        "gcode": str(gcode.relative_to(ROOT)).replace("\\", "/"),
        "log": str(log.relative_to(ROOT)).replace("\\", "/"),
        "note": "Real OrcaSlicer support slice; support filament mass from parsed G-code.",
    }
