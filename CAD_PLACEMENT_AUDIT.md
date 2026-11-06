# CAD Placement Audit

Source: `.cache/voron_full.FCStd`, derived from `assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step`.

## Counts

| Metric | Value |
|---|---:|
| Document objects | 4881 |
| Placements (non-Origin) | **4526** |
| Part::Feature solids | **1686** |
| App::Part assembly nodes | 355 |
| Construction Line/Plane/Point | 2485 |
| Duplicate part IDs | 0 |
| Zero-volume solids | 1 |
| Unit / glTF unit / scale | mm / m / 0.001 |

## Transform rule

`obj.Shape` already includes the object's own `Placement`. The correct world shape is therefore
`obj.Shape * parent.getGlobalPlacement()`; applying `obj.getGlobalPlacement()` again would double-apply
the object placement. This was verified on `B Drive Frame Upper`: shape bbox -133.895..-17.895 X,
parent transform gives -78.0..38.0 X, inside the nominal frame; the erroneous global transform gave
-406.05..-349.02 X.

## Envelope and issues

Finite solid union: `[-88.0, -49.0, -143.1]` → `[342.0, 485.45, 378.9]` mm (size `[430.0, 534.45, 522.0]`).
This includes cable chains, spool/exhaust and outliers; it is not used as the frame envelope.
Duplicate exact placements by (name, rounded world translation, volume): **0**.
Zero-volume solid: `['F0490']` — an inverted/open compound, retained in metadata but excluded from the physical mesh where meshing fails.

## 20 sampled dimensions vs FreeCAD bbox

| # | Part | Module | Dimensions mm | FreeCAD bbox mm | Max diff |
|---:|---|---|---|---:|---:|
| 1 | M5x16 BHCS (1) | FRAME | [9.567, 19.3101, 9.5068] | [9.567, 9.5068, 19.3101] | 0.0 |
| 2 | 2020 Drop-in T-nut, M5 (19) | FRAME | [4.3, 13.0, 7.7] | [4.3, 7.7, 13.0] | 0.0 |
| 3 | Panel | FRAME | [369.1999, 369.2, 3.0] | [369.1999, 369.2, 3.0] | 0.0 |
| 4 | B Drive Frame Upper | XY_GANTRY | [116.0, 57.0274, 16.0] | [116.0, 57.0274, 16.0] | 0.0 |
| 5 | GT2 20T 6mm | XY_GANTRY | [16.0, 16.0, 16.0] | [16.0, 16.0, 16.0] | 0.0 |
| 6 | GT2 20T Idler (1) | XY_GANTRY | [18.0, 18.0, 8.6] | [18.0, 18.0, 8.6] | 0.0 |
| 7 | Z Motor Mount | Z_DRIVE | [42.5563, 30.9472, 51.2472] | [51.2472, 42.5563, 30.9472] | 0.0 |
| 8 | GT2 20T Idler 9mm (3) | Z_DRIVE | [18.0, 13.0, 18.0] | [13.0, 18.0, 18.0] | 0.0 |
| 9 | NEMA17 Stepper | Z_DRIVE | [42.8381, 49.0, 42.6601] | [42.6602, 42.8381, 49.0] | 0.0001 |
| 10 | x_carriage_frame_left | TOOLHEAD | [21.8416, 32.4, 68.7521] | [32.4, 21.8416, 68.7522] | 0.0001 |
| 11 | x_carriage_frame_right | TOOLHEAD | [22.4729, 32.5657, 68.9993] | [32.5657, 22.4729, 68.9993] | 0.0 |
| 12 | Hotend Fan Mount | TOOLHEAD | [60.5802, 15.265, 66.3925] | [15.265, 60.5803, 66.3925] | 0.0001 |
| 13 | 4020 Blower Fan | TOOLHEAD | [41.8, 10.8, 41.2193] | [10.8, 41.8, 41.2193] | 0.0 |
| 14 | Dragon Body Rear | TOOLHEAD | [47.7331, 14.98, 53.6278] | [47.7332, 14.98, 53.6278] | 0.0001 |
| 15 | Bed heater | BUILD_PLATFORM | [200.0, 235.0, 3.5] | [235.0, 200.0, 3.5] | 0.0 |
| 16 | 10in MIC6 Plate | BUILD_PLATFORM | [254.0, 254.0, 7.76] | [254.0, 254.0, 7.76] | 0.0 |
| 17 | bottom_panel_hinge_x2 (1) | ENCLOSURE | [23.2, 14.4064, 7.1263] | [23.2, 14.4064, 7.1262] | 0.0001 |
| 18 | RS-25 PSU Bracket (1) | ELECTRONICS | [10.0, 67.0, 19.6] | [10.0, 19.6, 67.0] | 0.0 |
| 19 | DIN Clips | ELECTRONICS | [8.0, 62.0, 16.6] | [8.0, 62.0, 16.6] | 0.0 |
| 20 | Cable Cover | WIRING | [82.5673, 45.1481, 35.2929] | [45.1481, 82.5673, 35.2929] | 0.0 |

The comparison uses sorted axis extents because parent rotations permute X/Y/Z. The 20 samples
match the saved FreeCAD object bbox extents. This is an internal consistency check, not an
independent physical measurement.

Machine-readable: `docs/reports/placement_samples.json`; hierarchy: `ASSEMBLY_HIERARCHY.json`.
