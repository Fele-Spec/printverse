# PrintVerse Phase 2 — Core Virtual Print Loop

Date: 2026-11-06 · Root: `C:\Users\someb\Desktop\printverse`

## 1. Verdict

| Area | Status | Evidence |
|---|---|---|
| 275 vs 280 mm mechanical conflict | **COMPLETE** | `MECHANICAL_PARAMETERS.md`; Klipper 300 config `position_max: 280`; Orca `printable_height: 275` |
| Full STEP geometry import | **COMPLETE** | build123d/OCP imported 267 MB / 1,677 solids in 76.17 s |
| Exact STEP assembly transforms | **PARTIAL** | XCAF names/hierarchy recovered (1,690 nodes); FreeCAD 4,526 objects with 2,977 non-identity placements; Web scene does not yet serialize those placements |
| Mechanical scene hierarchy + articulation | **COMPLETE (proxy)** | frame / CoreXY gantry / toolhead / four-point Z / bed / printed-object nodes; `docs/architecture/MECHANICAL_SCENE.md` |
| STL → Orca → G-code → parser → animation | **COMPLETE** | real upload slice; 100 layers; 7,853 toolpath moves; WebGL E2E |
| Detach / translate / rotate / scale / collect | **COMPLETE** | `TransformControls`; E2E status `DETACHED`; collection item created |
| Virtual filament accounting | **COMPLETE** | 6 deterministic tests + API wallet/reserve/commit/release |
| CadQuery/build123d isolation | **COMPLETE** | build123d/OCP 8 main venv; CadQuery 2.8/OCP 7.9 in `.venv-cadquery`; both `box` tests pass |
| Image-to-3D | **DEFERRED / BLOCKED** | 8 GB VRAM; Hunyuan3D 10–29 GB, TRELLIS ≥16 GB; no paid API used |

Overall phase verdict: **PARTIAL** — the requested upload→virtual print→detach→collect loop passes,
but the exact STEP transform hierarchy is not yet name-preserving and the scene uses verified
nominal dimensions for major modules. Do not present the kinematic proxy as exact CAD placement.

## 2. Mechanical height resolution

| Claim | Source | Verdict |
|---|---|---|
| **280 mm** | `assets/.../Voron2_Octopus_Config.cfg`, `[stepper_z]`, “300mm build” → `#position_max: 280` | Mechanical Z travel/soft max |
| **280 mm** | configurator `build_z = frame_z - 200` for 300 spec | Configurator build Z |
| **275 mm** | `configs/machine/voron-v2.4r2-300-0.4.json` `printable_height` | Orca vendor safety ceiling |
| **5 mm** | difference | **Inferred** safety headroom; not documented in JSON |
| 300 mm Z | none | **False**; 300 is X/Y. Frame is 460×460×480 |

The scene uses 300×300 XY, 280 Z mechanical travel, and a 275 mm slicer admission ceiling.
A community report notes toolhead collisions near the top/front with Stealthburner/Tap; that
remains **PHYSICAL_PENDING**.

## 3. CAD import

- **Full geometry:** build123d 0.13.0 + OCP 8.0.1.1.0 loaded the 267,315,729-byte STEP in
  **76.17 s**, returning **1,677 solids**, volume 122,455.72 mm³.
- **Anomaly:** imported bbox is 430 × 534.154 × 522 mm, not the 460 × 460 × 480 mm frame.
  It is retained as an explicit anomaly and not silently normalized. Likely causes: assembly
  transform/outlier parts; name-preserving XCAF traversal is the next audit.
- **Product hierarchy:** text-level categories cover 1,534 products; the XCAF traversal
  recovered **1,690 real nodes** with 9 top groups (`Gantry`, `Z Assembly`, `Electronics`,
  `Skirt`, `Frame`, `Bed Components`, `Panels`, `Spool Holder`, `Exhaust Filter Assembly`).
  Evidence: `docs/reports/step_xcaf_tree.json`, `manifests/machine-hierarchy.json`.
- **FreeCAD object placements:** the second full import completed in 230.83 s with 4,526
  objects (1,686 `Part::Feature`, 355 `App::Part`, the rest construction geometry) and
  **2,977 non-identity placements**. See `docs/reports/freecad_full_tree.json`.
- **XCAF names:** 1,690 nodes / 9 top groups. `GetLocation_s` returned identity for every
  node, and `XCAFDoc_Location` binding crashes; it is not used for transforms.
- **Real CAD mesh in the Web scene:** the official `MIC6_Bed_V2_300.step` was meshed by
  FreeCAD (`scripts/freecad_mesh_bed.py`) to a 57,884-byte STL: 568 vertices, 1,156 faces,
  watertight, 305 × 305 × 7.76 mm. It is loaded as the actual bed plate in
  `frontend/public/models/voron_300_bed.stl`; the frame/toolhead remain proxies.
- **Web scene:** uses the recovered hierarchy and nominal BOM dimensions; it does not yet
  serialize the 4,526 FreeCAD placements into glTF. See `docs/architecture/MECHANICAL_SCENE.md`.

## 4. Real G-code loop

