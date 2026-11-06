# PrintVerse G-code Test Report

## 1. Profile basis

Resolved from OrcaSlicer 2.4.2's bundled official Voron vendor profiles:

| Profile | File | Source |
|---|---|---|
| Machine | `configs/machine/voron-v2.4r2-300-0.4.json` | `Voron 2.4 300 0.4 nozzle` |
| Process | `configs/process/voron-0.20mm-standard.json` | `0.20mm Standard @Voron` |
| Filament | `configs/filament/generic-pla.json` | `Generic PLA @System` |

Resolution is performed by `scripts/build_orca_profiles.py`, which walks the official
`inherits` chain. The profiles are **UNVERIFIED_AGAINST_PHYSICAL_MACHINE**: they are vendor
defaults, not measurements of this or any real Voron. The Orca machine profile declares a
275 mm printable height; the configurator derives 280 mm. That discrepancy is retained, not
silently normalized.

## 2. Test model

`assets/test-models/cube.stl`: 20 × 20 × 20 mm, 12 triangles, 8 unique vertices, watertight,
volume 8,000 mm³.

## 3. Slice command

```powershell
& tools\OrcaSlicer-2.4.2\orca-slicer.exe assets\test-models\cube.stl `
  --load-settings "configs\process\voron-0.20mm-standard.json;configs\machine\voron-v2.4r2-300-0.4.json" `
  --load-filaments configs\filament\generic-pla.json `
  --slice 0 --outputdir assets\test-models --export-3mf "cube.3mf" `
  --datadir .cache\orca-data --logfile logs\orca-slice2.log --debug 3
```

Exit code **0**. Outputs:

| File | Bytes | Meaning |
|---|---:|---|
| `assets/test-models/plate_1.gcode` | 301,690 | Orca default plate filename |
| `assets/test-models/cube.gcode` | 301,690 | canonical copy |
| `assets/test-models/cube.3mf` | 50,039 | project + G-code |
| `logs/orca-slice2.log` | — | slice log |

First attempt used an absolute `--export-3mf` path. Slicing succeeded, but Orca joined the
absolute path to `--outputdir`, producing an invalid doubled path, failed thumbnail rendering
because no OpenGL context exists in CLI mode, and exited **-13**. This is an Orca CLI quirk,
not a slicing failure; the rerun with a bare filename exited 0.

## 4. Slicer result

| Metric | Value |
|---|---|
| Layers | 100 |
| G-code lines | 11,938 |
| Max Z | 20.00 mm |
| Filament diameter / density | 1.75 mm / 1.24 g/cm³ |
| Filament used | 1,333.89 mm = 3.21 cm³ = **3.98 g** |
| Slicer time (normal mode) | **19m 52s = 1,192 s** |
| Feature commands in file | G1 only (real cube has no G2/G3) |

## 5. Parser result

`scripts/parse_gcode.py` produced `docs/reports/gcode_parse.json`.

| Metric | Parser | Slicer | Delta |
|---|---:|---:|---:|
| Layers | 100 | 100 | 0 |
| Extrusion length | 1,333.886 mm | 1,333.89 mm | 0.004 mm |
| Filament volume | 3,208.372 mm³ | 3.21 cm³ (3,210 mm³) | ~0.05% |
| Filament mass | **3.978 g** | **3.98 g** | **0.05%** |
| Travel + path | 42,259.91 mm extrusion path | — | — |
| Retraction length | 1,005.0 mm | — | — |
| G1 moves | 8,630 | — | — |
| Slicer estimate | — | 1,192 s | — |
| Naive feedrate estimate | 408.4 s | — | ignores acceleration/jerk; not used for planning |

### Bounds

| Axis | G-code extrusion centerline | Expected model | Delta |
|---|---:|---:|---:|
| X | 19.6 mm | 20.0 mm | −0.4 mm |
| Y | 19.6 mm | 20.0 mm | −0.4 mm |
| Z | 19.8 mm (0.2 → 20.0) | 20.0 mm | −0.2 mm |

The −0.4 mm XY delta is exactly one 0.40 mm perimeter line width: the parser measures the
nozzle centerline, while the printed outer edge adds half a line width on each side. The Z
delta is the 0.2 mm first-layer centerline. The result is dimensionally consistent; the
`diameter_matches_model_within_1mm` flag is true.

## 6. G2/G3 coverage

The real cube contains no arcs. A synthetic test (`scripts/gcode_parser_test.py`) exercised:

- `G90` absolute XYZ
- `M83` relative extrusion
- `G2` and `G3` with I/J centers
- two layer markers

Result: 2 arcs recognized, 2 layers, 4.0 mm extrusion, 48.49 mm path. `docs/reports/gcode_parser_unit.json`.

## 7. Visualization library decision

| Candidate | Version | License | Result |
|---|---|---|---|
| `gcode-preview` | 2.18.0 | MIT | Mature Three.js preview; README supports `three >=0.166 <0.186`; our Three.js is 0.187 → **not installed** to avoid a broken peer |
| `gcode-parser` (cncjs) | 2.2.0 | MIT | Node-side parser; evaluated, not adopted |
| `gcode-toolpath` (cncjs) | 3.0.0 | MIT | Toolpath generator; evaluated, not adopted |
| Custom Python parser | local | project | Adopted for analysis and simulation data |

Recommended next step: pin Three.js 0.185 or isolate the G-code viewer package, then evaluate
`gcode-preview` against a 1M-segment toolpath. The current parser output is ready to feed a
custom `LineSegments` / `BufferGeometry` renderer without sending G-code text through an LLM.

## 8. Limitations

- No G2/G3 arcs in the real test object; synthetic coverage only.
- Naive time ignores acceleration, junction deviation and pressure advance.
- Orca's 275 mm printable height vs configurator 280 mm remains unresolved without a real machine.
- No physical print was performed, and no real printer was contacted.

## 9. Phase-2 animation toolpath

`scripts/gcode_to_toolpath.py` converts the same real G-code into the compact toolpath used by
the Three.js scene:

| Field | Value |
|---|---:|
| Layers | 100 |
| Moves | 7,853 |
| Types | Custom, Travel, Inner wall, Outer wall, Bottom surface, Internal solid infill, Sparse infill, Internal Bridge, Top surface |
| Mass | 3.9784 g |
| Bounds | 140.2–159.8 X, 140.2–159.8 Y, 0.2–20.0 Z |

Evidence: `docs/reports/toolpath_test.json`. The animation interpolates the toolhead along
these real moves, moves the bed by G-code Z, and advances deposited line geometry; it does not
use a preset loop.

## 10. Verdict

**COMPLETE** for test slicing, G-code generation, parsing, mass and dimensional consistency.
Profile calibration against a real Voron remains out of scope and is marked unverified.
