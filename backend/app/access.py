"""Identity for local vs shared deployments.

Default mode preserves the single-user demo. With PRINTVERSE_SHARE_MODE=1:
  loopback  -> owner (admin, unlimited)
  remote    -> guest (limited wallet, no first-print-free)
This is deliberately not a password login; put it behind Tailscale/Cloudflare
Access or a trusted reverse proxy before public exposure.
"""
from __future__ import annotations

import os
from fastapi import HTTPException, Request

DEMO = "demo"
OWNER = "owner"
GUEST = "guest"
LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


def share_mode() -> bool:
    return os.environ.get("PRINTVERSE_SHARE_MODE", "0").lower() in {"1", "true", "yes", "on"}


def resolve_user(request: Request) -> str:
    if not share_mode():
        return DEMO
    host = request.client.host if request.client else ""
    if host in LOOPBACK:
        return OWNER
    token = request.headers.get("X-PV-Member", "")
    required = os.environ.get("PV_GUEST_TOKEN", "")
    if required and token != required:
        raise HTTPException(401, "member token required")
    return GUEST


def public_status(request: Request) -> dict:
    user = resolve_user(request)
    return {
        "mode": "shared" if share_mode() else "local-demo",
        "user": user,
        "unlimited": user == OWNER,
        "note": "owner is loopback-only in shared mode; remote clients receive the guest wallet",
    }
