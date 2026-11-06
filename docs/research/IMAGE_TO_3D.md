> **Phase-4 update:** The multi-provider implementation and current status are in `IMAGE_TO_3D_PROVIDERS.md` and `PHASE4_REPORT.md`. This file is retained as the original hardware evaluation. The Kimi key was tested: model listing succeeded but chat returned HTTP 429 due to insufficient account balance. No cloud 3D call was made.

# Image-to-3D Evaluation for PrintVerse

Evaluated 2026-11-06. Host GPU: **NVIDIA RTX 5060 Laptop, 8,151 MiB VRAM**, driver 592.82.
No model weights were downloaded, no account/API key used, and no license accepted on the
user's behalf.

## Candidates

| System | Local feasibility on 8 GB | Official requirement | License | Weights / repo | Status |
|---|---|---|---|---|---|
| **Hunyuan3D 2.1** | No | ~10 GB VRAM for shape, 21 GB for texture, 29 GB total | GitHub `NOASSERTION` (Tencent community license terms) → treat as **UNKNOWN_LICENSE** until legal review | ~3.3B shape + 2B paint; large | **BLOCKED** |
| **TRELLIS** | No | NVIDIA GPU with **at least 16 GB** | MIT | Large, multi-stage pipeline | **BLOCKED** |
| **TripoSR** | Marginal but plausible | README: about **6 GB VRAM** for a single image | MIT (source, pretrained models, demo) | ~0.5B-class LRM; smaller than the others | **PARTIAL** — candidate, not installed |
| Paid API (e.g. Tripo/Hunyuan cloud) | N/A | account + key + billing | provider terms | not invoked | **NOT_STARTED** — requires explicit authorization |

Sources:

- https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 (README model-zoo table, license)
- https://github.com/microsoft/TRELLIS (README hardware section, license)
- https://github.com/VAST-AI-Research/TripoSR (README installation/VRAM, license)
- TripoSR repo activity: pushed 2026-06-04, ~7,298 stars, MIT, not archived.

## Printability comparison

| Criterion | Hunyuan3D 2.1 | TRELLIS | TripoSR |
|---|---|---|---|
| Visual quality | Highest of the three | High, flexible output | Good, fast |
| Watertightness for printing | Needs mesh repair | Needs repair/decimation | Often needs repair/remeshing |
| VRAM | 10–29 GB | ≥16 GB | ~6 GB |
| Texture | PBR texture pipeline | Radiance/Gaussian/mesh | Vertex/texture-limited |
| Local on this host | No | No | Possible; to be tested |
| License clarity | Unclear/commercial review | MIT | MIT |

No image-to-3D mesh should reach the slicer without `printverse-mesh-preflight`; visual quality
does not imply a manifold, printable shell.

## Decision

1. Do **not** download Hunyuan3D or TRELLIS weights on this 8 GB machine.
2. Keep TripoSR as the local candidate; install it only on a faster link and in an isolated
   environment, then measure peak VRAM and repair rate.
3. Any cloud API is opt-in only; it requires the user's own account/key, an explicit budget,
   and acceptance of the provider's terms. No key was created or used here.
4. Until a candidate passes the mesh preflight, the product should show “AI draft, not yet
   printable” rather than promising a print-ready model.

## Next test protocol (when authorized)

1. One reference image with a clear silhouette and a known scale marker.
2. Record wall time, peak VRAM, output triangle count, watertightness, non-manifold edges.
3. Repair a copy in `assets/processed/`; re-run the audit.
4. Slice the repaired mesh with the Voron 300 profile; compare mass and bounds with the source.
5. Record the license and model hash in `manifests/resources.json`.
