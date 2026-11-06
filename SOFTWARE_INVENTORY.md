# PrintVerse Software Inventory

Generated: 2026-11-06 (Asia/Shanghai) · Project root: `C:\Users\someb\Desktop\printverse`

## Host

| Item | Value | How verified |
|---|---|---|
| OS | Windows NT 10.0.26200 (Windows 11 25H2 family) | `[Environment]::OSVersion` |
| Architecture | AMD64 / x86_64 | `$env:PROCESSOR_ARCHITECTURE`, Python `platform.machine()` |
| CPU | AMD Family 25 Model 97 Stepping 2, 32 logical processors | `$env:PROCESSOR_IDENTIFIER`, `os.cpu_count()` |
| RAM | **Total not readable** (CIM/WMI access denied); 15,279 MB available | `Get-Counter '\Memory\Available MBytes'` |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU, 8,151 MiB VRAM, driver 592.82 | `nvidia-smi` |
| Disk | 215.6 GB total, 48.0 GB free at final audit | `shutil.disk_usage()` |
| Admin | No | WindowsPrincipal check |
| Network | Node HTTPS works; PowerShell `Invoke-WebRequest`, `curl` and Git schannel fail with `SEC_E_NO_CREDENTIALS`; GitHub `api.github.com` occasionally resets | direct tests |

The sandbox blocks WMI/CIM, `systeminfo` collection and browser named pipes. RAM total is therefore reported as unavailable instead of guessed.

## Runtimes

| Tool | Version | Path |
|---|---|---|
| Python (project venv) | 3.12.10 | `.venv\Scripts\python.exe` |
| Python (system) | 3.10.0 | `D:\python\python.exe` |
| Python (Anaconda) | 3.13.5 | `D:\Anaconda3\python.exe` |
| Node.js | 24.16.0 | `D:\node.exe` |
| npm | 11.13.0 | `D:\npm.ps1` |
| Git | 2.54.0.windows.1 | `D:\Git\cmd\git.exe` |
| uv | 0.11.28 | `D:\python\Scripts\uv.exe` |
| 7zr | 26.04 | `tools\downloads\7zr.exe` |

## Desktop / engineering tools

| Tool | Version | Path | Verification |
|---|---|---|---|
| FreeCAD | 1.1.4 (build 2026-09-28, commit `4fd3bf320`) | `tools\FreeCAD-1.1.4\FreeCAD_1.1.4-Windows-x86_64-py311\` | imported STL and STEP in `FreeCADCmd` |
| Blender | 4.5.12 LTS | `tools\Blender-4.5.12\blender.exe` | headless STL import, GLB export |
| 3D Print Toolbox | 1.5.0 | `.cache\blender\extensions\user_default\print3d_toolbox` | enabled; `mesh.print3d_check_all` returned `{'FINISHED'}` |
| OrcaSlicer | 2.4.2 | `tools\OrcaSlicer-2.4.2\orca-slicer.exe` | CLI sliced `cube.stl` to 100-layer G-code and 3MF |

## Python packages (project venv)

Lock: `requirements.lock` (61 pinned distributions). Key versions:

| Package | Version |
|---|---|
| numpy | 2.5.4 |
| scipy | 1.18.1 |
| trimesh | 5.2.0 |
| meshio | 5.3.5 |
| shapely | 2.2.0 |
| pygltflib | 1.16.5 |
| manifold3d | 3.5.4 |
| rtree | 1.4.1 |
| mapbox-earcut | 2.1.0 |
| fastapi | 0.162.0 |
| pydantic | 2.14.3 |
| uvicorn | 0.54.0 |
| pytest | 9.2.0 |
| markdownify / beautifulsoup4 / lxml | 1.2.3 / 4.15.0 / 6.1.3 |
| matplotlib / pillow | 3.11.2 / 13.0.0 |

**Not installed:** `build123d`, `cadquery`, `gmsh`, `torch`, `torchmcubes`. `build123d`/`cadquery` were dropped after the PyPI download rate averaged roughly 50 KB/s (numpy alone took 4m21s); FreeCAD 1.1.4 covers the bootstrap CAD imports. This is reported as PARTIAL, not hidden.

## Node / frontend packages

Built with `frontend/package-lock.json`:

| Package | Version |
|---|---|
| react / react-dom | 19.3.1 |
| three | 0.187.0 |
| @react-three/fiber | 9.8.2 |
| @react-three/drei | 10.7.9 |
| vite | 8.3.6 |
| @vitejs/plugin-react | 6.2.1 |
| typescript | 5.9.3 |
| playwright-core | 1.65.0 (system Edge; no bundled browser) |

`gcode-preview` 2.18.0 was evaluated but not installed: its README supports `three >=0.166.0 <0.186.0`, while this project uses 0.187.0. Pin 0.185 or isolate a viewer if adopting it.

## Reproducibility

- `bootstrap.ps1` reuses existing downloads, extracts missing tools, installs the Python lock, builds profiles/docs/frontend, runs core tests and rebuilds manifests.
- `scripts/patch_vite_windows.py` applies the narrow workaround for Vite's `net use` child process being blocked by this sandbox. It changes only the installed Vite copy and is idempotent.
- `manifests/dependencies.json` contains the environment, Python lock, Python license scan and Node manifest.