Test: 20×20×20 mm cube, uploaded through the real API endpoint, sliced by OrcaSlicer 2.4.2
with the resolved Voron 300 profiles.

| Item | Result |
|---|---|
| API `POST /api/jobs` | HTTP 200, `ready` |
| Slice notice | `Sliced cube.stl: 100 layers, 3.978 g` |
| G-code layers | 100 |
| Toolpath moves | 7,853 (extrusion + travel; real G-code) |
| Material | 1,333.886 mm filament, 3,978.4 mg |
| Slicer estimate | 1,192 s (19m52s) |
| Animation timeline | 408.4 s equivalent motion; viewer speed 300× in E2E |
| Toolhead | follows G-code X/Y; world Z fixed at bed datum |
| Bed | moves down by G-code Z (`bed world = 300 − z`) |
| Material | extrusion segments only; no fake path |

E2E evidence: `docs/reports/phase2_e2e.json`

- initial `READY`; uploaded `READY`; mid `PRINTING`; complete `COMPLETE`; detach `DETACHED`.
- collection item count ≥1; WebGL 2.0; **0 console errors; 0 HTTP failures**.
- Screenshots: `assets/previews/phase2_scene_initial.png`, `_printing.png`, `_complete.png`,
  `_detached.png`, `_collection.png`.

The final solid shown on the bed is the uploaded STL; the deposited toolpath is the actual
G-code extrusion path. The toolhead is parked at the rear after completion so the part is
visible.

## 5. Finished-object interaction

- `TransformControls` attaches to the actual printed-object group, not a wrapper at world
  origin.
- Modes: translate / rotate / scale; OrbitControls is disabled by the control while dragging.
- `Detach from bed` changes state to `DETACHED`; the object is no longer parented to the moving
  bed group.
- `Add to collection` calls `POST /api/collection`; collection is persisted in SQLite and
  returned by `GET /api/collection`.
- E2E screenshot shows a centered gizmo around the 20 mm cube; no page errors.

## 6. Virtual filament accounting

Backend: FastAPI + SQLite, integer milligrams, no payment provider.

Rules tested:

1. First virtual print free, once.
2. Second print reserves/deducts by G-code mass.
3. Cancel refunds and restores the free entitlement.
4. Duplicate reserve/complete/collection calls are idempotent.
5. Insufficient balance raises and does not charge.
6. Admin unlimited does not consume the free entitlement or balance.

Test command:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q -p no:cacheprovider
# 6 passed
```

The clean E2E run showed the first virtual print free: wallet stayed **100.00 g → 100.00 g**
while the entitlement changed to used, and one collection item was created. The independent
accounting test then verifies the next paid job reserves 3.978 g: **100.000 g → 96.022 g**.
The final delivered database is reset so a new user sees the first print free again.

## 7. API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | service health |
| GET | `/api/machine` | resolved parameters (275/280) |
| GET | `/api/wallet` | virtual balance + entitlement + ledger |
| POST | `/api/jobs` | upload STL, real Orca slice, reserve |
| GET | `/api/jobs/{id}` | job + wallet |
| POST | `/api/jobs/{id}/complete` | commit completed print |
| POST | `/api/jobs/{id}/cancel` | release reservation |
| GET/POST | `/api/collection` | list/save finished object |

Runtime artifacts are served at `/runtime/jobs/...`; source and generated files stay under
`runtime/` and are ignored by Git.

## 8. CadQuery isolation

- Main venv: build123d 0.13.0 + `cadquery-ocp-novtk` 8.0.1.1.0.
- Separate `.venv-cadquery`: CadQuery 2.8.0 + `cadquery-ocp` 7.9.3.1.
- Tests: `assets/processed/build123d_test.step` (6,000 mm³), `assets/processed/cadquery_test.step`
  (6,000 mm³, 15,478 bytes).
- Locks: `requirements.lock`, `requirements-cadquery.lock`.

## 9. Known limitations

1. XCAF names/hierarchy are now recovered, but exact STEP world transforms are still missing
   (location-attribute binding crash); the scene uses nominal kinematic placement. This is the
   main remaining gap to a “full CAD” claim.
2. One real CAD mesh (the 305 × 305 × 7.76 mm bed plate, 1,156 faces) is integrated. The
   toolhead and frame are still simplified procedural geometry; the 4,526 FreeCAD placements
   are not yet serialized into glTF.
3. Full imported STEP bbox anomaly (430×534×522) needs investigation.
4. E2E animation uses a 300× viewer speed to finish in seconds; the real slicer estimate is
   19m52s. Speed is a UI control, not a fabricated time.
5. Chromium requires an approved full-access or non-sandboxed session in this environment.
6. No real printer, heating, firmware, Moonraker or payment was touched.

## 10. Next smallest steps

1. Serialize the 4,526 FreeCAD object placements into a glTF hierarchy (use the 355
   `App::Part` groups for naming), then compare its frame bbox against 460×460×480 and replace
   the nominal proxy meshes module by module.
2. Replace the procedural toolhead/frame with selected real meshes at the verified joints.
3. Add 40–60% mid-print screenshot and a layer scrub control.
4. Deploy the backend with a proper PostgreSQL migration and auth.
