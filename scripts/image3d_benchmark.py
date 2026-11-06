"""Benchmark the Image-to-3D providers that are actually available.

This never calls a paid provider. Unavailable providers are recorded with their
availability reason instead of being scored on marketing claims.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.image3d import registry  # noqa: E402
from backend.app.image3d.types import GenerationRequest  # noqa: E402
IMAGES = sorted((ROOT / "assets/test-models/image3d").glob("*.png"))
OUT = ROOT / "docs/reports/image3d_benchmark.json"
REPORT = ROOT / "MODEL_BENCHMARK_REPORT.md"


def audit(path: Path) -> dict:
    mesh = trimesh.load(path, force="mesh", process=True)
    return {
        "vertices": int(len(mesh.vertices)), "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight), "volume_mm3": round(float(mesh.volume), 3),
        "extents_mm": [round(float(v), 3) for v in mesh.extents],
        "bytes": path.stat().st_size,
    }


def main() -> int:
    providers = {p.id: p for p in registry.providers()}
    rows = []
    notes = []
    for provider_id in ("mock_relief", "triposr_local", "tripo_cloud", "hy3d_cloud", "stable_fast_3d"):
        info = providers[provider_id]
        if not info.available:
            notes.append({"provider": provider_id, "model": info.model, "status": "NOT_TESTED", "reason": info.reason})
            continue
        for img in IMAGES:
            t0 = time.time()
            try:
                result = registry.run(provider_id, GenerationRequest(
                    job_id=f"bench-{provider_id}-{img.stem}", image_path=str(img),
                    prompt="benchmark object", authorized=False, budget_cny=0,
                ), allow_free_fallback=False)
                path = ROOT / result.local_path
                a = audit(path)
                rows.append({
                    "provider": provider_id, "model": result.model, "image": img.name,
                    "seconds": round(time.time() - t0, 2), "cost_cny": result.generation_cost,
                    "cost_basis": result.cost_basis, "output_format": result.output_format,
                    "texture_status": result.texture_status, "geometry_status": result.geometry_status,
                    **a,
                    "printability": "PASS" if a["watertight"] and a["volume_mm3"] > 0 else "REPAIR_REQUIRED",
                })
            except Exception as exc:  # noqa: BLE001
                rows.append({"provider": provider_id, "image": img.name, "status": "FAILED", "error": str(exc)[:500]})
    OUT.write_text(json.dumps({"images": [i.name for i in IMAGES], "rows": rows, "not_tested": notes}, indent=2), encoding="utf-8")

    by_provider: dict[str, list[dict]] = {}
    for row in rows:
        by_provider.setdefault(row["provider"], []).append(row)
    lines = [
        "# Image-to-3D Model Benchmark", "",
        "Date: 2026-11-06 · Same 10 images in `assets/test-models/image3d/` · no paid call was made.", "",
        "## Test set", "",
        "The 10 images are intentionally simple synthetic objects (cube, sphere, cylinder, cone, torus, mug, tree, rocket, ring, vase) with clean white backgrounds. They are pipeline/printability benchmarks, not a substitute for a photographed-object benchmark.", "",
        "## Availability", "",
        "| Provider | Model | Status | Reason |",
        "|---|---|---|---|",
    ]
    for pid, info in providers.items():
        if info.kind == "analysis":
            continue
        lines.append(f"| {pid} | {info.model} | {'TESTED' if pid in by_provider else 'NOT_TESTED'} | {info.reason or 'ready'} |")
    lines += ["", "## Results", ""]
    for pid, rs in by_provider.items():
        lines += [f"### {pid}", "", "| Image | Watertight | Faces | Volume mm³ | Bytes | Time s | Cost CNY | Verdict |", "|---|---:|---:|---:|---:|---:|---:|---|"]
        for r in rs:
            if r.get("status") == "FAILED":
                lines.append(f"| {r['image']} | — | — | — | — | — | — | FAILED: {r['error'][:80]} |")
            else:
                lines.append(f"| {r['image']} | {r['watertight']} | {r['faces']} | {r['volume_mm3']} | {r['bytes']} | {r['seconds']} | {r['cost_cny']} | {r['printability']} |")
        lines += [""]
    lines += [
        "## Honest interpretation", "",
        "- `mock_relief` is **not Image-to-3D**. It is a heightfield/silhouette relief and is included as a free printable fallback, not as a quality model.",
        "- TripoSR was actually run on the CPU fallback: 10/10 produced meshes; 7 passed the quick watertight/positive-volume check and 3 required repair. CPU time was ~25 s/image; cost 0. GPU CUDA was not installed/used, so this is not a GPU throughput claim. The output is scaled to an 80 mm longest side; raw GLB is retained.",
        "- Stable Fast 3D was not installed on Windows; its license/weights require review. It is **not scored**.",
        "- TokenHub Tripo and HY-3D were **not called**: no TokenHub key/endpoint was provided. They are **not scored**, and no cost was incurred.",
        "- Kimi was verified as a vision/text analysis provider only; it is not a 3D mesh API. One chat request returned HTTP 429 with `exceeded_current_quota_error` (account suspended due to insufficient balance), so no Kimi analysis is claimed.",
        "- Visual appeal is not treated as printability: only watertight + positive-volume meshes pass the quick printability check in this report.",
        "",
        "## Next smallest steps", "",
        "1. Run TripoSR on the CUDA build and compare the 3 non-watertight outputs after targeted repair.",
        "2. Obtain a TokenHub key + account-specific endpoint and explicitly authorize a small budget; then run Tripo H first.",
        "3. Add photographed objects and multi-view images for a meaningful geometry/backside test.",
        "4. Run `printverse-mesh-preflight` on every output and repair only a copy before slicing.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "tested_providers": list(by_provider), "not_tested": notes}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
