# Height Clearance Analysis

Status: **CAD_ANALYSIS_COMPLETE / PHYSICAL_CLEARANCE_PENDING**

## 1. Values

| Field | Value | Status |
|---|---:|---|
| `max_printable_z_mm` | **275** | Orca vendor safety ceiling |
| `max_klipper_travel_z_mm` | **280** | Klipper 300-build `position_max` |
| `verified_physical_z_clearance_mm` | **null** | Not measured on a physical machine |
| Difference | **5 mm** | Inferred safety margin, not a CAD dimension |

## 2. CAD evidence

From the eight exported module GLBs (metres before the scene's ×1000 mm conversion):

| Module | Z min | Z max |
|---|---:|---:|
| FRAME | -0.058 m | 0.379 m |
| ENCLOSURE | -0.129 m | 0.379 m |
| XY_GANTRY | -0.035 m | 0.265 m |
| Z_DRIVE | -0.143 m | 0.372 m |
| TOOLHEAD | 0.028 m | 0.157 m |
| BUILD_PLATFORM | -0.021 m | 0.000 m |
| WIRING | 0.141 m | 0.374 m |

Nominal CAD relation: the enclosure/frame top is 379 mm above the bed datum, the toolhead upper
envelope is 157 mm, leaving **222 mm** between the toolhead top and the frame top in this
assembly pose. This is a static CAD distance, not a guarantee of safe nozzle/duct/cable travel.

## 3. Z motion model

- Voron V2.4 uses a moving bed; the CoreXY gantry/toolhead Z is fixed.
- 275 mm is used as the conservative slicer-visible print height.
- 280 mm is the Klipper travel reference from the official 300 mm configuration.
- At a 275 mm part, the bed moves down; the part top can approach the fixed toolhead envelope.
- The CAD assembly's Z coordinates place the bed top near 0 and the frame bottom at −58 mm;
  converting that assembly frame to a physical floor requires a real machine reference and is
  therefore not asserted here.

## 4. Collision risk

| Risk | Finding | Status |
|---|---|---|
| Toolhead vs top frame | 222 mm static CAD gap | CAD_CHECKED |
| Cable chain vs frame/top | WIRING envelope z = 141–374 mm; no dynamic sweep in CAD | **UNVERIFIED** |
| Toolhead/duct vs part at 275 mm | Requires real Z datum and physical endstop | **UNVERIFIED** |
| Bed/part vs lower frame | CAD coordinates need physical normalization | **UNVERIFIED** |
| 300 mm Z claim | False; 300 is X/Y | **REJECTED** |

## 5. Required physical checks (do not skip)

1. Home Z and measure nozzle-to-bed at the top of travel.
2. Measure the full toolhead/cable-chain envelope while moving X/Y at max Z.
3. Verify the real endstop and `position_max` after any config change.
4. Update `verified_physical_z_clearance_mm` only with a measured value and method.

No real printer was connected, heated, homed, or moved for this report.
