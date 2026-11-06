# PrintVerse Mechanical Parameter Table — Voron V2.4r2 300 mm

Date: 2026-11-06 · Scope: 300 mm spec, direct feed, blind joints, generic cable chains.
Status legend:

- **VERIFIED_OFFICIAL** — explicit value in an official repository/config, with a local path.
- **DERIVED** — deterministic result of the official configurator formulas.
- **VENDOR_SAFETY** — a slicer vendor value, not a mechanical CAD dimension.
- **COMMUNITY_UNVERIFIED** — community report; useful but not machine-verified.
- **PHYSICAL_PENDING** — cannot be confirmed without the real printer.

## 1. The 275 vs 280 conflict — resolved

These are **not two competing mechanical heights**:

| Value | What it actually is | Evidence | Status |
|---:|---|---|---|
| **280 mm** | Klipper Z travel / soft maximum for the 300 mm build | `Firmware/voron-official/klipper_configurations/Octopus/Voron2_Octopus_Config.cfg`, `[stepper_z]` section: `## Uncomment below for 300mm build` → `#position_max: 280` | **VERIFIED_OFFICIAL** |
| **280 mm** | Configurator build Z for the 300 mm spec | `assets/.../BOM/raw/configurator_2.4.js`: `build_z = frame_z - 200`; 300 spec → frame 480, build 280 | **DERIVED** |
| **275 mm** | OrcaSlicer `printable_height` for the Voron 2.4 300 profile | `configs/machine/voron-v2.4r2-300-0.4.json`, line 88 | **VENDOR_SAFETY** |

**Resolution used by PrintVerse:**

- **Mechanical/Z travel model:** 280 mm.
- **Slicer/printable ceiling:** 275 mm.
- **Effective clearance:** 5 mm reserved by the vendor profile.
- The 5 mm is **inferred from the difference** (280 − 275); the Orca profile does not
  document a rationale in the JSON. Treat it as a safety ceiling, not a CAD-derived travel.
- This is **not** a 300 mm Z machine. “300” is the X/Y spec; the 300-spec frame is
  460 × 460 × 480 mm and the Z travel is 280 mm.

The Voron forum has a community report that a Stealthburner/Tap toolhead can collide with the
front extrusions near `X=300` at `Z>265`, and that real usable height can be lower than the
nominal value. That is retained as **COMMUNITY_UNVERIFIED** and a reason to keep the 275 mm
slicer ceiling until a physical machine is measured.

Sources:

- Official Klipper config: `assets/source/voron-v2.4r2-300/Firmware/voron-official/klipper_configurations/Octopus/Voron2_Octopus_Config.cfg`
- Orca profile: `configs/machine/voron-v2.4r2-300-0.4.json`
- Configurator: `assets/source/voron-v2.4r2-300/BOM/raw/configurator_2.4.js`
- Community thread: <https://forum.vorondesign.com/threads/real-300mm-in-z-axis-with-direct-extruder.1009/>

## 2. Unified parameter table

