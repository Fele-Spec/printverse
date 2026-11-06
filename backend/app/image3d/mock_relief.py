"""Free local fallback: a printable heightfield relief, explicitly not a 3D reconstruction."""
from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageOps

from .base import Image3DProvider
from .types import GenerationRequest, GenerationResult, ProviderInfo

ROOT = Path(__file__).resolve().parents[3]


class MockReliefProvider(Image3DProvider):
    id = "mock_relief"
    model = "silhouette-heightfield-v1"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id, label="Mock relief (free, printable)", kind="local", model=self.model,
            available=True, cost_class="free", output_formats=["stl"],
            supports_texture=False, license="PrintVerse local fallback",
            reason="Not image-to-3D reconstruction; a heightfield/silhouette relief for pipeline testing.",
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        job_dir = ROOT / "runtime" / "image3d" / request.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        out = job_dir / "mock_relief.stl"
        source = Image.open(request.image_path).convert("RGBA")
        source = ImageOps.exif_transpose(source).resize((160, 160))
        rgba = np.asarray(source, dtype=np.float32) / 255.0
        alpha = rgba[..., 3]
        # If the image has no meaningful alpha, use a simple luminance silhouette.
        if alpha.min() > 0.98:
            mask = (rgba[..., :3].mean(axis=2) < 0.92).astype(np.float32)
        else:
            mask = (alpha > 0.2).astype(np.float32)
        if mask.mean() < 0.01:
            mask[:] = 1.0
        gray = rgba[..., :3].mean(axis=2)
        # Background is flat; foreground is raised. This is a relief, not a volumetric guess.
        height = (1.0 - gray) * 14.0 * mask
        # Downsample for a predictable STL size.
        from PIL import Image as PImage
        hi = PImage.fromarray(np.uint8(np.clip(height / 14.0, 0, 1) * 255)).resize((72, 72), PImage.Resampling.LANCZOS)
        h = np.asarray(hi, dtype=np.float32) / 255.0 * 14.0
        h = np.pad(h, 1, mode="constant")
        n = h.shape[0]
        span = 80.0
        xs = np.linspace(-span / 2, span / 2, n)
        ys = np.linspace(-span / 2, span / 2, n)
        X, Y = np.meshgrid(xs, ys)
        top = np.stack([X, Y, h + 0.6], axis=-1).reshape(-1, 3)
        bottom = np.stack([X, Y, np.zeros_like(h)], axis=-1).reshape(-1, 3)
        vertices = np.vstack([top, bottom])
        top_idx = np.arange(n * n).reshape(n, n)
        bot_idx = top_idx + n * n
        faces: list[list[int]] = []
        for y in range(n - 1):
            for x in range(n - 1):
                a, b, c, d = top_idx[y, x], top_idx[y, x + 1], top_idx[y + 1, x], top_idx[y + 1, x + 1]
                faces += [[a, b, d], [a, d, c]]
                a, b, c, d = bot_idx[y, x], bot_idx[y, x + 1], bot_idx[y + 1, x], bot_idx[y + 1, x + 1]
                faces += [[a, d, b], [a, c, d]]
        # Explicit perimeter wall quads from grid perimeter.
        perim = []
        perim += [(0, x) for x in range(n - 1)]
        perim += [(y, n - 1) for y in range(n - 1)]
        perim += [(n - 1, x) for x in range(n - 1, 0, -1)]
        perim += [(y, 0) for y in range(n - 1, 0, -1)]
        for i in range(len(perim)):
            y1, x1 = perim[i]
            y2, x2 = perim[(i + 1) % len(perim)]
            t1, t2 = top_idx[y1, x1], top_idx[y2, x2]
            b1, b2 = bot_idx[y1, x1], bot_idx[y2, x2]
            faces += [[t1, b2, b1], [t1, t2, b2]]
        mesh = trimesh.Trimesh(vertices=vertices, faces=np.asarray(faces, dtype=np.int64), process=True)
        mesh.export(out)
        return GenerationResult(
            provider=self.id, model=self.model, task_id=request.job_id,
            output_format="stl", output_url=f"/runtime/image3d/{request.job_id}/mock_relief.stl",
            local_path=str(out.relative_to(ROOT)).replace("\\", "/"),
            generation_cost=0.0, cost_basis="free", texture_status="NONE",
            geometry_status="MOCK_RELIEF", task_status="completed",
            metadata={"note": "Heightfield relief, not image-to-3D reconstruction", "watertight": bool(mesh.is_watertight)},
        )
