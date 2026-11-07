"""PrintVerse API package."""
import os
from pathlib import Path

# Keep optional CAD/DXF libraries from writing into the user's home cache in
# sandboxed/container deployments.
_cache = Path(__file__).resolve().parents[2] / ".cache" / "ezdxf-config"
_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CONFIG_HOME", str(_cache))
