# Image-to-3D Model Benchmark

Date: 2026-11-06 · Same 10 images in `assets/test-models/image3d/` · no paid call was made.

## Test set

The 10 images are intentionally simple synthetic objects (cube, sphere, cylinder, cone, torus, mug, tree, rocket, ring, vase) with clean white backgrounds. They are pipeline/printability benchmarks, not a substitute for a photographed-object benchmark.

## Availability

| Provider | Model | Status | Reason |
|---|---|---|---|
| mock_relief | silhouette-heightfield-v1 | TESTED | Not image-to-3D reconstruction; a heightfield/silhouette relief for pipeline testing. |
| triposr_local | TripoSR (stabilityai/TripoSR) | TESTED | ready |
| stable_fast_3d | Stable Fast 3D | NOT_TESTED | Windows-native install not attempted; upstream project is research code and the official weights/license require review before download. |
| tripo_cloud | tripo-3d-3.1 | NOT_TESTED | TOKENHUB_API_KEY + submit/query URL not configured; see docs. |
| hy3d_cloud | hy-3d-3.1 | NOT_TESTED | TOKENHUB_API_KEY + submit/query URL not configured; see docs. |

## Results

TripoSR CPU was actually run on all 10 images: **10 generated, 7 PASS, 3 REPAIR_REQUIRED**. CPU time was about 25 s/image; cost 0. The 3 failures are recorded, not hidden.


### mock_relief

| Image | Watertight | Faces | Volume mm³ | Bytes | Time s | Cost CNY | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 01_cube.png | True | 21900 | 6819.399 | 1095084 | 0.08 | 0.0 | PASS |
| 02_sphere.png | True | 21900 | 8607.846 | 1095084 | 0.07 | 0.0 | PASS |
| 03_cylinder.png | True | 21900 | 6549.591 | 1095084 | 0.08 | 0.0 | PASS |
| 04_cone.png | True | 21900 | 5118.846 | 1095084 | 0.06 | 0.0 | PASS |
| 05_torus.png | True | 21900 | 8647.078 | 1095084 | 0.06 | 0.0 | PASS |
| 06_mug.png | True | 21900 | 5957.947 | 1095084 | 0.07 | 0.0 | PASS |
| 07_tree.png | True | 21900 | 4381.749 | 1095084 | 0.09 | 0.0 | PASS |
| 08_rocket.png | True | 21900 | 455.725 | 1095084 | 0.06 | 0.0 | PASS |
| 09_ring.png | True | 21900 | 2277.205 | 1095084 | 0.07 | 0.0 | PASS |
| 10_vase.png | True | 21900 | 3342.862 | 1095084 | 0.07 | 0.0 | PASS |

### triposr_local

| Image | Watertight | Faces | Volume mm³ | Bytes | Time s | Cost CNY | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 01_cube.png | True | 61952 | 37231.164 | 3097684 | 24.84 | 0.0 | PASS |
| 02_sphere.png | False | 73624 | 60586.81 | 3681284 | 25.94 | 0.0 | REPAIR_REQUIRED |
| 03_cylinder.png | False | 58404 | 29506.931 | 2920284 | 24.98 | 0.0 | REPAIR_REQUIRED |
| 04_cone.png | False | 57532 | 41491.402 | 2876684 | 25.33 | 0.0 | REPAIR_REQUIRED |
| 05_torus.png | True | 63608 | 47484.336 | 3180484 | 26.1 | 0.0 | PASS |
| 06_mug.png | True | 67628 | 33744.474 | 3381484 | 24.86 | 0.0 | PASS |
| 07_tree.png | True | 54700 | 19662.527 | 2735084 | 25.4 | 0.0 | PASS |
| 08_rocket.png | True | 60288 | 20559.018 | 3014484 | 25.42 | 0.0 | PASS |
| 09_ring.png | True | 68152 | 31248.221 | 3407684 | 25.22 | 0.0 | PASS |
| 10_vase.png | True | 53860 | 27738.639 | 2693084 | 25.35 | 0.0 | PASS |

## Honest interpretation

- `mock_relief` is **not Image-to-3D**. It is a heightfield/silhouette relief and is included as a free printable fallback, not as a quality model.
- TripoSR is the intended free local candidate and was actually run on the CPU fallback: 10/10 produced meshes; 7 passed the quick watertight/positive-volume check and 3 required repair. CPU time was ~25 s/image; cost 0. GPU CUDA was not installed/used, so this is not a GPU throughput claim. The output is scaled to an 80 mm longest side; raw GLB is retained.
- Stable Fast 3D was not installed on Windows; its license/weights require review. It is **not scored**.
- TokenHub Tripo and HY-3D were **not called**: no TokenHub key/endpoint was provided. They are **not scored**, and no cost was incurred.
- Kimi was verified as a vision/text analysis provider only; it is not a 3D mesh API. One chat request returned HTTP 429 with `exceeded_current_quota_error` (account suspended due to insufficient balance), so no Kimi analysis is claimed.
- Visual appeal is not treated as printability: only watertight + positive-volume meshes pass the quick printability check in this report.

## Next smallest steps

1. Run TripoSR on the CUDA build and compare the 3 non-watertight outputs after targeted repair.
2. Obtain a TokenHub key + account-specific endpoint and explicitly authorize a small budget; then run Tripo H first.
3. Add photographed objects and multi-view images for a meaningful geometry/backside test.
4. Run `printverse-mesh-preflight` on every output and repair only a copy before slicing.
