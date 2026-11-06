# PrintVerse Bootstrap Report

Date: 2026-11-06 (Asia/Shanghai) · Root: `C:\Users\someb\Desktop\printverse`
Overall status: **COMPLETE (A–J)** — all ten completion criteria pass. One optional
hardware-gated capability, local image-to-3D, remains BLOCKED on this 8 GB GPU and is reported
separately rather than disguised as a completed test.

## 1. Completion criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| A | Official Voron V2.4r2 engineering data acquired | **COMPLETE** | 342 MB tag archive, 185 STL, 267 MB assembly STEP, DXF, F3D, manuals; no LFS pointers |
| B | 300 mm BOM generated or blocked reason | **COMPLETE** | 120 line items replayed from official configurator JS; `BOM_300MM.csv/.html/.pdf` |
| C | Required software installed or verified fallback | **COMPLETE** | FreeCAD, Blender + Print3D, OrcaSlicer, Python 3.12 + `build123d` 0.13.0/OCP 8.0.1.1.0, Node installed and exercised; `cadquery` 2.8 requires OCP <8.0 and is incompatible with build123d's OCP 8.0, so it is evaluated and deferred to a separate venv |
| D | Project Skills loaded | **COMPLETE** | six skills in catalog and loadable; `SKILL_AUDIT.md` |
| E | FreeCAD imports test CAD | **COMPLETE** | STL 60×34×2 mm and STEP bed 305×305×7.76 mm imported; full assembly import PARTIAL |
| F | OrcaSlicer completes a test slice | **COMPLETE** | 20 mm cube, 100 layers, exit 0, G-code + 3MF |
| G | G-code parsed successfully | **COMPLETE** | 100 layers, 3.978 g vs 3.98 g slicer, bounds consistent |
| H | Three.js test scene actually runs | **COMPLETE** | real headless Edge WebGL 2.0 render, 1440×898 canvas, 802 triangles, three screenshots, background toggle, 0 console errors/404 |
| I | Source and license recorded | **COMPLETE** | `OFFICIAL_RESOURCES.md`, `LICENSE_AUDIT.csv`, 3,400+ file checksum manifest |
| J | All reports generated | **COMPLETE** | ten required deliverables plus manifests |

All A–J criteria now pass. The single BLOCKED item is optional local image-to-3D, which cannot
run on 8 GB VRAM; it is not counted as a completed test.

## 2. Environment

| Item | Result |
|---|---|
| OS | Windows NT 10.0.26200, AMD64 |
| CPU | AMD Family 25 Model 97, 32 logical processors |
| RAM | total not readable (WMI/CIM denied); 15,279 MB available |
| GPU | RTX 5060 Laptop, 8,151 MiB VRAM, driver 592.82 |
| Disk | 215.6 GB total, ~48 GB free at final audit |
| Admin | No |
| Python | 3.12.10 venv; 3.10 / 3.13 system |
| Node / npm | 24.16.0 / 11.13.0 |
| Git / uv | 2.54.0 / 0.11.28 |
| Network | Node HTTPS works; Windows schannel / Git / curl fail; GitHub API intermittent |

No administrator rights were requested. No system security setting was changed. No bootloader,
firmware, printer or payment system was touched.

## 3. Acquired engineering data

### Voron V2.4r2

- Tag `V2.4r2`, commit `45128487e8e8e4aa113bb2cbfdf5bf6752d242d3`.
- Archive SHA256 `e7891703…`; 342,066,710 bytes.
- 185 STLs, 12 DXFs, 3 bed STEPs, one 267 MB assembly STEP, one F3D assembly, two manuals.
- Full official directory hierarchy retained; category copies preserve names.
- No Git LFS pointer files were found.
- 185/185 STLs load; 179 are watertight; 6 official parts are not watertight (listed in
  `CAD_VALIDATION_REPORT.md`). No source file was modified.

### 300 mm BOM

The official configurator is a static page whose JS builds the BOM. `scripts/generate_bom.mjs`
executes the published `bom_2.4.js` + `configurator_2.4.js` in a VM with the exact selection:
V2.4 / 300 / New Build / Direct Feed / Blind Joints / Generic Cable Chains. Result: 120 line
items, total quantity 1,244, build volume 300×300×280 mm, frame 460×460×480 mm.

A real headless-Edge screenshot of the generated BOM page is saved at
`assets/previews/BOM_300MM_browser.png` (browser result: 120 rows, 0 console errors). The
official configurator UI itself was not visually automated; its raw HTML/JS is archived under
`assets/source/voron-v2.4r2-300/BOM/raw/` and its BOM logic was replayed exactly.
`assets/previews/BOM_300MM_page1.png` is an additional generated table preview.

### Docs / firmware

- 25 official documents mirrored as Markdown + generated HTML: `docs/official-docs/INDEX.md`.
- Klipper v0.13.0 and Moonraker v0.11.0 source + docs.
- Voron assembly manuals in PDF.
- No real Moonraker instance was contacted.

## 4. Software and tests

