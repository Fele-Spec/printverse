"""Shared-mode identity tests: owner is loopback/admin, remote is guest/quota."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_shared_mode_owner_and_guest(monkeypatch):
    monkeypatch.setenv("PRINTVERSE_SHARE_MODE", "1")
    with TestClient(app, client=("127.0.0.1", 50000)) as local:
        a = local.get("/api/access").json()
        assert a["mode"] == "shared" and a["user"] == "owner" and a["unlimited"] is True
        w = local.get("/api/wallet").json()
        assert w["role"] == "admin"
    with TestClient(app, client=("192.168.1.20", 50001)) as remote:
        a = remote.get("/api/access").json()
        assert a["user"] == "guest" and a["unlimited"] is False
        w = remote.get("/api/wallet").json()
        assert w["role"] == "user"
        assert w["balance_g"] == 20.0
        assert w["first_print_available"] is False


def test_shared_mode_can_require_guest_token(monkeypatch):
    monkeypatch.setenv("PRINTVERSE_SHARE_MODE", "1")
    monkeypatch.setenv("PV_GUEST_TOKEN", "invite-123")
    with TestClient(app, client=("192.168.1.21", 50002)) as remote:
        r = remote.get("/api/wallet")
        assert r.status_code == 401
        r = remote.get("/api/wallet", headers={"X-PV-Member": "invite-123"})
        assert r.status_code == 200
