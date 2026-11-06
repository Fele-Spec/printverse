# Performance Report

Date: 2026-11-06 · Browser: Microsoft Edge, local `http://127.0.0.1:4173/`

## 1. Model budget

| Metric | Value |
|---|---:|
| Placement records | 4,526 |
| Shape-bearing parts | 1,686 |
| Full module GLBs | 8 files / **35.49 MB** |
| Full triangles | 1,939,867 |
| Default LOD GLBs | 8 files / **8.92 MB** |
| LOD triangles | 497,199 |
| Default draw calls | 8 merged module meshes |
| High-detail draw calls | 1,686 part meshes when Toolhead/Interior view is active |
| InstancedMesh objects | 0 (not implemented) |
| Load errors | 0 |

## 2. Measured load

Headless Edge / local Vite preview:

- first visible scene: **8.0–9.1 s** (all LOD modules, localhost)
- GLB transfer durations: 2–153 ms after warm cache; first frame includes mesh/material setup
- no page errors or HTTP failures

## 3. Measured FPS

### Hardware WebGL — PASS

Script: `scripts/phase3_perf_hw.mjs` (non-headless Edge, D3D11, window off-screen)

```json
{"renderer":"ANGLE (AMD, AMD Radeon(TM) 610M (0x0000164E) Direct3D11 vs_5_0 ps_5_0, D3D11)",
 "raf":60.10,"renderFrames":181}
```

- **60.1 FPS**, above the 45 FPS target.
- The count is from the scene's internal `useFrame` counter, not only `requestAnimationFrame`.

### Headless SwiftShader — NOT A HARDWARE FPS REFERENCE

`scripts/phase3_perf.mjs` / `phase3_after_views.mjs`:

- rAF and `useFrame` both throttled/very slow: **0.8–2.2 FPS**
- renderer: `ANGLE ... SwiftShader Device`
- This is the software rasterizer used for deterministic screenshots, not the user's GPU.
- Do not present the SwiftShader number as the product FPS; it is recorded to keep the
  measurement honest.

## 4. Optimizations applied

1. **Per-module merged render LOD**: 1,686 draw calls → 8 draw calls by default.
2. **Face-range picking** (`module-face-ranges-lod.json`): merged mesh face index → placement ID,
   so part selection survives the merge.
3. **High-detail on demand**: Toolhead and Interior views load the full 1,686-node GLBs; Product,
   Top, Engineering and Exploded use the 497k-face LOD.
4. **Static contact shadows** (`frames={1}`), 1024 shadow map, no real-mesh cast shadows.
5. **Asynchronous per-module loading** with Suspense.
6. **Transparent enclosure** uses a single standard material; transmission is not recomputed for
   every panel.

## 5. Not implemented / risks

- **InstancedMesh is not implemented** for repeated bolts/nuts/washers. The current LOD merges
  them; this saves draw calls but does not satisfy the instancing requirement. Mark PARTIAL.
- No Draco/Meshopt compression; GLBs are raw. 35.5 MB full / 9.7 MB LOD is acceptable on localhost
  but should be compressed before deployment.
- The LOD decimation is aggressive for small features (18% retained faces per large part); close
  inspection uses the full module mesh, but the merged LOD can show faceting at product scale.
- The CAD mode now drives the real TOOLHEAD and BUILD_PLATFORM nodes; the XY crossbeam remains
  static and is not yet a separate movable component.
- Hardware FPS was measured with the CAD display only; the combined print animation plus CAD
  mode was not benchmarked on hardware.

## 6. Verdict

- **Hardware FPS target (45): PASS** at 60.1 FPS.
- **Headless software target: NOT MET** at 0.8–2.2 FPS; environment limitation.
- **Instancing requirement: PARTIAL**.
- **Load target: no numeric target given; 8–9 s local, acceptable for this asset size.**
