# PHASE 3 COMPLETION REPORT

Date: 2026-11-06 · Project: PrintVerse · Machine: Voron V2.4r2 300

## 1. Executive status

| Goal | Status |
|---|---|
| A. Replace proxy geometry with real FreeCAD modules | **PARTIAL — real modules + toolhead/bed motion; XY crossbeam still static** |
| B. High-end industrial 3D visual upgrade | **COMPLETE for the reviewed desktop views** |
| 4,526 placements audit | **COMPLETE** |
| Eight modular GLBs | **COMPLETE** |
| Part selection / inspector | **COMPLETE** |
| View presets / ortho / transparency / explode / module visibility | **COMPLETE** |
| 45 FPS target | **PASS on hardware (60.1 FPS); software headless PARTIAL** |
| InstancedMesh fasteners | **PARTIAL — not implemented** |
| Exact 275/280 resolution | **COMPLETE; physical clearance remains PHYSICAL_PENDING** |
| Image-to-3D | **DEFERRED / BLOCKED by 8 GB VRAM** |

Overall: **PARTIAL**. The real CAD toolhead and platform now follow the G-code, but the XY
crossbeam is still one merged static module and repeated fasteners are not instanced. Neither
is hidden.

## 2. Current project state

- Working tree clean at start; branch `master`.
- Frontend: React 19 + Three.js 0.187 + R3F 9.8 + Drei 10.7.
- Backend and preview running on `127.0.0.1:8000` and `127.0.0.1:4173`.
- No real printer, payment, cloud GPU or paid API was touched.

## 3. What was delivered

### 3.1 CAD audit

- 4,881 FreeCAD document objects → **4,526 placements** after excluding 355 internal
  `App::Origin` nodes.
- **1,686** Part::Feature solids, **355** App::Part assemblies, **2,485** construction
  Line/Plane/Point objects.
- 0 duplicate part IDs.
- 1 zero/negative-volume solid (`F0490`).
- 20 sampled parts: **20/20 dimension match** against saved FreeCAD bbox extents (sorted axes),
  maximum difference 0.0001 mm.
- Correct transform rule: shape includes own Placement; only parent global applied. The first
  erroneous global-apply run produced a −406..−349 X bbox; corrected result is −78..38 X.

Files: `CAD_PLACEMENT_AUDIT.md`, `docs/reports/placements_audit.json`,
`docs/reports/placement_samples.json`, `manifests/placements.json`.

### 3.2 Eight modular GLBs

`assets/models/voron/modules/` and `frontend/public/models/voron/modules/`:

| Module | Parts | Full MB | LOD MB |
|---|---:|---:|---:|
| FRAME | 182 | 2.25 | 0.69 |
| ENCLOSURE | 392 | 7.62 | 1.39 |
| XY_GANTRY | 470 | 7.68 | 2.09 |
| Z_DRIVE | 315 | 7.32 | 2.54 |
| TOOLHEAD | 180 | 5.36 | 1.04 |
| BUILD_PLATFORM | 16 | 0.17 | 0.04 |
| ELECTRONICS | 130 | 3.28 | 0.68 |
| WIRING | 1 | 0.17 | 0.03 |
| **Total** | **1,686** | **35.49** | **8.92** |

- Full GLBs: one node per placement, node metadata.
- LOD GLBs: merged module mesh + `module-face-ranges-lod.json` face-to-placement map for picking.
- Unit conversion: mm → m, exactly one 0.001 scale.
- Manifest: `CAD_MODULE_MANIFEST.json`.

### 3.3 Visual upgrade

- ACES Filmic, sRGB, exposure 1.42, procedural Lightformer studio, key/fill/rim, contact shadow.
- 12-material `MATERIAL_LIBRARY.json`; module material groups; smoked/clear/hidden enclosure.
- Six camera presets + orthographic camera; CAD-specific target framing.
- Explode slider/preset, module toggles, part inspector with dimensions/material/path and a
  selection box.
- Part click test: `SOLID116`, ENCLOSURE, 191.5×3.0×403.0 mm, placement F4208, path
  `.../Front Door Right/SOLID116`, no errors.
- Before/after folder with 4 before and 10 after images.

### 3.4 Performance

- Hardware WebGL (AMD Radeon 610M, D3D11): **60.1 FPS**, 181 render frames / 3 s.
- Headless SwiftShader: 0.8–2.2 FPS; not a hardware reference.
- First visible scene: **8.0–9.1 s** local.
- Load errors / page errors: **0**.
- Default draw calls: 8 merged modules; high detail: 1,686 parts.
- No InstancedMesh; no Draco/Meshopt.

## 4. Functional regression

The phase-2 acceptance still passes after the visual/CAD changes:

- clean wallet 100.00 g / first print free;
- upload `cube.stl` → Orca slice → 100 layers / 3.978 g;
- PRINTING → COMPLETE → DETACHED → collection 1;
- 0 console errors, 0 HTTP failures.

Evidence: `docs/reports/phase2_e2e.json`.

## 5. Deliverables

| Required | File |
|---|---|
| CAD placement audit | `CAD_PLACEMENT_AUDIT.md` |
| Module manifest | `CAD_MODULE_MANIFEST.json` |
| Eight module GLBs | `assets/models/voron/modules/*.glb` |
| Assembly hierarchy | `ASSEMBLY_HIERARCHY.json` |
| Material library | `MATERIAL_LIBRARY.json` |
| Model validation | `MODEL_VALIDATION_REPORT.md` |
| Visual upgrade | `VISUAL_UPGRADE_REPORT.md` |
| Performance | `PERFORMANCE_REPORT.md` |
| Height clearance | `HEIGHT_CLEARANCE_ANALYSIS.md` |
| Before/after screenshots | `BEFORE_AFTER_SCREENSHOTS/` |
| Phase completion | this file |

## 6. Open items and next smallest steps

1. **Split the XY gantry crossbeam from its static rails.** The toolhead and platform now move
   inside the real CAD hierarchy, but the whole XY_GANTRY module is still static. Split the
   crossbeam into a movable node to complete CoreXY visualization.
2. **InstancedMesh for fasteners.** Deduplicate screw/nut/washer geometry and use instanced
   matrices for the hundreds of repeated standard parts; keep part metadata in an instance map.
3. **Wire harness.** WIRING currently has only one solid; cable-chain and wire geometry are
   mostly construction objects. Add sourced cable geometry or explicitly mark the module as
   partial in the UI.
4. **Normal maps/texture atlases.** The material library is parameter-driven; no UV normal maps
   are authored yet.
5. **Physical Z clearance.** The CAD gap is 222 mm toolhead-to-top; the moving bed and cable
   chain still require real measurement. `verified_physical_z_clearance_mm` stays null.
6. **Image-to-3D.** Deferred; no large weights or paid service downloaded.

## 7. Honest statement

The printer is no longer a decorative parts collage: the real frame, enclosure, gantry, Z drive,
toolhead, platform, electronics and the one available wiring part are loaded from the official
FreeCAD assembly. The toolhead and platform now move inside that real hierarchy during G-code
playback. The XY crossbeam remains static and fasteners are not instanced, so the overall phase
status is **PARTIAL**, not COMPLETE.
