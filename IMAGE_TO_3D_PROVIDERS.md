# Image-to-3D Provider Architecture

Date: 2026-11-06 · Status: **COMPLETE (architecture)**; TripoSR CPU tested; cloud/Kimi external gates BLOCKED

## 1. Hardware audit

| Item | Result |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Laptop |
| VRAM | **8,151 MiB** |
| Driver / CUDA | 592.82 / CUDA 13.1 |
| Main venv PyTorch | **not installed** |
| Main venv protected | build123d 0.13 + OCP 8 untouched; CadQuery has its own `.venv-cadquery` |
| Isolated TripoSR venv | `.venv-triposr` created |
| TripoSR source | `.cache/triposr-src/TripoSR-main` (MIT) |
| TripoSR checkpoint | **complete 1.68 GB** `.cache/TripoSR/model.ckpt` |

The GPU meets TripoSR's published ~6 GB target. The actual run used the **CPU fallback** because CUDA torch was not installed; no GPU throughput/VRAM claim is made.

## 2. Provider status

| Provider | Role | Status | Notes |
|---|---|---|---|
| **Mock relief** | free local fallback | **COMPLETE** | Colour GLB primary + STL/3MF/OBJ; watertight, cost 0; **not** genuine image-to-3D |
| **Multi-view local** | deterministic 3-view hull | **COMPLETE (local)** | Front/side/top silhouettes; visual hull, not AI; colour GLB |
| **Drawing local** | raster contour extrusion | **COMPLETE (basic)** | Dark closed contours → 2.5D GLB; dimensions/constraints NOT inferred |
| **TripoSR local** | free primary local | **COMPLETE (CPU)** | 10/10 meshes generated; 7 pass quick printability, 3 repair-required; ~25 s/image; cost 0 |
| **Stable Fast 3D** | free high-texture candidate | **NOT_INSTALLED** | Windows-native install not attempted; official weights/license need review |
| **TokenHub Tripo** | low-cost cloud | **NOT_CONFIGURED** | adapter implemented; needs official account endpoint + key |
| **TokenHub HY-3D 3.1** | high-quality cloud | **NOT_CONFIGURED** | adapter implemented; needs official account endpoint + key |
| **Kimi analysis** | image understanding / prompt | **BLOCKED_ACCOUNT / HTTP 429** | `/v1/models` returned 200 and listed `kimi-k3.1-pro`, `kimi-k3`, `kimi-k2.6`; one chat/vision call returned **429: account suspended due to insufficient balance** |
| **Kimi 3D Make** | manual import only | **MANUAL_ONLY** | no public 3D generation API assumed |

## 3. Unified contract

Every generation provider returns a colour GLB as the primary asset (STL/3MF/OBJ are derived):

```text
provider
model
task_id
output_format
output_url
local_path
generation_cost
texture_status
geometry_status
task_status
```

Extra audit fields: `cost_currency`, `cost_basis`, `error`, `metadata`.
The result schema is implemented in `backend/app/image3d/types.py`.

## 4. API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/image3d/providers` | availability, reason, cost class, license, docs |
| GET | `/api/image3d/jobs` | list recent jobs |
| POST | `/api/image3d/jobs` | image + provider + prompt + authorization/budget |
| GET | `/api/image3d/jobs/{id}` | status and result |
| POST | `/api/image3d/analyze` | Kimi image understanding only |

Frontend: top-right **图片 → 3D** opens the provider studio. It can upload, select provider, record the brief, preview/download the colour GLB, download derived STL/3MF, and hand the STL to the print flow while preserving the GLB for the finished object.

## 5. Cost routing and authorization

- `auto` chooses local TripoSR when fully ready, otherwise **Mock relief**.
- Cloud providers require **both** `authorized=true` and a **positive budget**; otherwise the API returns 402/409 and makes no call.
- Explicitly unavailable providers are rejected; they are never silently replaced with a paid provider.
- Free fallback is local-only; it records `fallback_from` and `fallback_reason`.
- Each job records `generation_cost`, `cost_currency`, `cost_basis`; unknown cost stays `null`, never invented.
- Retries are bounded (max two attempts); no infinite paid retry.

## 6. Cloud adapter reality check

Official docs:
- [TokenHub Tripo-3D](https://cloud.tencent.com/document/product/1823/137074) — models `tripo-3d-3.1`, `tripo-3d-p1`, `tripo-3d-p2`; image input is a URL.
- [TokenHub HY-3D](https://cloud.tencent.com/document/product/1823/137181) — models `hy-3d-3.0`, `hy-3d-3.1`; supports `image_base64` / `image_url`; `stl` is an allowed result format.

No TokenHub key or account-specific submit/query endpoint was available. The adapter therefore requires:

```text
TOKENHUB_API_KEY
TOKENHUB_TRIPO_SUBMIT_URL
TOKENHUB_TRIPO_QUERY_URL
TOKENHUB_HY3D_SUBMIT_URL
TOKENHUB_HY3D_QUERY_URL
```

Nothing was called and **no cost was incurred**. Tripo additionally needs a publicly reachable image URL; a local file is not silently uploaded or guessed into a URL.

## 7. Kimi

- Key is stored only in ignored `.env.local`; it is never in Git or the frontend.
- `kimi-k3.1-pro` supports image input according to `/v1/models`.
- It is used only for subject/silhouette/material analysis, a modeling brief, parameter hints, and mesh-error explanation.
- It is **not** a text-to-3D mesh API.
- One test call returned HTTP 429 with `exceeded_current_quota_error`: the account is suspended due to insufficient balance. The client reports unavailable and invents no analysis. Recharge the Kimi account and set `KIMI_ANALYSIS_ENABLED=true` to retry.
- **Rotate the key** because it was pasted into the conversation.

## 8. Ten-image benchmark

`MODEL_BENCHMARK_REPORT.md` records the same 10 synthetic object images. Mock relief and TripoSR CPU were actually tested; TripoSR produced 10/10 meshes, 7 quick printability passes and 3 repair-required outputs. Stable Fast 3D, Tripo and HY-3D are marked NOT_TESTED with reasons. No vendor claims are used as quality data.

## 9. Safety and boundaries

- Original CAD and model environments untouched.
- No real printer, no heating, no payment; cloud calls require explicit authorization.
- No model weight or vendor asset is committed from `.cache`.
- Kimi key not logged in reports or manifests.
