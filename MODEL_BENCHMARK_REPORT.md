# Image-to-3D Model Benchmark

Date: 2026-11-06 · Same 10 images in `assets/test-models/image3d/` · no paid call was made.

## Test set

The 10 images are intentionally simple synthetic objects (cube, sphere, cylinder, cone, torus, mug, tree, rocket, ring, vase) with clean white backgrounds. They are pipeline/printability benchmarks, not a substitute for a photographed-object benchmark.

## Availability

| Provider | Model | Status | Reason |
|---|---|---|---|
| mock_relief | silhouette-heightfield-v1 | TESTED | Not image-to-3D reconstruction; a heightfield/silhouette relief for pipeline testing. |
| triposr_local | TripoSR (stabilityai/TripoSR) | NOT_TESTED | TripoSR model.ckpt missing |
| stable_fast_3d | Stable Fast 3D | NOT_TESTED | Windows-native install not attempted; upstream project is research code and the official weights/license require review before download. |
| tripo_cloud | tripo-3d-3.1 | NOT_TESTED | TOKENHUB_API_KEY + submit/query URL not configured; see docs. |
| hy3d_cloud | hy-3d-3.1 | NOT_TESTED | TOKENHUB_API_KEY + submit/query URL not configured; see docs. |

## Results

### mock_relief

| Image | Watertight | Faces | Volume mm³ | Bytes | Time s | Cost CNY | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 01_cube.png | True | 21900 | 6819.399 | 1095084 | 0.07 | 0.0 | PASS |
| 02_sphere.png | True | 21900 | 8607.846 | 1095084 | 0.07 | 0.0 | PASS |
| 03_cylinder.png | True | 21900 | 6549.591 | 1095084 | 0.09 | 0.0 | PASS |
| 04_cone.png | True | 21900 | 5118.846 | 1095084 | 0.07 | 0.0 | PASS |
| 05_torus.png | True | 21900 | 8647.078 | 1095084 | 0.07 | 0.0 | PASS |
| 06_mug.png | True | 21900 | 5957.947 | 1095084 | 0.07 | 0.0 | PASS |
| 07_tree.png | True | 21900 | 4381.749 | 1095084 | 0.08 | 0.0 | PASS |
| 08_rocket.png | True | 21900 | 455.725 | 1095084 | 0.07 | 0.0 | PASS |
| 09_ring.png | True | 21900 | 2277.205 | 1095084 | 0.07 | 0.0 | PASS |
| 10_vase.png | True | 21900 | 3342.862 | 1095084 | 0.07 | 0.0 | PASS |

## Honest interpretation

- `mock_relief` is **not Image-to-3D**. It is a heightfield/silhouette relief and is included as a free printable fallback, not as a quality model.
- TripoSR is the intended free local candidate; hardware (RTX 5060, 8 GB) meets its ~6 GB claim, but the isolated environment/model download did not complete in this run. It is **not scored**.
- Stable Fast 3D was not installed on Windows; its license/weights require review. It is **not scored**.
- TokenHub Tripo and HY-3D were **not called**: no TokenHub key/endpoint was provided. They are **not scored**, and no cost was incurred.
- Kimi was verified as a vision/text analysis provider only; it is not a 3D mesh API. One chat request returned HTTP 429 with `exceeded_current_quota_error` (account suspended due to insufficient balance), so no Kimi analysis is claimed.
- Visual appeal is not treated as printability: only watertight + positive-volume meshes pass the quick printability check in this report.

## Next smallest steps

1. Finish the isolated TripoSR environment (CPU fallback or CUDA wheel) and rerun the same 10 images.
2. Obtain a TokenHub key + account-specific endpoint and explicitly authorize a small budget; then run Tripo H first.
3. Add photographed objects and multi-view images for a meaningful geometry/backside test.
4. Run `printverse-mesh-preflight` on every output and repair only a copy before slicing.
