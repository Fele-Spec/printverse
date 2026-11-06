"""Local three-view silhouette visual hull.

This is a deterministic multi-view reconstruction, not an AI model. It expects
front, side and top orthographic silhouettes of the same object on a plain
background and intersects their visual hull on a voxel grid. It is useful for
simple objects and for keeping the multi-view product path testable without a
cloud key.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageOps

from ..mesh_prep import export_bundle, repair_and_scale
from .base import Image3DProvider
from .types import GenerationRequest, GenerationResult, ProviderError, ProviderInfo

ROOT = Path(__file__).resolve().parents[3]


def _mask(path: str, n: int) -> tuple[np.ndarray, np.ndarray]:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGBA").resize((n, n), Image.Resampling.LANCZOS)
    arr = np.asarray(im, dtype=np.float32) / 255.0
    alpha = arr[..., 3]
    rgb = arr[..., :3]
    if alpha.min() > 0.98:
        # White-ish studio background; keep saturated or dark object pixels.
        chroma = rgb.max(axis=2) - rgb.min(axis=2)
        mask = (rgb.min(axis=2) < 0.90) | (chroma > 0.06)
    else:
        mask = alpha > 0.2
    if mask.mean() < 0.01:
        mask[:] = True
    return mask, rgb


def _vid(index: int, i: int, j: int, k: int) -> int:
    return index


def build_visual_hull(front_path: str, side_path: str, top_path: str, n: int = 32, span: float = 80.0) -> trimesh.Trimesh:
    front, rgb_front = _mask(front_path, n)
    side, rgb_side = _mask(side_path, n)
    top, rgb_top = _mask(top_path, n)
    # Image row 0 is top; voxel k=0 is bottom.
    front = np.flipud(front)
    side = np.flipud(side)
    top = np.flipud(top)
    rgb_front = np.flipud(rgb_front)
    rgb_side = np.flipud(rgb_side)
    rgb_top = np.flipud(rgb_top)
    inside = np.zeros((n, n, n), dtype=bool)
    for i in range(n):
        for j in range(n):
            inside[i, j, :] = front[:, i] & side[:, j] & top[j, i]
    voxels = np.argwhere(inside)
    if len(voxels) == 0:
        raise ProviderError("三视图没有交集；请使用同尺寸、同朝向的正面/侧面/顶面图片", status="failed")

    cell = span / n
    vertices: list[list[float]] = []
    colors: list[list[float]] = []
    vid: dict[tuple[int, int, int, int], int] = {}
    faces: list[list[int]] = []

    def vertex(i: int, j: int, k: int, corner: int) -> int:
        key = (i, j, k, corner)
        if key not in vid:
            x = -span / 2 + (i + (corner & 1)) * cell
            y = -span / 2 + (j + ((corner >> 1) & 1)) * cell
            z = (k + ((corner >> 2) & 1)) * cell
            vid[key] = len(vertices)
            vertices.append([x, y, z])
            # Front colour for the front half; top colour otherwise.
            c = rgb_front[min(n - 1, k), min(n - 1, i)] if i < n / 2 else rgb_top[min(n - 1, j), min(n - 1, i)]
            colors.append([float(c[0]), float(c[1]), float(c[2]), 1.0])
        return vid[key]

    # Cube corner numbering: bit0=x, bit1=y, bit2=z.
    # direction + four cube corners, emitted only when the neighbouring voxel is outside.
    sides = [
        (0, 0, -1, (0, 1, 3, 2)), (0, 0, 1, (4, 6, 7, 5)),
        (0, -1, 0, (0, 4, 5, 1)), (0, 1, 0, (2, 3, 7, 6)),
        (-1, 0, 0, (0, 2, 6, 4)), (1, 0, 0, (1, 5, 7, 3)),
    ]
    for i, j, k in voxels:
        for di, dj, dk, q in sides:
            ni, nj, nk = i + di, j + dj, k + dk
            if 0 <= ni < n and 0 <= nj < n and 0 <= nk < n and inside[ni, nj, nk]:
                continue
            faces.append([vertex(i, j, k, c) for c in q])
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=False)
    mesh.visual = trimesh.visual.ColorVisuals(vertex_colors=np.asarray(colors))
    # Remove internal/duplicate faces and make a consistently oriented shell.
    mesh.update_faces(mesh.unique_faces())
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_normals(mesh)
    if not mesh.is_watertight:
        mesh.fill_holes()
    if mesh.volume < 0:
        mesh.invert()
    return mesh


class MultiViewProvider(Image3DProvider):
    id = "multiview_local"
    model = "silhouette-visual-hull-3view"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id, label="本地三视图重建", kind="local", model=self.model,
            available=True, reason="正面/侧面/顶面轮廓视觉外壳；不是 AI 单图猜测。",
            cost_class="free", output_formats=["glb", "stl", "3mf", "obj"],
            supports_texture=True, license="PrintVerse local visual hull",
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        paths = request.options.get("image_paths") or []
        if len(paths) != 3:
            raise ProviderError("多视角需要正面、侧面、顶面 3 张图片", status="not_configured")
        try:
            mesh = build_visual_hull(*paths)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"多视角重建失败: {exc}", status="failed")
        repaired, prep = repair_and_scale(mesh, target_mm=80.0)
        job_dir = ROOT / "runtime" / "image3d" / request.job_id
        paths_out = export_bundle(repaired, job_dir, "multiview")
        return GenerationResult(
            provider=self.id, model=self.model, task_id=request.job_id,
            output_format="glb", output_url=f"/runtime/image3d/{request.job_id}/multiview.glb",
            local_path=paths_out["glb"], generation_cost=0.0, cost_basis="free",
            texture_status="VERTEX_COLOR" if getattr(repaired.visual, "kind", "") == "vertex" else "NONE",
            geometry_status="MULTIVIEW_VISUAL_HULL", task_status="completed",
            metadata={
                "views": ["front", "side", "top"], "mesh": prep,
                "stl_url": f"/runtime/image3d/{request.job_id}/multiview.stl",
                "three_mf_url": f"/runtime/image3d/{request.job_id}/multiview.3mf",
                "asset_format": "glb",
                "note": "Deterministic silhouette visual hull, not an AI reconstruction",
            },
        )