| Parameter | Value | Unit | Source | Status | Used by |
|---|---:|---|---|---|---|
| Frame outer X | 460 | mm | Configurator `frame_x = build_x + 160`; BOM 420 + 2×20 extrusions | **DERIVED** | Machine scene |
| Frame outer Y | 460 | mm | Configurator `frame_y = build_y + 160` | **DERIVED** | Machine scene |
| Frame outer Z | 480 | mm | Configurator `frame_z = build_z + 200`; BOM 480-LCP-RCP ×4 | **DERIVED** | Machine scene |
| Build X travel | 300 | mm | Klipper X/Y 300 setting; Orca `printable_area` 0–300 | **VERIFIED_OFFICIAL** | G-code, UI |
| Build Y travel | 300 | mm | Klipper X/Y 300 setting; Orca `printable_area` 0–300 | **VERIFIED_OFFICIAL** | G-code, UI |
| Z mechanical travel | 280 | mm | Klipper `position_max: 280` (300 build) | **VERIFIED_OFFICIAL** | Z mechanism |
| Z slicer ceiling | 275 | mm | Orca `printable_height` | **VENDOR_SAFETY** | Slicer/job validation |
| Z minimum (Klipper) | −5 | mm | `[stepper_z] position_min: -5` | **VERIFIED_OFFICIAL** | Homing model only |
| Z endstop position | −0.5 | mm | `[stepper_z] position_endstop: -0.5` | **VERIFIED_OFFICIAL** | Homing model only |
| Z rail length | 350 | mm | BOM `Linear Rail MGN9H 350mm` ×6 (4 Z + 2 Y) | **DERIVED** | Scene rails |
| X rail length | 350 | mm | BOM `Linear Rail MGN12H 350mm` ×1 | **DERIVED** | X gantry |
| Y rail length | 350 | mm | BOM MGN9H 350 mm (shared with Z line count) | **DERIVED** | Gantry |
| X gantry extrusion | 380 | mm | BOM `HFSB5-2020-380` ×1 | **DERIVED** | Gantry |
| Y gantry extrusion | 400 | mm | BOM `HFSB5-2020-400` ×2 | **DERIVED** | Gantry |
| Frame extrusions | 420 | mm | BOM `HFSB5-2020-420-TPW` ×10 | **DERIVED** | Frame |
| Cross brace | 290 | mm | BOM `HFSB5-2020-290` ×1 | **DERIVED** | Rear brace |
| Z frame extrusion | 480 | mm | BOM `HFSB5-2020-480-LCP-RCP` ×4 | **DERIVED** | Frame |
| Bed plate | 305 × 305 × 7.76 | mm | Official `MIC6_Bed_V2_300.step` imported in FreeCAD | **VERIFIED_OFFICIAL** | Bed |
| Bed heater | 250 × 250 | mm | BOM `Keenovo ... 250x250mm (450W)` | **DERIVED/BOM** | Bed thermal model |
| Build plate nominal | 300 × 300 | mm | Configurator build X/Y; Orca printable area | **DERIVED** | Product limit |
| A/B open belt | 1800 | mm | BOM `LL-2GT-6 1800mm` ×2 | **DERIVED** | CoreXY animation |
| Z belt loop | 188 | mm | BOM `GT2 Belt Loop 188mm` ×4 | **DERIVED** | Z animation |
| Z gear ratio | 80:16 | — | Klipper `[stepper_z] gear_ratio: 80:16` | **VERIFIED_OFFICIAL** | Screw rotation |
| Z rotation distance | 40 | mm | Klipper `[stepper_z] rotation_distance: 40` | **VERIFIED_OFFICIAL** | Screw rotation |
| Z motor count | 4 | — | Four Z drives in CAD/BOM | **DERIVED** | Bed mechanism |
| A/B motor count | 2 | — | CoreXY A/B drives | **VERIFIED_OFFICIAL** | Gantry |
| Toolhead clearance | 275 nominal | mm | Orca ceiling; community conflict near top/front | **PHYSICAL_PENDING** | UI warning |

## 3. What is still NOT verified

1. **Actual nozzle-to-bed Z at the top of travel** on a physical 300 mm V2.4r2.
2. Whether 275 mm is sufficient for every toolhead/duct/cable-chain combination; the Voron
   forum reports collisions near the top/front with Stealthburner + Tap.
3. Bed mesh/quad gantry level offsets and the actual Z endstop trigger.
4. Heater actual area vs nominal 300 × 300 bed (BOM heater is 250 × 250).
5. Full CAD assembly transforms: the 267 MB STEP has 1,534 products and 1,662 solids, but a
   full FreeCAD import exceeded the bootstrap timeout. Scene hierarchy uses verified nominal
   dimensions and explicit kinematic relationships, not claimed exact STEP transforms.

## 4. Simulation policy

- Machine model: **460 × 460 × 480 mm frame**, **300 × 300 mm XY**, **280 mm Z travel**.
- Slicer admission: reject G-code with `Z > 275.0` unless the user explicitly overrides after
  a physical calibration.
- Print test: 20 × 20 × 20 mm cube, max Z 20 mm — no conflict with 275/280.
- UI must label 275 as the slicer ceiling and 280 as the mechanical travel; never present
  300 mm Z as a verified build height.
