"""STEP import through the bundled FreeCAD CLI (Windows-local path)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FREECAD = ROOT / "tools" / "FreeCAD-1.1.4" / "FreeCAD_1.1.4-Windows-x86_64-py311" / "FreeCADCmd.exe"
SCRIPT = ROOT / "scripts" / "step_to_stl.py"


class StepImportError(RuntimeError):
    pass


def convert_step(src: Path, dst: Path, timeout: int = 300) -> None:
    if not FREECAD.exists():
        raise StepImportError("FreeCADCmd missing; cannot import STEP")
    dst.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    # FreeCAD otherwise writes to the user's AppData, which may be sandboxed.
    env["FREECAD_USER_HOME"] = str(ROOT / ".cache" / "freecad-home")
    env["HOME"] = env["FREECAD_USER_HOME"]
    env["APPDATA"] = str(ROOT / ".cache" / "freecad-config")
    env["STEP_INPUT"] = str(src)
    env["STL_OUTPUT"] = str(dst)
    command = f"exec(open(r'{SCRIPT}').read())"
    proc = subprocess.run(
        [str(FREECAD), "-c", command], cwd=str(ROOT), env=env,
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0 or not dst.exists() or dst.stat().st_size < 100:
        raise StepImportError((proc.stderr or proc.stdout or "STEP conversion failed")[-3000:])
