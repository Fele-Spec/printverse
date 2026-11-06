"""TokenHub Tripo / HY-3D adapters.

The public docs define model names and parameters, but the exact HTTP endpoint
assigned to an account is not assumed here. Endpoints must be provided through
environment variables. Without a key and endpoints the provider is reported as
CONFIG_REQUIRED and never charges anything.
"""
from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

import httpx

from ..mesh_prep import export_bundle, repair_and_scale
from . import config
from .base import Image3DProvider
from .types import GenerationRequest, GenerationResult, ProviderError, ProviderInfo

ROOT = Path(__file__).resolve().parents[3]


class TokenHubProvider(Image3DProvider):
    def __init__(self, kind: str):
        self.kind = kind  # tripo | hy3d
        self.id = "tripo_cloud" if kind == "tripo" else "hy3d_cloud"
        self.model = config.get("TOKENHUB_TRIPO_MODEL", "tripo-3d-3.1") if kind == "tripo" else config.get("TOKENHUB_HY3D_MODEL", "hy-3d-3.1")
        self.key = config.get("TOKENHUB_API_KEY")
        self.submit_url = config.get(f"TOKENHUB_{'TRIPO' if kind == 'tripo' else 'HY3D'}_SUBMIT_URL")
        self.query_url = config.get(f"TOKENHUB_{'TRIPO' if kind == 'tripo' else 'HY3D'}_QUERY_URL")

    def info(self) -> ProviderInfo:
        configured = bool(self.key and self.submit_url and self.query_url)
        reason = "ready" if configured else "TOKENHUB_API_KEY + submit/query URL not configured; see docs."
        return ProviderInfo(
            id=self.id,
            label="TokenHub Tripo" if self.kind == "tripo" else "TokenHub HY-3D 3.1",
            kind="cloud", model=self.model, available=configured, reason=reason,
            cost_class="low" if self.kind == "tripo" else "high",
            requires_authorization=True, requires_key=True,
            output_formats=["glb", "obj", "stl"], supports_texture=True,
            docs_url="https://cloud.tencent.com/document/product/1823/137074" if self.kind == "tripo" else "https://cloud.tencent.com/document/product/1823/137181",
            license="Tencent Cloud TokenHub terms",
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        info = self.info()
        if not info.available:
            raise ProviderError(info.reason, status="not_configured")
        if not request.authorized or request.budget_cny <= 0:
            raise ProviderError("cloud generation requires explicit authorization and a positive budget", status="authorization_required")
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {"model": self.model, "texture": True, "pbr": True}
        if request.prompt:
            payload["prompt"] = request.prompt[:1024]
        if self.kind == "hy3d":
            data = base64.b64encode(Path(request.image_path).read_bytes()).decode("ascii")
            payload.update({"image_base64": data, "enable_pbr": True, "generate_type": "Normal", "result_format": "stl"})
        else:
            # Tripo's documented image input is a URL. A local file cannot be sent as a URL;
            # a public image URL must be supplied explicitly.
            image_url = request.options.get("image_url") or config.get("TOKENHUB_IMAGE_URL")
            if not image_url:
                raise ProviderError("Tripo input requires a public image URL; set options.image_url or TOKENHUB_IMAGE_URL", status="not_configured")
            payload.update({"input": image_url, "texture": True, "pbr": True, "face_limit": 50000})
        with httpx.Client(timeout=60) as client:
            r = client.post(self.submit_url, headers=headers, json=payload)
            if r.status_code in (401, 403):
                raise ProviderError(f"TokenHub unauthorized ({r.status_code})", status="failed")
            r.raise_for_status()
            submitted = r.json()
        task_id = submitted.get("id") or submitted.get("task_id") or submitted.get("data", {}).get("id")
        if not task_id:
            raise ProviderError("TokenHub response has no task id", status="failed")
        deadline = time.time() + 300
        while time.time() < deadline:
            time.sleep(5)
            with httpx.Client(timeout=60) as client:
                q = client.get(self.query_url, headers=headers, params={"id": task_id})
                q.raise_for_status()
                result = q.json()
            data = result.get("data", result)
            status = str(data.get("status", "")).lower()
            if status in {"completed", "succeeded", "success"}:
                url = data.get("output_url") or data.get("model_url") or data.get("result_url")
                if not url:
                    files = data.get("files") or data.get("result", {}).get("files") or []
                    if files:
                        url = files[0] if isinstance(files[0], str) else files[0].get("url")
                if not url:
                    raise ProviderError("completed task has no output URL", status="failed")
                job_dir = ROOT / "runtime" / "image3d" / request.job_id
                job_dir.mkdir(parents=True, exist_ok=True)
                suffix = Path(url.split("?", 1)[0]).suffix.lower()
                source = job_dir / f"cloud_raw{suffix if suffix in {'.glb', '.stl', '.obj'} else '.glb'}"
                with httpx.Client(timeout=120, follow_redirects=True) as client:
                    dl = client.get(url)
                    dl.raise_for_status()
                    source.write_bytes(dl.content)
                import trimesh
                mesh = trimesh.load(source, force="mesh", process=True)
                fixed, prep = repair_and_scale(mesh, target_mm=80.0)
                paths = export_bundle(fixed, job_dir, "cloud")
                cost = data.get("generation_cost", data.get("cost"))
                return GenerationResult(
                    provider=self.id, model=self.model, task_id=str(task_id), output_format="glb",
                    output_url=f"/runtime/image3d/{request.job_id}/cloud.glb",
                    local_path=paths["glb"],
                    generation_cost=float(cost) if isinstance(cost, (int, float)) else None,
                    cost_basis="provider-reported" if isinstance(cost, (int, float)) else "unknown",
                    texture_status="VERTEX_COLOR" if getattr(fixed.visual, "kind", "") == "vertex" else "REQUESTED",
                    geometry_status="REPAIRED" if prep["raw"] != prep["repaired"] else "GENERATED",
                    task_status="completed",
                    metadata={
                        "raw_status": data, "prep": prep,
                        "stl_url": f"/runtime/image3d/{request.job_id}/cloud.stl",
                        "three_mf_url": f"/runtime/image3d/{request.job_id}/cloud.3mf",
                        "asset_format": "glb",
                    },
                )
            if status in {"failed", "error", "cancelled"}:
                raise ProviderError(f"TokenHub task {status}: {data}", status="failed")
        raise ProviderError("TokenHub task timed out", status="timeout", retryable=True)