| Component | Version | Test |
|---|---|---|
| FreeCAD | 1.1.4 | STL and STEP imported through `FreeCADCmd` |
| Blender | 4.5.12 LTS | STL imported, GLB exported, mesh 60×34×2 |
| 3D Print Toolbox | 1.5.0 | addon enabled; `print3d_check_all` returned `{'FINISHED'}` |
| OrcaSlicer | 2.4.2 | cube sliced, 100 layers, 3MF written |
| Python venv | 3.12.10 + 100 locked packages | trimesh/meshio/FastAPI and build123d Box→STEP pass |
| Three.js | 0.187.0 | GLB parsed: 1 mesh, 802 triangles, 60×34×2 mm |
| Frontend | React 19.3 + R3F 9.8 + Drei 10.7 | `vite build` pass; preview HTTP 200 |

## 5. Remaining limits and one blocked optional capability

### 5.1 Browser screenshot / WebGL render — COMPLETE

The default workspace sandbox cannot launch Chromium: it fails at
`mojo\public\cpp\platform\platform_channel.cc: Check failed: ... 拒绝访问` because the sandbox
denies the named-pipe IPC Chrome requires (Playwright: `spawn EPERM`). The ACL diagnostic
classified the cache path `NOT_THIS_CLASS` and made no changes.

After an approved one-shot full-access run, the real test completed:

| Result | Value |
|---|---|
| Browser | system Microsoft Edge, headless, SwiftShader |
| WebGL | WebGL 2.0 (OpenGL ES 3.0 Chromium), ANGLE SwiftShader |
| Canvas | 1440 × 898 |
| Object | `Filament_Card`, 1 mesh, 802 triangles, 60 × 34 × 2 mm |
| Interactions | drag-orbit and wheel zoom changed the view; light background active |
| Console errors / 404 | 0 / 0 |
| Screenshots | `threejs_scene.png`, `threejs_orbited.png`, `threejs_light.png` |
| Machine evidence | `docs/reports/threejs_smoke.json` |

This is an actual rendered result, not a fabricated screenshot. The only environment caveat is
that Chromium still needs full access or a non-sandboxed session to start; the workspace default
cannot run it.

### 5.2 build123d — installed; cadquery — evaluated, not installed

The `cadquery-ocp-novtk` wheel is 47.7 MB, not the multi-hundred-MB package initially assumed.
It was fetched through Node, SHA256-verified, and installed; `build123d` 0.13.0 + OCP 8.0.1.1.0
then installed successfully.

Test: `Box(10, 20, 30)` → volume 6,000 mm³, bounding box 10 × 20 × 30, exported
`assets/processed/build123d_test.step` (15,430 bytes). **COMPLETE.**

`cadquery` 2.8.0 requires `cadquery-ocp>=7.9.3.1,<8.0`, which conflicts with build123d's OCP
8.0. It is not installed into the main venv; a separate venv is the correct route if CadQuery's
API is needed.

### 5.3 Image-to-3D — PARTIAL / BLOCKED BY HARDWARE

- Hunyuan3D 2.1: ~10 GB VRAM for shape, 21 GB texture, 29 GB combined. Host has 8 GB → **BLOCKED**.
- TRELLIS: requires at least 16 GB → **BLOCKED**.
- TripoSR: ~6 GB VRAM, MIT, active; a viable candidate on 8 GB, but CUDA PyTorch and weights
  were not downloaded. **PARTIAL**.

No account, API key, paid API or license agreement was accepted on the user's behalf. Details:
`docs/research/IMAGE_TO_3D.md`.

## 6. Safety boundary

- No real printer connection, no heating, no motion command, no firmware flash, no print job.
- Moonraker is documentation-only; no endpoint was called.
- No public exposure of any service.
- No real payment, card data or payment credential.
- No license/login/access-control bypass.
- Original official files were never edited; derived files live in `assets/processed/` or
  `docs/`.

## 7. Cost

No external paid API, cloud GPU or payment call was made. Token counts and RMB spend are not
exposed through the available tool surface, so no token/cost figure is invented here. See
`docs/reports/COST_REPORT.md`. The RMB 100 cap and RMB 80 stop threshold remain in force.

## 8. Deliverables

Root:

- `PRINTVERSE_BOOTSTRAP_REPORT.md`
- `OFFICIAL_RESOURCES.md`
- `CAD_ASSET_INDEX.csv`
- `BOM_300MM.csv` / `.html` / `.pdf`
- `SKILL_AUDIT.md`
- `SOFTWARE_INVENTORY.md`
- `LICENSE_AUDIT.csv`
- `GCODE_TEST_REPORT.md`
- `CAD_VALIDATION_REPORT.md`
- `NEXT_DEVELOPMENT_PLAN.md`
- `manifest.json`, `SHA256SUMS.txt`

Supporting:

- `manifests/resources.json`, `resources.csv`, `licenses.csv`, `checksums.sha256`,
  `dependencies.json`, `source_versions.json`
- `requirements.lock`, `frontend/package-lock.json`
- `bootstrap.ps1` and `scripts/`
- `docs/official-docs/`, `docs/reports/`, `docs/research/`

## 9. Next action

Open `NEXT_DEVELOPMENT_PLAN.md`. The next engineering step is STEP→glTF conversion of the
267 MB assembly and a toolpath streaming renderer; the browser and CAD verification gaps are
closed. Local image-to-3D remains a separate hardware-gated experiment.
