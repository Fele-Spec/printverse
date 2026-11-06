"""Combine per-part FreeCAD STL meshes into modular glTF binaries.

Scene units: metres. The source STLs are in millimetres and already carry the
FreeCAD global placement; each mesh is scaled exactly once by 0.001.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "manifests/module-parts.json"
OUT = ROOT / "assets/models/voron/modules"
PUBLIC = ROOT / "frontend/public/models/voron/modules"
MANIFEST = ROOT / "CAD_MODULE_MANIFEST.json"
RANGES = ROOT / "frontend/public/models/voron/module-face-ranges.json"
LOD_RANGES = ROOT / "frontend/public/models/voron/module-face-ranges-lod.json"
INSTANCED_IDS = ROOT / "frontend/public/models/voron/instanced-ids.json"


def main() -> int:
    groups = json.loads(PARTS.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    skip_ids = set(json.loads(INSTANCED_IDS.read_text(encoding="utf-8"))) if INSTANCED_IDS.exists() else set()
    manifest = {"unit": "m", "source_unit": "mm", "scale_factor": 0.001, "modules": {}}
    all_ranges = {}
    lod_ranges = {}
    for module, parts in sorted(groups.items()):
        if not parts:
            continue
        scene = trimesh.Scene()
        meshes = []
        lod_meshes = []
        ranges = []
        lod_part_ranges = []
        faces = 0
        cursor = 0
        lod_cursor = 0
        for p in parts:
            path = ROOT / p["mesh_file"]
            if not path.exists():
                continue
            mesh = trimesh.load(path, force="mesh", process=True)
            if mesh.is_empty:
                continue
            mesh.apply_scale(0.001)
            meshes.append(mesh)
            ranges.append({"placement_id": p["placement_id"], "part_name": p["part_name"], "start": cursor, "count": len(mesh.faces)})
            cursor += len(mesh.faces)
            lod_mesh = mesh
            if len(mesh.faces) >= 120:
                try:
                    simplified = mesh.simplify_quadric_decimation(0.82)
                    if simplified is not None and not simplified.is_empty and len(simplified.faces) > 20:
                        lod_mesh = simplified
                except Exception:
                    lod_mesh = mesh
            if p["placement_id"] not in skip_ids:
                lod_meshes.append(lod_mesh)
                lod_part_ranges.append({"placement_id": p["placement_id"], "part_name": p["part_name"], "start": lod_cursor, "count": len(lod_mesh.faces)})
                lod_cursor += len(lod_mesh.faces)
            scene.add_geometry(
                mesh,
                node_name=p["placement_id"],
                geom_name=p["placement_id"],
                metadata={
                    "placement_id": p["placement_id"],
                    "part_name": p["part_name"],
                    "path": p["path"],
                    "module": module,
                    "source_unit": "mm",
                    "faces": len(mesh.faces),
                },
            )
            faces += len(mesh.faces)
        if not scene.geometry:
            continue
        target = OUT / f"{module}.glb"
        scene.export(target, file_type="glb")
        shutil.copy2(target, PUBLIC / target.name)
        bounds = scene.bounds

        merged = trimesh.util.concatenate(meshes) if meshes else None
        merged_target = OUT / f"{module}.merged.glb"
        if merged is not None and not merged.is_empty:
            merged.export(merged_target, file_type="glb")
            shutil.copy2(merged_target, PUBLIC / merged_target.name)
            merged_bytes = merged_target.stat().st_size
            merged_faces = len(merged.faces)
            all_ranges[module] = ranges
        else:
            merged_bytes = 0
            merged_faces = 0

        lod = trimesh.util.concatenate(lod_meshes) if lod_meshes else None
        lod_target = OUT / f"{module}.lod.glb"
        if lod is not None and not lod.is_empty:
            lod.export(lod_target, file_type="glb")
            shutil.copy2(lod_target, PUBLIC / lod_target.name)
            lod_bytes = lod_target.stat().st_size
            lod_faces = len(lod.faces)
            lod_ranges[module] = lod_part_ranges
        else:
            lod_bytes = 0
            lod_faces = 0
        manifest["modules"][module] = {
            "file": f"assets/models/voron/modules/{module}.glb",
            "public_file": f"frontend/public/models/voron/modules/{module}.glb",
            "render_file": f"frontend/public/models/voron/modules/{module}.lod.glb",
            "bytes": target.stat().st_size,
            "merged_bytes": merged_bytes,
            "lod_bytes": lod_bytes,
            "parts": len(scene.geometry),
            "faces": faces,
            "merged_faces": merged_faces,
            "lod_faces": lod_faces,
            "bounds_m": bounds.tolist() if bounds is not None else None,
        }
        print(module, "parts", len(scene.geometry), "faces", faces, "lod", lod_faces, lod_bytes, flush=True)
    RANGES.write_text(json.dumps(all_ranges, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    LOD_RANGES.write_text(json.dumps(lod_ranges, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TOTAL_BYTES", sum(m["bytes"] for m in manifest["modules"].values()))
    print("TOTAL_PARTS", sum(m["parts"] for m in manifest["modules"].values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
