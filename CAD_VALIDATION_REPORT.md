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

### Full assembly — geometry import COMPLETE; transform audit PARTIAL

The 267 MB `VORON2.4_Assembly.step` was imported with **build123d 0.13.0 / OCP 8.0.1.1.0**
(`scripts/full_step_import.py`), not FreeCAD. Result (`docs/reports/full_step_import.json`):

| Metric | Value |
|---|---:|
| Import time | 76.17 s |
| Solids returned | 1,677 |
| Volume | 122,455.72 mm³ |
| Bounding box | 430 × 534.154 × 522 mm |
| BBox min / max | (−88, −49, −143.096) / (342, 485.154, 378.904) |

The STEP text structure (`docs/reports/step_structure.json`) gives:

| Structural count | Value |
|---|---:|
| `PRODUCT` entries | 1,534 |
| `NEXT_ASSEMBLY_USAGE_OCCURRENCE` | 1,544 |
| `MANIFOLD_SOLID_BREP` | 1,662 |
| `ADVANCED_BREP_SHAPE_REPRESENTATION` | 1,421 |
| `CARTESIAN_POINT` | 1,267,030 |
| `AXIS2_PLACEMENT_3D` | 187,334 |

The imported bounding box is **not** 460 × 460 × 480 mm. It is evidence that the assembly
contains geometry/transform outliers or parts that extend beyond the frame; it is **not** used
as the frame envelope. The authoritative frame envelope remains the configurator/BOM-derived
460 × 460 × 480 mm.

### Name-preserving XCAF hierarchy — names COMPLETE, transforms PARTIAL

A separate XCAF traversal (`scripts/step_xcaf_tree.py`, OCP 7.9) recovered the real product
tree: **1,690 nodes**, depth 7, root `_VORON2.4_Assembly v89`. The nine top-level groups are:

| Group | Direct children |
|---|---:|
| Gantry | 12 |
| Z Assembly | 9 |
| Electronics | 14 |
| Skirt | 3 |
| Frame | 5 |
| Bed Components | 1 |
| Panels | 8 |
| Spool Holder | 5 |
| Exhaust Filter Assembly | 8 |

The XCAF root bbox is 432 × 536.452 × 524 mm (same anomaly family as the build123d import).
`XCAFDoc_ShapeTool.GetLocation_s` returned identity for all 1,690 nodes, and
`XCAFDoc_Location.FindAttribute` crashes in this OCP 7.9 binding. Top-group bboxes are recorded
in `docs/reports/step_xcaf_tree.json` (e.g. Frame group 410 × 410 × 430 mm), but they are not
used to overwrite the configurator frame envelope. Names and parent/child relationships are
real and stored in `docs/reports/step_xcaf_tree.json` and `manifests/machine-hierarchy.json`.

### FreeCAD full object tree — geometry and placements (complete audit)

A second independent full import with FreeCAD 1.1.4 completed in **230.83 s** and yielded
**4,526 objects** (`docs/reports/freecad_full_tree.json`):

| Object type | Count | Meaning |
|---|---:|---|
| `Part::Feature` | 1,686 | actual solid/part shapes |
| `App::Part` | 355 | named sub-assemblies |
| `App::Line` / `App::Plane` / `App::Point` | 1,065 / 1,065 / 355 | construction geometry |
| Other | 1 | — |

The tree includes named assemblies such as `Gantry`, `Z Assembly`, `Frame`, `Bed Components`,
`Toolheads`, `X Carriage`, `XY Joint - Left`, `XY Joint - Right`, `A/B Drives`, and
`X Axis (MGN12)`. **2,977 objects have a non-identity `Placement`** (translation + rotation),
so object-level assembly placements now exist. The finite `Part::Feature` union is
714.58 × 801.98 × 826.99 mm, which includes outliers (spool/exhaust/construction geometry);
it is not used as the frame envelope.

The Web scene still uses nominal BOM dimensions and the verified kinematic hierarchy; it does
not yet serialize all 4,526 FreeCAD placements into glTF. This is a **PARTIAL integration**, not
a missing CAD import.

## 5. Assembly relationship model

- Text-level parent/child links: 1,544 — a populated solid assembly, not a flat dump.
- Product categories from the STEP names (`manifests/machine-hierarchy.json`):
  FRAME 234, CORE_XY_GANTRY 119, Z_AXIS 18, TOOLHEAD 46, ELECTRONICS_BAY 33,
  MOTION_HARDWARE 228, OTHER 856.
- The Web scene uses a verified kinematic hierarchy (frame → CoreXY gantry → toolhead,
  frame → four-point Z → bed → printed object). Positions are nominal dimensions from the
  official BOM/configurator; they are not claimed to be exact STEP transforms.
- BOM-to-CAD mapping is not one-to-one; product occurrence names and purchasing descriptions
  are different vocabularies.
- Frame envelope: 460 × 460 × 480 mm (configurator/BOM). Imported STEP bbox is retained as
  an anomaly to investigate, not silently normalized.

## 6. Missing / at-risk data

1. No per-part STEP for every mechanical part; the exhaustive part geometry is STL, plus one
   whole-machine STEP and one F3D.
2. The F3D file requires Autodesk Fusion 360; it was integrity-checked as a ZIP container but
   not opened.
3. XCAF product names/hierarchy are recovered, but component world transforms are identity
   fallback because the OCP 7.9 location-attribute binding crashes; the Web scene uses a
   nominal kinematic hierarchy.
4. BOM line items are purchasing descriptions, not CAD instance IDs.
5. All dimensions are nominal CAD values; none were measured on a physical Voron.

## 7. Verdict

- Official CAD acquired and checksummed: **COMPLETE**
- STL collection structurally validated: **COMPLETE**
- STEP part import in FreeCAD: **COMPLETE**
- Full assembly geometry import: **COMPLETE** (1,677 solids, 76 s)
- Name-preserving product hierarchy: **COMPLETE** (1,690 XCAF nodes, 9 top groups)
- Object-level placements: **COMPLETE** (4,526 FreeCAD objects, 2,977 non-identity placements)
- Exact placements serialized into the Web scene: **PARTIAL** (scene still nominal proxy)
- Dimensional audit against a physical machine: **PHYSICAL_PENDING**
