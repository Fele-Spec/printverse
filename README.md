# PrintVerse

AI 3D design platform, Voron V2.4r2 300 mm digital twin, G-code-driven virtual printing,
3D collection / desktop-pet surface, and dual virtual/physical filament accounting.

> Bootstrap status: **PARTIAL** (see [PRINTVERSE_BOOTSTRAP_REPORT.md](PRINTVERSE_BOOTSTRAP_REPORT.md)).
> The official CAD/BOM/docs stack, FreeCAD/Blender/OrcaSlicer, Python/Node environments,
> six project Skills, a real Orca slice, a G-code parser, and the Three.js scene build are
> ready. The browser screenshot is blocked by the DSH sandbox's named-pipe restriction, and
> `build123d`/`cadquery` plus image-to-3D weights were not installed because of network
> throughput and the 8 GB GPU limit. Those are reported honestly, not hidden.

## What is already available

| Area | Evidence |
|---|---|
| Voron V2.4r2 official design | `assets/source/voron-v2.4r2-300/` — 185 STL, assembly STEP, DXF, F3D, manuals |
| 300 mm BOM | `BOM_300MM.csv` / `.html` / `.pdf` — 120 line items replayed from the official configurator |
| Official docs | `docs/official-docs/INDEX.md` — Voron, Klipper, Moonraker |
| Slicer profiles | `configs/machine/`, `configs/process/`, `configs/filament/` |
| Test slice | `assets/test-models/cube.gcode`, `cube.3mf` — 100 layers, 3.98 g PLA |
| G-code parser | `scripts/parse_gcode.py` + `docs/reports/gcode_parse.json` |
| Frontend | `frontend/` — React 19 + Three.js + R3F + Drei, built GLB scene |
| Skills | `.dsh/skills/` — six PrintVerse skills recognized by the Harness |
| Indexes | `CAD_ASSET_INDEX.csv`, `LICENSE_AUDIT.csv`, `manifests/`, `SHA256SUMS.txt` |

## Quick start

```powershell
# 1. Serve the built frontend (already installed)
npm run preview --prefix frontend
# open http://127.0.0.1:4173/

# 2. Inspect a parsed slice
.\.venv\Scripts\python.exe scripts\parse_gcode.py assets\test-models\cube.gcode `
  --out docs\reports\gcode_parse.json --expected-size 20,20,20

# 3. Re-run the whole reproducible bootstrap
.\bootstrap.ps1
```

## Tool locations

- FreeCAD 1.1.4: `tools/FreeCAD-1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311/`
- Blender 4.5.12 LTS: `tools/Blender-4.5.12/blender.exe`
- OrcaSlicer 2.4.2: `tools/OrcaSlicer-2.4.2/orca-slicer.exe`
- Python 3.12 venv: `.venv/`
- Node 24.16 / npm 11.13; frontend deps in `frontend/node_modules/`

## Safety boundary

This bootstrap never connected to a real printer, never heated anything, never flashed
firmware, never exposed Moonraker, and never processed a payment. Moonraker work is
documentation and read-only design only. The browser screenshot limitation is an
environment restriction, not a product decision.

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
