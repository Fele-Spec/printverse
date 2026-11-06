"""Isolated local TripoSR provider."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import trimesh

from .base import Image3DProvider
from .types import GenerationRequest, GenerationResult, ProviderError, ProviderInfo

ROOT = Path(__file__).resolve().parents[3]
VENV = ROOT / ".venv-triposr"
RUNNER = ROOT / "scripts" / "triposr_runner.py"
REPO = ROOT / ".cache" / "triposr-src" / "TripoSR-main"
MODEL = ROOT / ".cache" / "TripoSR" / "model.ckpt"


class TripoSRProvider(Image3DProvider):
    id = "triposr_local"
    model = "TripoSR (stabilityai/TripoSR)"

    def _ready(self) -> tuple[bool, str]:
        if not (VENV / "Scripts" / "python.exe").exists():
            return False, "isolated .venv-triposr missing"
        if not MODEL.exists():
            return False, "TripoSR model.ckpt missing"
        if not REPO.exists():
            return False, "TripoSR source missing"
        try:
            r = subprocess.run([str(VENV / "Scripts" / "python.exe"), "-c", "import torch; print(torch.__version__)"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                return False, "torch not importable in .venv-triposr"
        except Exception as exc:
            return False, repr(exc)
        return True, "ready"

    def info(self) -> ProviderInfo:
        ready, reason = self._ready()
        return ProviderInfo(
            id=self.id, label="TripoSR local", kind="local", model=self.model,
            available=ready, reason=reason, cost_class="free", output_formats=["glb", "stl"],
            supports_texture=True, license="MIT (source and pretrained model)",
            docs_url="https://github.com/VAST-AI-Research/TripoSR",
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        ready, reason = self._ready()
        if not ready:
            raise ProviderError(reason, status="not_configured")
        job_dir = ROOT / "runtime" / "image3d" / request.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        raw = job_dir / "triposr.glb"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO)
        cmd = [
            str(VENV / "Scripts" / "python.exe"), str(RUNNER),
            "--image", request.image_path, "--output", str(raw),
            "--model-dir", str(MODEL.parent), "--device", "cuda:0",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
        if proc.returncode != 0:
            raise ProviderError((proc.stderr or proc.stdout or "TripoSR failed")[-4000:], status="failed", retryable=True)
        metrics = None
        for line in proc.stdout.splitlines():
            if line.startswith("TRIPOSR_RESULT "):
                metrics = json.loads(line[len("TRIPOSR_RESULT "):])
        if not raw.exists():
            raise ProviderError("TripoSR produced no mesh", status="failed")
        mesh = trimesh.load(raw, force="mesh", process=True)
        stl = job_dir / "triposr.stl"
        mesh.export(stl)
        return GenerationResult(
            provider=self.id, model=self.model, task_id=request.job_id,
            output_format="stl", output_url=f"/runtime/image3d/{request.job_id}/triposr.stl",
            local_path=str(stl.relative_to(ROOT)).replace("\\", "/"),
            generation_cost=0.0, cost_basis="free",
            texture_status="VERTEX_COLOR" if getattr(mesh.visual, "kind", "") == "vertex" else "NONE",
            geometry_status="GENERATED_UNVALIDATED", task_status="completed",
            metadata={"triposr": metrics, "watertight": bool(mesh.is_watertight)},
        )
