"""Mesh the official 300 mm bed STEP with FreeCAD and export STL for the Web scene."""
import MeshPart
import Import
import FreeCAD
from pathlib import Path

ROOT = Path(r"C:\Users\someb\Desktop\printverse")
STEP = ROOT / "assets/source/voron-v2.4r2-300/DXF/Build_Plate/MIC6_Bed_V2_300.step"
OUT = ROOT / "frontend/public/models/voron_300_bed.stl"
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = FreeCAD.newDocument("bed_mesh")
Import.insert(str(STEP), doc.Name)
doc.recompute()
obj = next(o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull())
mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=0.35, AngularDeflection=0.45, Relative=False)
mesh.write(str(OUT))
print("BED_MESH", mesh.CountPoints, mesh.CountFacets, OUT.stat().st_size)
