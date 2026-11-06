# Model Validation Report

Date: 2026-11-06 · Source: `VORON2.4_Assembly.step` → `.cache/voron_full.FCStd` → `assets/models/voron/modules/`

## 1. Placement audit

| Metric | Result |
|---|---:|
| FreeCAD document objects | 4,881 |
| Placements after excluding internal `App::Origin` | **4,526** |
| `Part::Feature` shape-bearing solids | **1,686** |
| `App::Part` assembly nodes | 355 |
| `App::Line` / `App::Plane` / `App::Point` construction | 2,485 |
| Duplicate part IDs | **0** |
| Zero/negative-volume solids | **1** (`F0490`, `COMPOUND003`, −9.421 mm³) |
| Units | mm source / m glTF / scale **0.001 once** |
| Double placement | **fixed**: shape includes own Placement; only parent global applied |

Evidence: `CAD_PLACEMENT_AUDIT.md`, `docs/reports/placements_audit.json`, `manifests/placements.json`,
`ASSEMBLY_HIERARCHY.json`.

## 2. Twenty-category dimension sample

Using sorted axis extents (parent rotations permute X/Y/Z):

- **20 / 20 MATCH**
- maximum absolute difference: **0.0001 mm**
- examples: Panel 369.1999×369.2×3.0, MIC6 plate 254×254×7.76, B Drive Frame Upper 116×57.0274×16.0

This is an internal consistency check between the world bbox and the saved FreeCAD object bbox,
not an independent physical measurement. Details: `docs/reports/placement_samples.json`.

## 3. Eight modules

| Module | Parts | Full faces | Full MB | LOD faces | LOD MB |
|---|---:|---:|---:|---:|---:|
| FRAME | 182 | 124,338 | 2.25 | 40,265 | 0.69 |
| ENCLOSURE | 392 | 430,094 | 7.62 | 81,057 | 1.39 |
| XY_GANTRY | 470 | 438,166 | 7.68 | 122,042 | 2.09 |
| Z_DRIVE | 315 | 434,246 | 7.32 | 148,880 | 2.54 |
| TOOLHEAD | 180 | 302,583 | 5.36 | 60,455 | 1.04 |
| BUILD_PLATFORM | 16 | 9,194 | 0.17 | 2,516 | 0.04 |
| ELECTRONICS | 130 | 191,532 | 3.28 | 40,236 | 0.68 |
| WIRING | 1 | 9,714 | 0.17 | 1,748 | 0.03 |
| **Total** | **1,686** | **1,939,867** | **35.49** | **497,199** | **8.92** |

- Full `.glb` files preserve one node per placement and node metadata (placement ID, name, path,
  module, source unit, faces). Full hierarchy is 1,686 nodes plus module roots in `trimesh`.
- `.lod.glb` files are one merged mesh per module for draw-call performance; face ranges are in
  `frontend/public/models/voron/module-face-ranges-lod.json`, enabling face → placement selection.
- `.merged.glb` files are intermediate full-detail merges; they are retained but not used by default.

## 4. Coordinate / scale validation

- FreeCAD/STEP coordinates: millimetres.
- glTF conversion: exactly one `0.001` scale in `scripts/build_module_glb.py`.
- Scene normalization: `position = [-127, -127, 58]` mm and `scale = 1000` in
  `RealModules.tsx`; this maps the assembly bed centre and frame bottom into the existing
  Three.js stage.
- Raw module bounds (m):
  - FRAME x −0.078..0.332, y −0.038..0.464, z −0.058..0.379
  - XY_GANTRY x −0.078..0.332, y −0.036..0.370, z −0.035..0.265
  - TOOLHEAD x 0.097..0.169, y 0.091..0.192, z 0.028..0.157
  - BUILD_PLATFORM x 0..0.254, y −0.008..0.262, z −0.021..0.000

## 5. Load / runtime errors

- Browser test: **0 pageerrors**, **0 console errors**, **0 failed HTTP requests**.
- All eight GLBs loaded; 4,526 placement index loaded; face-range selection works.
- Part click test returned `SOLID116`, module `ENCLOSURE`, dimensions `191.5 × 3.0 × 403.0 mm`,
  placement `F4208`, path `... / Front Door Right / SOLID116`.

## 6. Known defects

1. `WIRING` has only one shape-bearing part (Cable Cover); cable chains/wires are largely
   construction geometry, so the module is **PARTIAL**, not a full harness.
2. One zero/negative-volume compound `F0490` is flagged and retained; it may render as an
   open/inverted detail.
3. The raw assembly envelope is 430×534.45×522 mm, not 460×460×480; spool/exhaust/cable outliers
   and assembly coordinates mean it must not be used as the frame envelope.
4. Exact FreeCAD global coordinates are applied to the static CAD display; the print simulation
   still uses the separate kinematic proxy for toolhead/bed motion.
5. InstancedMesh is not used for repeated fasteners yet; this is a performance/quality item,
   not hidden.
