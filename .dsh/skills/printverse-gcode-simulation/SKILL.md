---
name: printverse-gcode-simulation
description: Drive OrcaSlicer headlessly, parse the resulting G-code, and validate the motion/extrusion model used by the PrintVerse virtual printer. Use when slicing a test model, comparing G-code bounds to the source mesh, computing layer/material statistics, or preparing toolpath data for Three.js.
whenToUse: A task mentions slicing, G-code, toolpaths, layer preview, extrusion simulation, print time, or filament mass.
metadata:
  version: "0.1.0"
  owner: PrintVerse
  license: MIT
  requires: [OrcaSlicer, python, scripts/build_orca_profiles.py, scripts/parse_gcode.py]
---

# PrintVerse G-code Simulation

## Inputs

- Mesh at `assets/test-models/<name>.stl`
- Machine profile `configs/machine/voron-v2.4r2-300-0.4.json`
- Process profile `configs/process/voron-0.20mm-standard.json`
- Filament profile `configs/filament/generic-pla.json`

The flat profiles are resolved from OrcaSlicer 2.4.2's official Voron presets. They are
`UNVERIFIED_AGAINST_PHYSICAL_MACHINE`; do not present them as calibrated production values.

## Slice

```powershell
& tools\OrcaSlicer-2.4.2\orca-slicer.exe assets\test-models\cube.stl `
  --load-settings "configs\process\voron-0.20mm-standard.json;configs\machine\voron-v2.4r2-300-0.4.json" `
  --load-filaments configs\filament\generic-pla.json `
  --slice 0 --outputdir assets\test-models --export-3mf "cube.3mf" `
  --datadir .cache\orca-data --logfile logs\orca-slice.log
```

`--export-3mf` must be a bare filename. An absolute path is joined to `--outputdir` and the
export fails even though slicing succeeded. Thumbnail rendering may fail in headless mode;
this is non-fatal because no OpenGL context is available.

## Parse

```powershell
.\.venv\Scripts\python.exe scripts\parse_gcode.py assets\test-models\cube.gcode `
  --out docs\reports\gcode_parse.json --expected-size 20,20,20
```

The parser handles `G0/G1/G2/G3`, `G90/G91`, `M82/M83`, relative extrusion, layer markers,
feedrate, arc length, and header/footer metadata. It reports:

- command and layer counts
- motion versus extrusion bounds
- extrusion length, retraction length, volume, and mass from density
- path length and a naive feedrate time (never substitute for the slicer estimate)
- per-layer extrusion and feature types

## Validation

- G-code layer count equals the slicer header count.
- Parser mass is within 2% of `; filament used [g]`.
- G-code extrusion bounds differ from the model by at most one extrusion width per side
  (the path centerline does not include the outer half-width).
- At least one G2/G3 command is covered by a synthetic parser unit test when the real model
  has no arcs.
- The Three.js viewer consumes parsed segments, not the whole G-code string through the
  language model.

## Failure handling

| Symptom | Action |
|---|---|
| Orca exits -13 | inspect log; separate slice failure from 3MF thumbnail/export failure |
| G-code missing | check output filename `plate_1.gcode`; copy to the canonical name |
| mass mismatch | verify filament diameter/density and relative-E mode |
| bounds mismatch > 1 mm | suspect skirt/brim, wrong profile, or unit error |
| parser finds 0 layers | scan the whole file; Orca metadata is in the footer |

## Outputs

`docs/reports/GCODE_TEST_REPORT.md`, `gcode_parse.json`, `cube.gcode`, `cube.3mf`, and a
toolpath JSON suitable for the frontend.
