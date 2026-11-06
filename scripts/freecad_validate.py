"""Validate Voron CAD/STL assets with FreeCAD's own importers.

Run with the bundled FreeCADCmd and FREECAD_USER_* pointed inside the workspace:
  freecadcmd.exe scripts/freecad_validate.py --out docs/reports/freecad_import.json \
      --stl <file.stl> --step <assembly.step>
"""
import argparse
import json
import os
import sys
import time

import FreeCAD
import Import


def doc_bbox(doc):
    bb = FreeCAD.BoundBox()
    found = False
    for obj in doc.Objects:
        try:
            if hasattr(obj, "Shape") and obj.Shape is not None and not obj.Shape.isNull():
                bb.add(obj.Shape.BoundBox)
                found = True
            elif hasattr(obj, "Mesh") and obj.Mesh is not None and obj.Mesh.CountPoints > 0:
                bb.add(obj.Mesh.BoundBox)
                found = True
        except Exception:
            continue
    return {
        "valid": found,
        "xmin": round(bb.XMin, 4), "ymin": round(bb.YMin, 4), "zmin": round(bb.ZMin, 4),
        "xmax": round(bb.XMax, 4), "ymax": round(bb.YMax, 4), "zmax": round(bb.ZMax, 4),
        "dx": round(bb.XLength, 4), "dy": round(bb.YLength, 4), "dz": round(bb.ZLength, 4),
    } if found else {"valid": False}


def import_file(path, label):
    t0 = time.time()
    doc = FreeCAD.newDocument(label)
    if path.lower().endswith((".stl", ".obj")):
        import Mesh
        mesh = Mesh.Mesh(path)
        obj = doc.addObject("Mesh::Feature", "imported_mesh")
        obj.Mesh = mesh
    else:
        Import.insert(path, doc.Name)
    doc.recompute()
    elapsed = time.time() - t0
    shapes, meshes, solids, faces = [], [], 0, 0
    volume = 0.0
    for obj in doc.Objects:
        try:
            if hasattr(obj, "Shape") and obj.Shape is not None and not obj.Shape.isNull():
                shapes.append(obj)
                solids += len(obj.Shape.Solids)
                faces += len(obj.Shape.Faces)
                if obj.Shape.Volume:
                    volume += obj.Shape.Volume
            elif hasattr(obj, "Mesh") and obj.Mesh is not None:
                meshes.append(obj)
        except Exception:
            continue
    result = {
        "path": os.path.abspath(path),
        "bytes": os.path.getsize(path),
        "label": label,
        "elapsed_s": round(elapsed, 3),
        "object_count": len(doc.Objects),
        "part_feature_count": len(shapes),
        "mesh_feature_count": len(meshes),
        "solid_count": solids,
        "face_count": faces,
        "volume_mm3": round(volume, 3),
        "bbox_mm": doc_bbox(doc),
        "ok": bool(shapes or meshes),
    }
    if meshes:
        result["mesh_points"] = sum(o.Mesh.CountPoints for o in meshes)
        result["mesh_facets"] = sum(o.Mesh.CountFacets for o in meshes)
        try:
            result["mesh_solid_flags"] = [bool(o.Mesh.isSolid()) for o in meshes]
        except Exception:
            result["mesh_solid_flags"] = None
    FreeCAD.closeDocument(doc.Name)
    return result


def main():
    # FreeCADCmd reserves CLI options, so harnesses pass the job through env vars.
    if os.environ.get("PV_OUT"):
        args = argparse.Namespace(
            out=os.environ["PV_OUT"],
            stl=[p for p in os.environ.get("PV_STL", "").split(";") if p],
            step=[p for p in os.environ.get("PV_STEP", "").split(";") if p],
        )
    else:
        ap = argparse.ArgumentParser()
        ap.add_argument("--out", required=True)
        ap.add_argument("--stl", action="append", default=[])
        ap.add_argument("--step", action="append", default=[])
        args = ap.parse_args()
    report = {
        "freecad_version": list(FreeCAD.Version()),
        "python": sys.version,
        "cwd": os.getcwd(),
        "imports": [],
    }
    for p in args.stl:
        try:
            report["imports"].append(import_file(p, "stl"))
        except Exception as e:
            report["imports"].append({"path": os.path.abspath(p), "kind": "stl", "ok": False, "error": repr(e)})
    for p in args.step:
        try:
            report["imports"].append(import_file(p, "step"))
        except Exception as e:
            report["imports"].append({"path": os.path.abspath(p), "kind": "step", "ok": False, "error": repr(e)})
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not any(i.get("ok") for i in report["imports"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
