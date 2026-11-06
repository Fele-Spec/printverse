"""Stable Fast 3D candidate — audited but not installed on Windows yet."""
from __future__ import annotations

from .base import Image3DProvider
from .types import GenerationRequest, GenerationResult, ProviderError, ProviderInfo


class StableFast3DProvider(Image3DProvider):
    id = "stable_fast_3d"
    model = "Stable Fast 3D"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id, label="Stable Fast 3D (candidate)", kind="local", model=self.model,
            available=False,
            reason="Windows-native install not attempted; upstream project is research code and the official weights/license require review before download.",
            cost_class="free", output_formats=["glb"], supports_texture=True,
            docs_url="https://github.com/Stability-AI/stable-fast-3d",
            license="Stability AI Community License / research terms — REVIEW_REQUIRED",
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderError(self.info().reason, status="not_configured")
