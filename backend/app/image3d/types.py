"""Shared types for PrintVerse Image-to-3D providers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderInfo:
    id: str
    label: str
    kind: str  # local | cloud | analysis
    model: str
    available: bool
    reason: str = ""
    cost_class: str = "free"  # free | low | high | unknown
    requires_authorization: bool = False
    requires_key: bool = False
    output_formats: list[str] = field(default_factory=list)
    supports_texture: bool = False
    docs_url: str = ""
    license: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class GenerationResult:
    provider: str
    model: str
    task_id: str
    output_format: str
    output_url: str
    local_path: str
    generation_cost: float | None
    texture_status: str
    geometry_status: str
    task_status: str
    cost_currency: str = "CNY"
    cost_basis: str = "provider-reported"  # free | provider-reported | unknown
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class GenerationRequest:
    job_id: str
    image_path: str
    prompt: str = ""
    authorized: bool = False
    budget_cny: float = 0.0
    options: dict[str, Any] = field(default_factory=dict)


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, status: str = "failed", retryable: bool = False, cost: float | None = None):
        super().__init__(message)
        self.status = status
        self.retryable = retryable
        self.cost = cost
