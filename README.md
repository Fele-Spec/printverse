# PrintVerse

AI 3D design platform, Voron V2.4r2 300 mm digital twin, G-code-driven virtual printing,
3D collection / desktop-pet surface, and dual virtual/physical filament accounting.

> Phase 2 functional acceptance: **COMPLETE** — upload→Orca slice→G-code animation→detach→collect
> passes end to end ([PHASE2_REPORT.md](PHASE2_REPORT.md)).
>
> Phase 3: **PARTIAL** — 4,526 FreeCAD placements, eight real module GLBs (1,686 parts), real
> CAD default view with part picking, module modes, transparency, explode and studio lighting;
> the real CAD toolhead and platform follow the G-code (XY crossbeam static), and InstancedMesh
> fasteners are implemented as an optional layer. See [PHASE3_COMPLETION_REPORT.md](PHASE3_COMPLETION_REPORT.md).
>
> Phase 4 Image-to-3D: **COMPLETE (architecture)** — provider architecture, free Mock relief,
> TripoSR CPU, explicit cost authorization, frontend studio and 10-image benchmark are runnable.
> Kimi account and TokenHub are external gates.
>
> Phase 5 full-product correction: **COMPLETE（12/12 验收）** — colour GLB primary, local three-view
> visual hull, STEP/3MF/OBJ/GLB import, Chinese UI, browser desktop pet and colour finished
> object are implemented; PostgreSQL adapter is locally verified. Docker Compose is verified in WSL2; Tauri release exe + NSIS + desktop shortcut are built; engineering-drawing-to-CAD and exact wall/support analysis remain
> unfinished. See [PHASE5_REPORT.md](PHASE5_REPORT.md).
>
> Bootstrap status: **COMPLETE (A–J)** — see [PRINTVERSE_BOOTSTRAP_REPORT.md](PRINTVERSE_BOOTSTRAP_REPORT.md).
> Official CAD/BOM/docs, FreeCAD/Blender/OrcaSlicer, Python 3.12 + build123d/OCP, Node/Three.js,
> six project Skills, a real Orca slice, a parsed G-code file, and real headless-Edge WebGL
> screenshots are ready. The optional local image-to-3D path is implemented (TripoSR CPU /
> visual hull / Mock); Hunyuan3D/TRELLIS remain blocked by the 8 GB GPU.
> Kimi is additionally blocked by account balance (HTTP 429), documented rather than hidden.

## What is already available

| Area | Evidence |
|---|---|
| Voron V2.4r2 official design | `assets/source/voron-v2.4r2-300/` — 185 STL, assembly STEP, DXF, F3D, manuals |
| 300 mm BOM | `BOM_300MM.csv` / `.html` / `.pdf` — 120 line items replayed from the official configurator |
| Official docs | `docs/official-docs/INDEX.md` — Voron, Klipper, Moonraker |
| Slicer profiles | `configs/machine/`, `configs/process/`, `configs/filament/` |
| Test slice | `assets/test-models/cube.gcode`, `cube.3mf` — 100 layers, 3.98 g PLA |
| G-code parser | `scripts/parse_gcode.py` + `docs/reports/gcode_parse.json` |
| Frontend | `frontend/` — React 19 + Three.js + R3F + Drei; real WebGL screenshots in `assets/previews/phase2_scene_*.png` |
| Phase-2 loop | upload → Orca slice → parser → CoreXY/Z animation → detach → collect; `PHASE2_REPORT.md` |
| Phase-3 CAD twin | 8 module GLBs, 1,686 parts, part picker, views, transparency, explode; `PHASE3_COMPLETION_REPORT.md` |
| Skills | `.dsh/skills/` — six PrintVerse skills recognized by the Harness |
| Indexes | `CAD_ASSET_INDEX.csv`, `LICENSE_AUDIT.csv`, `manifests/`, `SHA256SUMS.txt` |

## Quick start (phase 2)

```powershell
# terminal 1: virtual ledger / upload / Orca slicing API
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# terminal 2: Vite UI
npm run dev --prefix frontend
# open http://127.0.0.1:4173/

# upload an STL, watch the real G-code animation, detach, add to collection
# top-right IMAGE → 3D opens the provider studio (free Mock provider works without keys)
```

桌面宠物：`http://127.0.0.1:4173/?pet=1`（浏览器透明视图）；Tauri 壳在 `desktop/`。

图片 → 彩色 3D：右上角 **图片 → 3D**；多视角请选 **正面/侧面/顶面 3 张**；工程图可选“工程图拉伸”并填写宽度/厚度；生成后点击 **用于虚拟打印**，完成打印后 **放到桌面**。

The built UI is `frontend/dist/`; do not double-click `index.html` — serve it with
`npm run preview --prefix frontend` or `npm run dev --prefix frontend`.
Architecture correction: [PRODUCT_ARCHITECTURE.md](PRODUCT_ARCHITECTURE.md) · [PHASE5_AUDIT.md](PHASE5_AUDIT.md) · [DEPLOYMENT.md](DEPLOYMENT.md).

Sharing is available as the opt-in `PRINTVERSE_SHARE_MODE=1` (owner loopback/admin unlimited,
remote guest 20 g quota); see [SHARING_AND_QUOTA.md](SHARING_AND_QUOTA.md). It is not password
authentication, so use a trusted LAN/Tailscale/Cloudflare setup and do not expose uvicorn directly.

The uploaded STL is sliced by the local OrcaSlicer 2.4.2 with the resolved Voron 300 profiles.
The browser test can also use the built bundle:

```powershell
npm run build --prefix frontend
npm run preview --prefix frontend
node scripts\phase2_e2e.mjs
```

Phase-2 report and evidence: [PHASE2_REPORT.md](PHASE2_REPORT.md),
[docs/reports/phase2_e2e.json](docs/reports/phase2_e2e.json).

## Tool locations

- FreeCAD 1.1.4: `tools/FreeCAD-1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311/`
- Blender 4.5.12 LTS: `tools/Blender-4.5.12/blender.exe`
- OrcaSlicer 2.4.2: `tools/OrcaSlicer-2.4.2/orca-slicer.exe`
- Python 3.12 venv: `.venv/` (build123d 0.13.0, OCP 8.0.1.1.0, trimesh 5.2.0)
- Isolated CadQuery venv: `.venv-cadquery/` (CadQuery 2.8.0, OCP 7.9.3.1)
- Node 24.16 / npm 11.13; frontend deps in `frontend/node_modules/`

## Safety boundary

This bootstrap never connected to a real printer, never heated anything, never flashed
firmware, never exposed Moonraker, and never processed a payment. Moonraker work is
documentation and read-only design only. Chromium needs an approved full-access or
non-sandboxed session to start because the default sandbox blocks its named-pipe IPC; the
captured WebGL screenshots are real results from that approved run, not mockups.

## Repository map

```text
assets/source/       immutable official downloads and extracted official tree
assets/processed/    derived GLB/preview models
assets/previews/     generated screenshots/table previews
configs/             resolved Orca machine / process / filament profiles
docs/official-docs/  mirrored official Markdown + generated HTML
docs/reports/        machine-readable test evidence
manifests/           resources, licenses, checksums, dependencies
scripts/             reproducible acquisition, validation, slicing and reporting
frontend/            React + Three.js test scene
.dsh/skills/         six PrintVerse Agent Skills
```

## License note

The Voron CAD and documentation are GPL-3.0; OrcaSlicer is AGPL-3.0; Klipper and Moonraker
are GPL-3.0. Commercial distribution and networked use require a license review. See
[LICENSE_AUDIT.csv](LICENSE_AUDIT.csv); no license was assumed for unclear assets.
