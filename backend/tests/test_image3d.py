"""Image-to-3D architecture tests; no paid API calls."""
from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app

ROOT = Path(__file__).resolve().parents[2]


def image_bytes() -> bytes:
    im = Image.new("RGB", (256, 256), "white")
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.rectangle((60, 80, 190, 220), fill=(50, 110, 170), outline="black", width=3)
    d.ellipse((95, 40, 155, 100), fill=(220, 170, 70), outline="black", width=3)
    b = io.BytesIO(); im.save(b, format="PNG"); return b.getvalue()


def test_providers_schema():
    with TestClient(app) as client:
        r = client.get("/api/image3d/providers")
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()["providers"]}
        assert {"mock_relief", "multiview_local", "triposr_local", "stable_fast_3d", "tripo_cloud", "hy3d_cloud", "kimi_analysis"} <= ids
        mock = next(p for p in r.json()["providers"] if p["id"] == "mock_relief")
        assert mock["cost_class"] == "free" and mock["available"] is True


def test_mock_job_is_real_watertight_mesh():
    with TestClient(app) as client:
        r = client.post(
            "/api/image3d/jobs",
            files={"file": ("test.png", image_bytes(), "image/png")},
            data={"provider": "mock_relief", "prompt": "test object", "authorized": "false", "budget_cny": "0"},
        )
        assert r.status_code == 200, r.text
        job = r.json()
        assert job["provider"] == "mock_relief"
        # BackgroundTasks run asynchronously in this app; poll before checking the result.
        for _ in range(10):
            job = client.get(f"/api/image3d/jobs/{job['id']}").json()
            if job["status"] in {"completed", "failed"}:
                break
        assert job["status"] == "completed", job
        assert job["generation_cost"] == 0.0
        assert job["output_url"].endswith(".glb")
        assert job["texture_status"] == "VERTEX_COLOR"
        path = ROOT / job["local_path"]
        assert path.exists() and path.stat().st_size > 100
        stl = ROOT / job["metadata"]["stl_url"].lstrip("/")
        assert stl.exists() and stl.stat().st_size > 100
        import trimesh
        mesh = trimesh.load(path, force="mesh", process=True)
        assert len(mesh.faces) > 0
        assert mesh.is_watertight
        assert mesh.visual.kind == "vertex"


def test_paid_provider_requires_authorization():
    with TestClient(app) as client:
        r = client.post(
            "/api/image3d/jobs",
            files={"file": ("test.png", image_bytes(), "image/png")},
            data={"provider": "tripo_cloud", "prompt": "x", "authorized": "false", "budget_cny": "10"},
        )
        assert r.status_code in (402, 409)
        assert "authorization" in r.text.lower() or "not configured" in r.text.lower()


def test_unavailable_provider_is_not_silently_paid():
    with TestClient(app) as client:
        r = client.post(
            "/api/image3d/jobs",
            files={"file": ("test.png", image_bytes(), "image/png")},
            data={"provider": "stable_fast_3d", "prompt": "x", "authorized": "true", "budget_cny": "10"},
        )
        assert r.status_code in (402, 409)
        assert "Windows" in r.text or "not configured" in r.text
