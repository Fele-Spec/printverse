---
name: printverse-cad-audit
description: Audit PrintVerse CAD assets — fixed-version STEP assemblies, STL parts, DXFs and official BOM data — using FreeCAD and deterministic file checks. Use when importing or validating Voron CAD, extracting bounding boxes, checking assembly completeness, or detecting Git LFS pointer files.
whenToUse: A task touches STEP/STP/STL/DXF integrity, FreeCAD import, assembly structure, dimensions, or CAD provenance.
metadata:
  version: "0.1.0"
  owner: PrintVerse
  license: MIT
  requires: [FreeCADCmd, python, assets/source, scripts/freecad_validate.py]
---

# PrintVerse CAD Audit

## Inputs

- Fixed official tag `V2.4r2` from `VoronDesign/Voron-2`
- `assets/source/voron-v2.4r2-300/CAD/`
- `assets/source/voron-v2.4r2-300/STLs/`
- `assets/source/voron-v2.4r2-300/DXF/`
- `manifests/resources.json`

## Preflight

1. Confirm the source tag/commit in `manifests/resources.json`; reject a moving branch.
2. Reject Git LFS pointer files: a CAD file under 1 KB whose text starts
   `version https://git-lfs.github.com/spec/v1`.
3. Test ZIP integrity before extraction (`zipfile.ZipFile.testzip()`), then record SHA256.
4. Keep the original archive and extracted official tree; never edit them.

## FreeCAD environment

FreeCAD writes a profile outside the workspace by default. Always set:

```powershell
$env:FREECAD_USER_HOME = '<project>\.cache\freecad\home'
$env:FREECAD_USER_DATA = '<project>\.cache\freecad\data'
$env:FREECAD_USER_TEMP = '<project>\.cache\freecad\temp'
```

Run the importer through the console pipe because `FreeCADCmd` reserves CLI options:

```powershell
$env:PV_SCRIPT = '<project>\scripts\freecad_validate.py'
$env:PV_OUT = '<project>\docs\reports\freecad_import.json'
$env:PV_STL = '<part.stl>'
$env:PV_STEP = '<assembly.step>'
cmd /c "type scripts\freecad_entry.py | `"<FreeCADCmd.exe>`" -c"
```

## Checks

For every imported object record: object count, solids, faces, mesh points/facets,
bounding box in mm, volume, import seconds, and `ok`.

For the assembly:

- `ISO-10303-21` header and `FILE_SCHEMA` present
- non-zero solids and a plausible printer envelope (roughly 460 x 460 x 480 mm frame)
- no placeholder/zero-face parts
- missing sub-assemblies listed explicitly (do not infer from filenames alone)

For STLs: delegate topology to `printverse-mesh-preflight`.

## Failure handling

| Symptom | Action |
|---|---|
| `Could not create directories` | set `FREECAD_USER_*` inside the workspace |
| `unrecognised option '--stl'` | use `freecad_entry.py` stdin bridge, not positional args |
| `no supported file format` | use `Mesh.Mesh(path)` for STL; `Import.insert` for STEP |
| import takes too long | record timeout; validate a representative part and mark assembly PARTIAL |
| file is an LFS pointer | fetch with Git LFS or re-download the official archive; never rename the pointer |

## Outputs

- `docs/reports/freecad_import.json`
- `docs/reports/CAD_VALIDATION_REPORT.md`
- `docs/reports/CAD_ASSET_INDEX.csv`
- updated `manifests/checksums.sha256`

## Acceptance

PASS only when at least one STEP and one STL import returns a non-empty shape/mesh, the
assembly envelope is plausible, every count is reproducible, and no source file was edited.
