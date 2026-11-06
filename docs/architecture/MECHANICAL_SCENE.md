# PrintVerse Mechanical Scene — Voron V2.4r2 300 mm

## 1. Scene hierarchy

```text
VORON_V2_4R2_300 (world, millimetres, Z-up)
├── FRAME (static)
│   ├── 4 × 480 mm vertical 2020 extrusions
│   ├── 420 mm top/bottom X/Y beams
│   ├── 290 mm rear cross brace
│   └── transparent panels
├── CORE_XY_GANTRY
│   ├── two fixed Y rails at X = ±190 mm
│   ├── Y carriage / 380 mm gantry extrusion
│   ├── X rail (350 mm) and X carriage
│   └── 4 GT2 belt paths from A/B drives
├── TOOLHEAD
│   ├── X/Y follows G-code
│   ├── nozzle tip at the bed datum
│   └── after completion parked at Y = +185 mm
├── Z_AXIS
│   ├── four lead screws at X/Y = ±145 mm
│   ├── four Z motors
│   └── bed group moves along world Z
│       ├── 305 × 305 × 8 mm plate (nominal)
│       ├── 250 × 250 heater
│       └── PRINTED_OBJECT (bed-local coordinates)
└── ELECTRONICS_BAY (static)
```

The node names are mirrored in `manifests/machine-hierarchy.json`. XCAF recovered 1,690 real
product nodes and 9 top-level groups. A second FreeCAD import produced 4,526 objects and 2,977
non-identity placements, so object-level transforms exist; they are not yet serialized into the
Web scene. The Web scene is therefore a **kinematic proxy** with verified dimensions, not exact
STEP placement (see `CAD_VALIDATION_REPORT.md`).

## 2. Coordinate systems

| Domain | Origin | Axis convention |
|---|---|---|
| G-code / Klipper | front-left bed corner (0,0,0) | X right, Y back, Z up |
| Web machine | bed centre (0,0) | X right, Y back, Z up |
| Bed group | bed top at `worldZ = 300 − gcodeZ` | local Z = printed height above bed |
| Object | bed-local | bottom on bed, grows +Z locally |

Conversions:

```text
toolheadX = gcodeX − 150
toolheadY = gcodeY − 150
bedWorldZ = 300 − gcodeZ
objectWorldZ = bedWorldZ + localZ
```

At G-code Z=0 the bed top is at world 300 mm. At the cube's final Z=20 the bed top is 280 mm
and the object occupies world 280–300 mm. This models the real Voron moving-bed Z axis rather
than moving the gantry upward.

## 3. CoreXY mapping

For a standard CoreXY:

```text
A = X + Y
B = X − Y
```

The scene moves the Y carriage and X carriage directly from G-code X/Y, and draws the four
belt paths from the A/B motor positions to the gantry ends. Belt path lengths and motor
rotations are derived quantities; the current visual uses line geometry rather than a
toothed-belt mesh.

## 4. Z mechanics

- Four lead screws at the bed corners.
- Klipper gear ratio `80:16`; rotation distance `40 mm`.
- The bed group descends as Z increases; the nozzle datum remains fixed at world Z=300.
- The finished object is a separate world group after detach, initially at bed top, then
  movable with `TransformControls`.

## 5. G-code animation data

`scripts/gcode_to_toolpath.py` emits:

```text
moves[i] = [x0,y0,x1,y1,z,de,dt,typeIndex,isTravel,layer]
```

- `de > 0` with `isTravel=0` is deposited material.
- `PrintPaths` builds one `BufferGeometry` for extrusion segments and advances `drawRange`
  with the simulation time.
- Toolhead position is interpolated along the current real move; it is not a preset loop.
- Bed Z follows the move's layer Z.
- The animation timeline uses the per-move feedrate time; the slicer estimate (19m52s) is
  displayed separately. Viewer speed is a UI multiplier, not a claim about real print time.

## 6. Verified vs nominal

| Element | Basis |
|---|---|
| Frame 460×460×480 | Configurator + BOM extrusions |
| Build XY 300×300 | Klipper 300 + Orca printable area |
| Z travel 280 / slicer 275 | Klipper / Orca (see `MECHANICAL_PARAMETERS.md`) |
| Rails 350 mm, gantry 380/400, belts | BOM |
| Bed plate 305×305×7.76 | Official `MIC6_Bed_V2_300.step` |
| Toolhead shape | Simplified proxy; not claimed as exact CAD |
| Exact product transforms | Pending name-preserving XCAF import |

## 7. Files

- `frontend/src/components/VoronMachine.tsx` — frame, gantry, belts, Z axis, bed, toolhead
- `frontend/src/components/PrintPaths.tsx` — deposited G-code geometry
- `frontend/src/components/PrintSimulator.tsx` — time → move → toolhead/bed/deposition
- `frontend/src/components/FinishedObject.tsx` — final mesh + transform gizmo
- `frontend/src/components/PrintScene.tsx` — Z-up camera, orbit, scene composition
