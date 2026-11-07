"""Registry and cost-aware orchestration for Image-to-3D providers."""
from __future__ import annotations

from pathlib import Path

from .base import Image3DProvider
from .kimi import KimiClient
from .drawing import DrawingProvider
from .mock_relief import MockReliefProvider
from .multiview import MultiViewProvider
from .stablefast3d import StableFast3DProvider
from .tokenhub import TokenHubProvider
from .triposr import TripoSRProvider
from .types import GenerationRequest, GenerationResult, ProviderError, ProviderInfo

ROOT = Path(__file__).resolve().parents[3]
KIMI = KimiClient()

_PROVIDERS: dict[str, Image3DProvider] = {
    "drawing_local": DrawingProvider(),
    "mock_relief": MockReliefProvider(),
    "multiview_local": MultiViewProvider(),
    "triposr_local": TripoSRProvider(),
    "stable_fast_3d": StableFast3DProvider(),
    "tripo_cloud": TokenHubProvider("tripo"),
    "hy3d_cloud": TokenHubProvider("hy3d"),
}


def get_provider(provider_id: str) -> Image3DProvider:
    if provider_id not in _PROVIDERS:
        raise KeyError(provider_id)
    return _PROVIDERS[provider_id]


def providers() -> list[ProviderInfo]:
    out = [p.info() for p in _PROVIDERS.values()]
    out.append(ProviderInfo(
        id="kimi_analysis", label="Kimi image analysis", kind="analysis", model=KIMI.model,
        available=KIMI.available, reason=KIMI.reason,
        cost_class="low", requires_authorization=True, requires_key=True,
        output_formats=[], supports_texture=False,
        docs_url="https://platform.kimi.com/docs/guide/use-kimi-vision-model",
        license="Moonshot API terms",
    ))
    return out


def choose_auto() -> str:
    tri = _PROVIDERS["triposr_local"].info()
    return "triposr_local" if tri.available else "mock_relief"


def authorize(provider_id: str, authorized: bool, budget_cny: float) -> None:
    info = get_provider(provider_id).info()
    if info.kind == "cloud" or info.id == "kimi_analysis":
        if not authorized:
            raise ProviderError("paid provider requires explicit authorization", status="authorization_required")
        if budget_cny <= 0:
            raise ProviderError("paid provider requires a positive CNY budget", status="authorization_required")
    if info.kind == "cloud" and not info.available:
        raise ProviderError(info.reason, status="not_configured")


def run(provider_id: str, request: GenerationRequest, allow_free_fallback: bool = True) -> GenerationResult:
    if provider_id == "auto":
        provider_id = choose_auto()
    provider = get_provider(provider_id)
    provider.info()
    last: Exception | None = None
    for attempt in range(2):
        try:
            result = provider.generate(request)
            return result
        except ProviderError as exc:
            last = exc
            if exc.status in {"authorization_required", "not_configured"}:
                break
            if not exc.retryable:
                break
        except Exception as exc:  # noqa: BLE001
            last = ProviderError(str(exc), status="failed", retryable=True)
            break
    if allow_free_fallback and provider_id not in {"mock_relief"}:
        mock = _PROVIDERS["mock_relief"]
        result = mock.generate(request)
        result.metadata["fallback_from"] = provider_id
        result.metadata["fallback_reason"] = str(last)
        return result
    raise last if isinstance(last, ProviderError) else ProviderError(str(last or "provider failed"))


def analyze(image_path: str, prompt: str = "") -> dict:
    return KIMI.analyze(image_path, prompt)
