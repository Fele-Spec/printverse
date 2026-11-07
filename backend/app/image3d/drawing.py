"""Raster engineering-drawing import: closed ink contours -> 2.5D extrusion.

This is an intentionally simple deterministic drawing-to-CAD mesh path. It does
not infer dimensions, constraints, holes or parametric features from the image.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

from ..mesh_prep import export_bundle, inspect_mesh
from .base import Image3DProvider
from .types import GenerationRequest, GenerationResult, ProviderError, ProviderInfo

ROOT = Path(__file__).resolve().parents[3]


class DrawingProvider(Image3DProvider):
    id = "drawing_local"
    model = "raster-contour-extrude"

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id, label="工程图拉伸（本地）", kind="local", model=self.model,
            available=True,
            reason="识别深色封闭轮廓并拉伸为 2.5D 网格；不推断尺寸/约束/孔，不是参数化 CAD。",
            cost_class="free", output_formats=["glb", "stl", "3mf", "obj"],
            supports_texture=True, license="PrintVerse local OpenCV contour extrusion",
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            image = cv2.imread(request.image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError("cannot read image")
            # Dark ink on light paper; invert so ink becomes foreground.
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h, w = image.shape[:2]
            polys = []
            for contour in contours:
                if cv2.contourArea(contour) < max(50, w * h * 0.0002):
                    continue
                approx = cv2.approxPolyDP(contour, 0.002 * cv2.arcLength(contour, True), True)
                pts = [(float(p[0][0]), float(h - p[0][1])) for p in approx]
                if len(pts) >= 3:
                    poly = Polygon(pts).buffer(0)
                    if poly.is_valid and poly.area > 0:
                        polys.append(poly)
            if not polys:
                raise ValueError("no closed dark contour found")
            merged = unary_union(polys)
            max_dim = max(merged.bounds[2] - merged.bounds[0], merged.bounds[3] - merged.bounds[1])
            target_mm = float(request.options.get("width_mm", 80.0))
            scale = target_mm / max_dim if max_dim > 0 else 1.0
            from shapely.affinity import scale as shapely_scale
            merged = shapely_scale(merged, xfact=scale, yfact=scale, origin=(0, 0))
            height_mm = float(request.options.get("height_mm", 3.0))
            mesh = trimesh.creation.extrude_polygon(merged, height=height_mm)
            mesh.visual.face_colors = np.tile(np.array([[188, 201, 208, 255]], dtype=np.uint8), (len(mesh.faces), 1))
            job_dir = ROOT / "runtime" / "image3d" / request.job_id
            paths = export_bundle(mesh, job_dir, "drawing")
            return GenerationResult(
                provider=self.id, model=self.model, task_id=request.job_id,
                output_format="glb", output_url=f"/runtime/image3d/{request.job_id}/drawing.glb",
                local_path=paths["glb"], generation_cost=0.0, cost_basis="free",
                texture_status="FACE_COLOR", geometry_status="DRAWING_EXTRUDE", task_status="completed",
                metadata={
                    "contours": len(polys), "scale": round(scale, 6), "target_mm": target_mm,
                    "height_mm": height_mm, "mesh": inspect_mesh(mesh),
                    "stl_url": f"/runtime/image3d/{request.job_id}/drawing.stl",
                    "three_mf_url": f"/runtime/image3d/{request.job_id}/drawing.3mf",
                    "obj_url": f"/runtime/image3d/{request.job_id}/drawing.obj",
                    "asset_format": "glb",
                    "note": "Raster contour extrusion; dimensions/constraints are NOT inferred",
                },
            )
        except Exception as exc:
            raise ProviderError(f"工程图拉伸失败: {exc}", status="failed")
