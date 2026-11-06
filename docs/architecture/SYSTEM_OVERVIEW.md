# PrintVerse System Overview

## Layers

```text
Input (image / PDF drawing / STEP / STL / 3MF)
  -> ingestion + unit/format validation
  -> AI image-to-3D or CAD reconstruction
  -> mesh preflight (watertight, normals, scale)
  -> OrcaSlicer profile selection + slice
  -> G-code parse -> toolpath stream
  -> digital twin (Voron V2.4r2 300) motion + material growth
  -> collection / desktop pet
  -> filament ledger (virtual + physical)
  -> optional Moonraker read-only adapter (future, separately authorized)
```

## Service boundaries

| Boundary | Responsibility | Must not |
|---|---|---|
| `frontend` | Three.js scene, layer preview, user controls | trust unvalidated G-code or model metadata |
| `backend` | uploads, jobs, auth, quota, audit | process real payments in this phase |
| `database` | users, wallets, ledger, print jobs | allow negative available balance |
| `printer adapter` | read-only Moonraker snapshot | issue motion/heater commands by default |
| `scripts` | reproducible acquisition and validation | modify `assets/source/` originals |

## Digital twin model

- Machine frame 460 × 460 × 480 mm; build volume 300 × 300 × 280 mm from the configurator.
- Orca's vendor profile declares 275 mm printable height; unresolved, marked unverified.
- Motion: CoreXY A/B gantry, four-point Z, toolhead on MGN12 X rail.
- G-code drives nozzle position; extrusion width/volume drives material deposition.
- After completion the printed object becomes a detachable scene node for the collection.

## Data contracts

- `configs/machine/*.json`, `configs/process/*.json`, `configs/filament/*.json`: resolved
  Orca profiles, with provenance and unverified status in `configs/orca-profile-manifest.json`.
- `docs/reports/gcode_parse.json`: layers, bounds, extrusion, mass, time, per-layer totals.
- `docs/reports/mesh_audit.json`: topology and printability evidence.
- Ledger: integer milligrams; `operation_id` unique; reserve/commit/release.
- `PrinterSnapshot`: state, temperatures, position, job, progress, remaining time, errors.

## Security boundaries

- No real printer, no heating, no firmware, no public Moonraker, no real payment in bootstrap.
- License review required before commercial distribution (GPL/AGPL components).
- No model-generated shell command is executed without explicit tool policy.

## Open decisions

1. STEP→glTF conversion strategy and triangle budget.
2. `gcode-preview` vs custom Three.js toolpath renderer.
3. TripoSR local vs authorized cloud image-to-3D.
4. Physical ledger reconciliation source (spool weight vs slicer estimate).
5. Real-printer onboarding checklist and hardware E-stop.
