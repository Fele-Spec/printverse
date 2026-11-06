---
name: printverse-mesh-preflight
description: Check and repair 3D-print meshes for watertightness, winding, non-manifold edges, degenerate faces, scale and printability. Use before slicing, before accepting AI-generated geometry, or when a mesh fails in OrcaSlicer.
whenToUse: A task involves STL/OBJ/GLB validation, mesh repair, unit checks, or deciding whether a generated model is printable.
metadata:
  version: "0.1.0"
  owner: PrintVerse
  license: MIT
  requires: [python, trimesh, scripts/mesh_audit.py, assets/processed]
---

# PrintVerse Mesh Preflight

## Inputs

- Candidate mesh path
- Expected dimensions and unit assumption (PrintVerse uses millimetres)
- Source/provenance row in `manifests/resources.json`

## Procedure

1. Load with vertex merging enabled: `trimesh.load(path, force="mesh", process=True)`.
   Never run topology checks with `process=False`; separate STL vertices produce false
   non-manifold results.
2. Compute: vertices, faces, watertight, winding consistency, `is_volume`, Euler number,
   body count, volume, area, extents, bounds.
3. Count boundary edges, edges with more than two incident faces, degenerate faces
   (`area < 1e-12`), duplicate face pairs, and self-intersections when the trimesh build
   exposes `mesh_self_intersection`.
4. Compare extents to the expected model size. Report a centerline-vs-outline difference
   separately from a unit error.
5. For a failure, repair a copy only: `fix_normals`, `fill_holes`, `fix_winding`, then
   export to `assets/processed/<name>_repaired.stl`. Never overwrite `assets/source/`.
6. Re-run every check on the repaired copy and report whether it actually improved.

## Command

```powershell
.\.venv\Scripts\python.exe scripts\mesh_audit.py
```

Outputs `docs/reports/mesh_audit.json` and `mesh_audit.csv`.

## Pass criteria

- watertight = true
- winding consistent = true
- `is_volume` = true and volume > 0
- non-manifold edges = 0
- degenerate faces = 0
- extents plausible for the intended part
- self-intersections 0 or explicitly reported as a tool limitation

A mesh may be intentionally open (a surface, a sign, a test coupon). Do not silently call it
printable; label it `NON_PRINTABLE_INTENTIONAL` only when the task says so.

## Failure handling

| Symptom | Action |
|---|---|
| every edge is a boundary | merge vertices with `process=True` |
| repair creates spikes | discard repaired file; keep original and mark BLOCKED |
| GLB has multiple scenes | evaluate each mesh and report the aggregate |
| scale is 1000x off | report a unit mismatch; do not guess the intended unit |
| self-intersection check unavailable | record `null` and say the check was not performed |

## Outputs

Mesh audit records with evidence paths, repair provenance, and a clear printability verdict.
