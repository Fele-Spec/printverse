# PrintVerse Bootstrap Report

Date: 2026-11-06 (Asia/Shanghai) · Root: `C:\Users\someb\Desktop\printverse`
Overall status: **PARTIAL** — the engineering foundation is usable, but three environmental
limits are reported openly rather than disguised as success.

## 1. Completion criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| A | Official Voron V2.4r2 engineering data acquired | **COMPLETE** | 342 MB tag archive, 185 STL, 267 MB assembly STEP, DXF, F3D, manuals; no LFS pointers |
| B | 300 mm BOM generated or blocked reason | **COMPLETE** | 120 line items replayed from official configurator JS; `BOM_300MM.csv/.html/.pdf` |
| C | Required software installed or verified fallback | **PARTIAL** | FreeCAD, Blender + Print3D, OrcaSlicer, Python, Node installed and exercised; `build123d`/`cadquery` not installed because PyPI throughput was ~50 KB/s; FreeCAD/OCP is the working CAD fallback |
| D | Project Skills loaded | **COMPLETE** | six skills in catalog and loadable; `SKILL_AUDIT.md` |
| E | FreeCAD imports test CAD | **COMPLETE** | STL 60×34×2 mm and STEP bed 305×305×7.76 mm imported; full assembly import PARTIAL |
| F | OrcaSlicer completes a test slice | **COMPLETE** | 20 mm cube, 100 layers, exit 0, G-code + 3MF |
| G | G-code parsed successfully | **COMPLETE** | 100 layers, 3.978 g vs 3.98 g slicer, bounds consistent |
| H | Three.js test scene actually runs | **PARTIAL** | production build + Vite HTTP 200 + real Three.js `GLTFLoader` scene graph; pixel screenshot blocked by sandbox named pipes |
| I | Source and license recorded | **COMPLETE** | `OFFICIAL_RESOURCES.md`, `LICENSE_AUDIT.csv`, 3,400+ file checksum manifest |
| J | All reports generated | **COMPLETE** | ten required deliverables plus manifests |

The honest overall verdict is **PARTIAL**, not COMPLETE.

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

The page screenshot is **BLOCKED** by the same browser limitation as H. The HTML snapshot is
generated from the result; `assets/previews/BOM_300MM_page1.png` is a generated table preview,
not a browser screenshot.

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
| Python venv | 3.12.10 + 61 locked packages | trimesh/meshio/FastAPI imports pass |
| Three.js | 0.187.0 | GLB parsed: 1 mesh, 802 triangles, 60×34×2 mm |
| Frontend | React 19.3 + R3F 9.8 + Drei 10.7 | `vite build` pass; preview HTTP 200 |

## 5. What is blocked, and why

### 5.1 Browser screenshot / WebGL render — BLOCKED

The frontend builds and is served at `http://127.0.0.1:4173/`. Headless Edge/Chromium cannot
start under this DSH sandbox: it fails at
`mojo\public\cpp\platform\platform_channel.cc: Check failed: ... 拒绝访问` because the sandbox
denies the named-pipe IPC Chrome requires. The ACL diagnostic classified the cache path
`NOT_THIS_CLASS` and made no changes. Playwright launch fails with `spawn EPERM`.

Therefore: **build PASS, HTTP preview PASS, Three.js GLTFLoader PASS, rendered screenshot
BLOCKED**. No screenshot is fabricated. Running the same scene outside this sandbox (or in a
full-access session) is the next verification step.

### 5.2 build123d / cadquery — NOT INSTALLED

PyPI downloads averaged roughly 50 KB/s (numpy 12 MB took 4m21s). The OCP wheel needed by
build123d/cadquery is hundreds of MB. Installing it would consume a disproportionate share of
the bootstrap window. FreeCAD 1.1.4 is installed and successfully imports STEP/STL, so CAD work
is not unblocked, only the optional Python-native modelling API is missing. This is a
**PARTIAL**, not a hidden success.

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

Open `NEXT_DEVELOPMENT_PLAN.md`. The smallest next verification is to run the existing frontend
and Playwright suite in a non-sandboxed session to capture the 1440×980 rendered screenshot,
then proceed to STEP→glTF conversion and toolpath streaming.
