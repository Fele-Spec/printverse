"""Kimi API client for image understanding and modeling briefs.

Kimi is deliberately not used as a text-to-mesh API. This client only turns an
uploaded image into a structured analysis / prompt, or explains a mesh error.
"""
from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

import httpx

from . import config

SYSTEM = (
    "You are PrintVerse's image understanding assistant for a 3D-printable desk object. "
    "Return only a compact JSON object with keys: subject, silhouette, materials, style, "
    "suggested_prompt, print_risks, complexity_1_to_5. Do not claim to generate a mesh."
)


class KimiClient:
    def __init__(self) -> None:
        self.key = config.get("KIMI_API_KEY")
        self.base = config.get("KIMI_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
        self.model = config.get("KIMI_VISION_MODEL", "kimi-k3.1-pro")
        self.enabled = config.get("KIMI_ANALYSIS_ENABLED", "true").lower() not in {"0", "false", "no"}

    @property
    def available(self) -> bool:
        return bool(self.key) and self.enabled

    @property
    def reason(self) -> str:
        if not self.key:
            return "KIMI_API_KEY missing"
        if not self.enabled:
            return "Kimi account suspended / insufficient balance (HTTP 429); recharge and set KIMI_ANALYSIS_ENABLED=true."
        return "Kimi vision model; returns structure/prompt only, never a mesh"

    def models(self) -> list[dict]:
        if not self.key:
            return []
        with httpx.Client(timeout=30) as client:
            r = client.get(f"{self.base}/models", headers={"Authorization": f"Bearer {self.key}"})
            r.raise_for_status()
            return r.json().get("data", [])

    def analyze(self, image_path: str, prompt: str = "") -> dict:
        if not self.available:
            return {"available": False, "reason": self.reason}
        path = Path(image_path)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content = [
            {"type": "text", "text": (prompt.strip() or "Describe this object for a 3D-printable model.")},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
        ]
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": content},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        }
        with httpx.Client(timeout=90) as client:
            r = client.post(
                f"{self.base}/chat/completions",
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                json=body,
            )
            r.raise_for_status()
            data = r.json()
        text = data["choices"][0]["message"]["content"]
        parsed = None
        try:
            start = text.find("{")
            end = text.rfind("}")
            parsed = json.loads(text[start:end + 1]) if start >= 0 and end > start else None
        except Exception:
            parsed = None
        return {
            "available": True,
            "provider": "kimi",
            "model": self.model,
            "analysis": parsed,
            "raw": text,
            "usage": data.get("usage"),
            "generation_cost": None,
            "cost_note": "Kimi token cost is not converted to RMB without the account price table.",
        }

    def explain_mesh_error(self, error: str) -> dict:
        if not self.key:
            return {"available": False, "reason": "KIMI_API_KEY missing"}
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Explain a 3D-print mesh error concisely and give a repair step. Do not claim to run code."},
                {"role": "user", "content": error[:6000]},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        }
        with httpx.Client(timeout=60) as client:
            r = client.post(f"{self.base}/chat/completions",
                            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                            json=body)
            r.raise_for_status()
            data = r.json()
        return {"available": True, "text": data["choices"][0]["message"]["content"], "usage": data.get("usage"),
                "generation_cost": None, "cost_note": "Kimi token cost not converted to RMB."}
