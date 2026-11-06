"""Run TripoSR in its isolated venv and emit a mesh + JSON metrics.

Invoked by backend/app/image3d/triposr.py. This avoids touching the main
build123d/CadQuery venv.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / ".cache" / "triposr-src" / "TripoSR-main"
sys.path.insert(0, str(REPO))

# CPU fallback for torchmcubes. It is slower but avoids a Windows CUDA build.
try:
    import torchmcubes  # noqa: F401
except Exception:
    import types
    import mcubes
    shim = types.ModuleType("torchmcubes")

    def marching_cubes(volume, level=0.0):
        v, f = mcubes.marching_cubes(volume.detach().cpu().numpy(), float(level))
        return torch.from_numpy(v).float(), torch.from_numpy(f).long()

    shim.marching_cubes = marching_cubes
    sys.modules["torchmcubes"] = shim

# rembg is imported by tsr.utils but we do not use background removal for these
# controlled benchmark images. Avoid downloading its ONNX stack just for import.
try:
    import rembg  # noqa: F401
except Exception:
    rembg_shim = types.ModuleType("rembg")
    rembg_shim.remove = lambda image, *args, **kwargs: image
    sys.modules["rembg"] = rembg_shim

# TripoSR only downloads the DINO config at construction; the actual ViT weights
# are inside model.ckpt. Avoid a Hub metadata call by serving the local config.
import huggingface_hub as _hf  # noqa: E402
_orig_hf = _hf.hf_hub_download
_dino_config = Path(__file__).resolve().parents[1] / ".cache" / "TripoSR" / "dino_config.json"

def _local_hf(repo_id, filename, *args, **kwargs):
    if repo_id == "facebook/dino-vitb16" and filename == "config.json" and _dino_config.exists():
        return str(_dino_config)
    return _orig_hf(repo_id, filename, *args, **kwargs)

_hf.hf_hub_download = _local_hf

from tsr.system import TSR  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model-dir", default=str(ROOT / ".cache" / "TripoSR"))
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--resolution", type=int, default=192)
    args = ap.parse_args()
    start = time.time()
    device = args.device if torch.cuda.is_available() else "cpu"
    image = Image.open(args.image).convert("RGBA")
    if image.getextrema()[3][0] < 255:
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        image = Image.alpha_composite(background, image)
    image = image.convert("RGB")
    model = TSR.from_pretrained(args.model_dir, "config.yaml", "model.ckpt")
    model.renderer.set_chunk_size(8192)
    model.to(device)
    model.eval()
    with torch.no_grad():
        codes = model([image], device)
        meshes = model.extract_mesh(codes, True, resolution=args.resolution)
    mesh = meshes[0]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out)
    result = {
        "ok": True,
        "device": device,
        "seconds": round(time.time() - start, 2),
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "output": str(out),
        "cuda_peak_mb": int(torch.cuda.max_memory_allocated() / 1024 / 1024) if torch.cuda.is_available() else 0,
    }
    print("TRIPOSR_RESULT " + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
