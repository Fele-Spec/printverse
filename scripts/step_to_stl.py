"""FreeCAD STEP -> STL conversion for the standalone import path.

Run with FreeCADCmd:
  FreeCADCmd.exe scripts/step_to_stl.py input.step output.stl
"""
from __future__ import annotations

import os
import sys

import FreeCAD
import Mesh
import Part


def main() -> int:
    src = os.environ.get("STEP_INPUT") or (sys.argv[1] if len(sys.argv) > 1 else "")
    dst = os.environ.get("STL_OUTPUT") or (sys.argv[2] if len(sys.argv) > 2 else "")
    if not src or not dst:
        print("usage: step_to_stl.py input.step output.stl", file=sys.stderr)
        return 2
    shape = Part.Shape()
    shape.read(src)
    if shape.isNull():
        print("no shape found", file=sys.stderr)
        return 3
    mesh = Mesh.Mesh(shape.tessellate(0.15))
    mesh.write(dst)
    print(f"STEP_OK faces={len(shape.Faces)} triangles={mesh.CountFacets} output={dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
