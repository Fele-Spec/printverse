# PrintVerse Image-to-3D Phase Report

Date: 2026-11-06 · Status: **PARTIAL**

## 1. Outcome

A multi-provider Image-to-3D architecture is implemented and runnable without any cloud key:

- unified provider result contract;
- free local Mock relief fallback (explicitly not real Image-to-3D);
- isolated TripoSR environment attempt;
- Stable Fast 3D availability/licence audit;
- TokenHub Tripo/HY-3D adapters with explicit authorization and no guessed endpoints;
- Kimi vision analysis client, respecting that Kimi is not a mesh API;
- 10-image benchmark runner/report;
- frontend Image → 3D studio with upload, provider selection, authorization, result download and hand-off to the print flow.

## 2. Hardware

- NVIDIA RTX 5060 Laptop, **8,151 MiB VRAM**, driver 592.82, CUDA 13.1.
- Main `.venv`: no torch; build123d/CadQuery environments untouched.
- `.venv-triposr` created; TripoSR source downloaded; checkpoint incomplete (network); CPU torch wheel download incomplete; CUDA torch wheel (3.27 GB) not feasible in this run.
- Therefore TripoSR is **not scored** and no VRAM claim is made.

## 3. Provider status

| Provider | Status |
|---|---|
| Mock relief | **COMPLETE** (free, watertight relief; not true 3D) |
| TripoSR local | **PARTIAL / BLOCKED_NETWORK** |
| Stable Fast 3D | **NOT_INSTALLED / LICENSE_REVIEW** |
| TokenHub Tripo | **NOT_CONFIGURED** (adapter written) |
| TokenHub HY-3D 3.1 | **NOT_CONFIGURED** (adapter written) |
| Kimi analysis | **BLOCKED_ACCOUNT** — API 429: account suspended due to insufficient balance |
| Kimi 3D Make | **MANUAL_ONLY** |

## 4. Kimi

- `GET /v1/models` returned 200; available IDs included `kimi-k3.1-pro`, `kimi-k3`, `kimi-k2.6`.
- One vision call returned **429** with `exceeded_current_quota_error`: account suspended due to insufficient balance.
- The key is stored only in ignored `.env.local`; it is not in Git/frontend/reports.
- The key was pasted in chat and should be rotated.
- Kimi is used for analysis/prompting only, never as a 3D mesh generator.

## 5. Tests

`backend/tests/test_image3d.py`:

- provider schema and availability;
- Mock job produces a real STL, watertight, cost 0;
- paid provider requires authorization;
- unavailable provider is rejected, not silently paid.

Result: **4 passed** (plus the existing accounting suite).

## 6. Benchmark

`MODEL_BENCHMARK_REPORT.md` and `docs/reports/image3d_benchmark.json`:

- same 10 synthetic images;
- Mock relief tested on all 10: watertight, 21,900 faces, ~1.1 MB each, 0.07–0.09 s, cost 0;
- TripoSR, Stable Fast 3D, Tripo, HY-3D marked NOT_TESTED with reasons;
- no vendor marketing claim used as a score.

## 7. Sharing

`frontend/dist/index.html` must be served over HTTP; double-clicking is not supported.

A shared mode is implemented (`PRINTVERSE_SHARE_MODE=1`): loopback is owner/admin unlimited;
remote LAN clients are guest with a 20 g wallet and no first-print-free. An optional
`PV_GUEST_TOKEN`/`X-PV-Member` gate exists. This is not password authentication; use a trusted
LAN/Tailscale/Cloudflare setup. See `SHARING_AND_QUOTA.md`; tests are in `backend/tests/test_share.py`.

## 8. Open items

1. Finish TripoSR install (use a fast network or HF mirror with enough time) and run one real image; measure VRAM and printability.
2. Recharge/rotate Kimi account if analysis is required.
3. Obtain TokenHub account-specific endpoints and authorize a small budget before any cloud call.
4. Add password/proxy authentication on top of the opt-in owner/guest quota mode.
5. Add photographed object benchmark and multi-view tests.

## 9. Files

- `IMAGE_TO_3D_PROVIDERS.md`
- `MODEL_BENCHMARK_REPORT.md`
- `SHARING_AND_QUOTA.md`
- `backend/app/image3d/`
- `frontend/src/components/Image3DPanel.tsx`
- `docs/reports/image3d_benchmark.json`
- `BEFORE_AFTER_SCREENSHOTS/after_image3d_panel.png`
- `BEFORE_AFTER_SCREENSHOTS/after_image3d_result.png`
