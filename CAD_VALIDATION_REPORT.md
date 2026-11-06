# PrintVerse CAD Validation Report

## 1. Source integrity

| Check | Result |
|---|---|
| Source | `VoronDesign/Voron-2`, tag `V2.4r2`, commit `45128487e8e8e4aa113bb2cbfdf5bf6752d242d3` |
| Archive | `Voron-2-V2.4r2.zip`, 342,066,710 bytes, SHA256 `e7891703dc5188a46fce6450ea2aee3e600038681526f436497cf5e7e2b2ef3b` |
| Git LFS pointers | none found; no CAD file is a small LFS pointer |
| Nested assembly ZIP | 1 entry, `zipfile.testzip()` returned clean |
| STEP header | `ISO-10303-21;`, STEP Tools/ST-Developer export |
| DXF/PDF/STEP/F3D header sweep | **17 / 17 passed** |

## 2. Collection

| Category | Count | Notes |
|---|---:|---|
| STL mechanical parts | 185 | full official folder hierarchy preserved |
| Assembly STEP | 1 | 267,315,729 bytes (extracted from nested ZIP) |
| Native F3D assembly | 1 | 86,593,649 bytes; Fusion 360 native, not FreeCAD-importable |
| Bed STEP | 3 | 250 / 300 / 350 mm build plates |
| DXF | 12 | panels and build plates |
| Drawing PDF | 6 | panel/build-plate drawings |
| Assembly manual PDF | 2 | normal + high-contrast |
| Voron firmware configs | 4 controller families | Octopus, SKR 1.3, SKR 1.4, Spider |

`CAD_ASSET_INDEX.csv` indexes 220 files including test models and processed previews. The
canonical category copies are under `assets/source/voron-v2.4r2-300/{CAD,STLs,DXF,Manual}`;
the untouched official tree is under `.../Voron-2-2.4r2/`.

## 3. Full-collection mesh sweep

All 185 STLs were loaded with trimesh 5.2.0 using vertex merging.

| Result | Count |
|---|---:|
| Loaded successfully | **185 / 185** |
| Watertight | **179 / 185** |
| Not watertight | **6 / 185** |
| Parse errors | 0 |

The six non-watertight official parts:

1. `STLs/Gantry/X_Axis/X_Carriage/Bowden/bowden_dual_front_a.stl`
2. `STLs/Gantry/X_Axis/X_Carriage/Bowden/bowden_single_front.stl`
3. `STLs/Gantry/X_Axis/X_Carriage/Direct_Feed/extruder_body.stl`
4. `STLs/Gantry/X_Axis/X_Carriage/Printheads/E3D_Revo_Micro/printhead_front_e3d_revo_micro.stl`
5. `STLs/Panel_Mounting/corner_panel_clip_4mm_x8.stl`
6. `STLs/Panel_Mounting/midspan_panel_clip_4mm_x7.stl`

These are official files, so they were **not** overwritten. Any repair must go to
`assets/processed/` after an explicit decision; no repair was claimed for these six.

## 4. FreeCAD imports

### STL — PASS

`STLs/Test_Prints/Filament_Card.stl`:

- 401 points, 802 facets, 1 mesh feature
- bbox 60 × 34 × 2 mm
- `Mesh.isSolid()` = true
- import 0.01 s

Evidence: `docs/reports/freecad_stl_test.json`.

### STEP — PASS

`DXF/Build_Plate/MIC6_Bed_V2_300.step`:

- 1 solid, 20 faces, 1 Part feature
- bbox 305 × 305 × 7.76 mm
- volume 721,126.835 mm³
- import 0.186 s

Evidence: `docs/reports/freecad_step_part_test.json`.

### Full assembly — PARTIAL

The 267 MB `VORON2.4_Assembly.step` was attempted in `FreeCADCmd`. It consumed 261.7 CPU
seconds and about 1.2 GB working set, but had not completed after roughly 4.5 minutes; the
process was stopped to keep the workspace responsive. No assembly bounding box is claimed.

Instead, the STEP text structure was parsed (`docs/reports/step_structure.json`):

| Structural count | Value |
|---|---:|
| `PRODUCT` entries | 1,534 |
| `NEXT_ASSEMBLY_USAGE_OCCURRENCE` | 1,544 |
| `MANIFOLD_SOLID_BREP` | 1,662 |
| `ADVANCED_BREP_SHAPE_REPRESENTATION` | 1,421 |
| `CARTESIAN_POINT` | 1,267,030 |
| `AXIS2_PLACEMENT_3D` | 187,334 |

Product names include `_VORON2.4_Assembly`, `Gantry`, `A/B Drives`, `Z Belt Clamp Upper`,
`GT2 20T 6mm`, `NEMA17`, idlers, shims and bearings. This proves a populated assembly graph
exists, but not that FreeCAD can resolve every constraint or that dimensions match a physical
machine. The full import remains **PARTIAL / timed out**.

## 5. Assembly relationship attempt

- Text-level parent/child links: 1,544 — a complete-looking solid assembly, not a flat dump.
- FreeCAD object tree: not obtained (timeout).
- BOM-to-CAD mapping: not established; product names are Fusion 360 occurrences and do not
  map one-to-one to BOM line items.
- Frame envelope: not measured from the imported assembly. The configurator independently
  derives a 460 × 460 × 480 mm frame for the 300 mm build.

## 6. Missing / at-risk data

1. No per-part STEP for every mechanical part; the exhaustive part geometry is STL, plus one
   whole-machine STEP and one F3D.
2. The F3D file requires Autodesk Fusion 360; it was integrity-checked as a ZIP container but
   not opened.
3. The full STEP import is too slow for the current headless audit; a tiled/partial import or
   a stronger CAD kernel is needed for production.
4. BOM line items are purchasing descriptions, not CAD instance IDs.
5. All dimensions are nominal CAD values; none were measured on a physical Voron.

## 7. Verdict

- Official CAD acquired and checksummed: **COMPLETE**
- STL collection structurally validated: **COMPLETE**
- STEP part import in FreeCAD: **COMPLETE**
- Full assembly import and dimensional audit: **PARTIAL** (timed out; text structure parsed)
