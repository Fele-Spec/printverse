"""Load local secrets for Image-to-3D providers; never expose them to the frontend."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load_local_env() -> None:
    p = ROOT / ".env.local"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not os.environ.get(key):
            os.environ[key] = value


load_local_env()


def get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()
