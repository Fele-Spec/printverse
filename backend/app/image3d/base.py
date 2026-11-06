"""Base provider contract."""
from __future__ import annotations

from .types import GenerationRequest, GenerationResult, ProviderInfo


class Image3DProvider:
    id: str
    model: str

    def info(self) -> ProviderInfo:
        raise NotImplementedError

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise NotImplementedError

    def analyze(self, image_path: str, prompt: str = "") -> dict:
        raise NotImplementedError("not an analysis provider")
