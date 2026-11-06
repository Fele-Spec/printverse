# PrintVerse Next Development Plan

The bootstrap is **PARTIAL**. The foundation is real, but the browser render, Python-native
CAD, and image-to-3D path need the next phase.

## P0 — Close the verification gap (1–2 days)

1. Run `npm run preview --prefix frontend` and `scripts/threejs_smoke.mjs` in a non-sandboxed
   session; capture 1440×980 screenshots for dark/light/blueprint and drag/zoom.
2. Resolve the 275 vs 280 mm printable-height discrepancy against a real Voron or the official
   Klipper config; do not change the vendor profile silently.
3. Install `build123d` and `cadquery` in an isolated venv on a faster link; test
   `Box`/`import_step` and record OCP versions.
4. Decide whether to pin Three.js 0.185 for `gcode-preview` or isolate a viewer package.

**Acceptance:** screenshot files exist and are reviewed; both Python CAD libraries import a
STEP; no profile value is marked calibrated without evidence.

## P1 — Digital twin geometry (3–5 days)

1. Convert the 267 MB STEP assembly to a web-friendly hierarchy with FreeCAD/Blender:
   preserve product names, merge by material, decimate to a triangle budget, export glTF/GLB.
2. Build an asset manifest mapping CAD occurrences → machine nodes (frame, gantry, Z, toolhead,
   electronics bay).
3. Add a low-poly LOD and an instancing path for repeated fasteners.
4. Keep the original STEP untouched; write all conversions to `assets/processed/`.

**Acceptance:** GLB loads under 5 s locally; < 1.5 M triangles; named nodes resolve; bounding
box 460×460×480 mm ± 2 mm; visual pivot/origin documented.

## P2 — G-code toolpath streaming (3–5 days)

1. Convert parsed moves to a compact binary/JSON stream: layer index, type, x/y/z, extrusion
   width/volume, feed.
2. Implement a Three.js `LineSegments` renderer with per-layer visibility and a layer slider.
3. Add nozzle position interpolation and a “material growth” shader driven by extrusion.
4. Benchmark 1 M segments at 60 fps; use typed arrays and chunked uploads.
5. Compare `gcode-preview` (pin 0.185) against the custom renderer.

**Acceptance:** 100-layer cube and a 1 M-segment file render interactively; layer count and
mass match `gcode_parse.json`; no full G-code text is sent to an LLM.

## P3 — Image-to-3D (3–7 days, hardware-gated)

1. On a faster link, install TripoSR CPU/CUDA path in an isolated environment and test one image
   on the 8 GB GPU. Record peak VRAM and mesh watertightness.
2. Run every generated mesh through `printverse-mesh-preflight`; reject or repair before slicing.
3. If local quality is insufficient, prepare a provider-agnostic API adapter, but do not call a
   paid API or accept a license without the user's explicit authorization.
4. Hunyuan3D and TRELLIS stay out of scope on this GPU.

**Acceptance:** one image → printable mesh with recorded VRAM, runtime, license, and a
watertight/repair report; no hidden paid usage.

## P4 — Filament accounting (2–4 days)

1. Implement the schema from `printverse-filament-accounting`.
2. Reserve on slice release, commit on completion, release on cancel; idempotency by
   `operation_id`.
3. First virtual print free; admin unlimited virtual but usage still logged.
4. Concurrency tests for negative balance and duplicate commits.
5. No payment provider until separately authorized.

**Acceptance:** all seven accounting tests in the skill pass; a double commit produces one
ledger row; physical and virtual wallets cannot cross-mutate.

## P5 — Moonraker read-only design (2–3 days)

1. Build a fixture server and a `PrinterSnapshot` normalizer.
2. Allowlist read-only endpoints; hard timeout and response-size cap.
3. Add a `control` client that is disabled by default and cannot be enabled by config alone.
4. Do not connect to a real printer.

**Acceptance:** fixture snapshot works; mutating endpoints are unreachable from the read-only
client; no secret appears in logs or Git.

## P6 — Product/backend surface (after P1–P4)

- Auth, roles (`user`, `admin`), quotas, entitlements, audit log.
- Upload pipeline: image/PDF/STEP/STL/3MF → validation → AI/CAD → mesh preflight → slice.
- Job queue and SSE/WebSocket progress.
- Paywall UI states but no live payment.
- Cost dashboard fed by the provider's real usage API, not estimates.

## P7 — Real printer onboarding (separate written authorization only)

- Physical E-stop, thermal runaway, max temperature and motion envelope checks.
- Moonraker on loopback/VPN, API key rotation, dry-run first.
- First real job only after a signed checklist and explicit user approval.

## Budget and stop rules

- Default model: `deepseek-flash`; low/standard reasoning.
- Normal retries: 3. On the third failure, write the exact command/error and mark BLOCKED.
- At RMB 80, stop optional work and emit a cost report; never exceed RMB 100 without a new
  explicit authorization.
- No paid cloud GPU or image API in the current phase.

## Definition of done for the next phase

The digital twin loads the converted Voron assembly in a browser; a sliced cube drives the
nozzle and grows material layer by layer; the model can be detached from the plate; the first
free print and quota ledger pass deterministic tests; and Moonraker remains read-only. Until
then, this project stays **PARTIAL**, not COMPLETE.
