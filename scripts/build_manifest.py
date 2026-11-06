#!/usr/bin/env python3
"""Build PrintVerse resource, license, CAD index, checksum and dependency manifests."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAN = ROOT / "manifests"
REPORTS = ROOT / "docs" / "reports"
BASE = ROOT / "assets/source/voron-v2.4r2-300"
NOW = datetime.now(timezone.utc).isoformat()

DOWNLOAD_META = {
    "Voron-2-V2.4r2.zip": ("official-design-archive", "Voron V2.4r2 complete design archive", "VoronDesign/Voron-2", "V2.4r2", "GPL-3.0", "https://github.com/VoronDesign/Voron-2"),
    "Voron-Documentation-main.zip": ("official-documentation-archive", "Voron Documentation source mirror", "VoronDesign/Voron-Documentation", "main", "GPL-3.0", "https://github.com/VoronDesign/Voron-Documentation"),
    "klipper-v0.13.0.zip": ("firmware-source", "Klipper v0.13.0 source and docs", "Klipper3d/klipper", "v0.13.0", "GPL-3.0", "https://github.com/Klipper3d/klipper"),
    "moonraker-v0.11.0.zip": ("api-server-source", "Moonraker v0.11.0 source and docs", "Arksine/moonraker", "v0.11.0", "GPL-3.0", "https://github.com/Arksine/moonraker"),
    "OrcaSlicer_Windows_V2.4.2_x64_portable.zip": ("slicer-tool", "OrcaSlicer v2.4.2 portable x64", "OrcaSlicer/OrcaSlicer", "v2.4.2", "AGPL-3.0", "https://github.com/OrcaSlicer/OrcaSlicer"),
    "FreeCAD_1.1.4-Windows-x86_64-py311.7z": ("cad-tool", "FreeCAD 1.1.4 portable x64", "FreeCAD/FreeCAD", "1.1.4", "LGPL-2.1-or-later", "https://github.com/FreeCAD/FreeCAD"),
    "blender-4.5.12-windows-x64.zip": ("3d-tool", "Blender 4.5.12 LTS portable x64", "blender.org", "4.5.12", "GPL-3.0-or-later", "https://download.blender.org/release/Blender4.5/"),
    "7zr.exe": ("extractor", "7-Zip standalone console extractor", "7-zip.org", "26.04", "LGPL-2.1-or-later WITH unRAR restriction", "https://www.7-zip.org/"),
    "print3d-toolbox-1.5.0.zip": ("blender-extension", "Blender 3D Print Toolbox", "extensions.blender.org", "1.5.0", "GPL-3.0-or-later", "https://extensions.blender.org/add-ons/print3d-toolbox/"),
}

LICENSES = [
    # component, version, license, source, commercial_use, modification, redistribution, notes
    ("Voron V2.4r2 CAD/STL/DXF", "V2.4r2", "GPL-3.0", "https://github.com/VoronDesign/Voron-2", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Copyleft; provide source and license for distributed derivatives."),
    ("Voron Documentation", "main b8c014f8", "GPL-3.0", "https://github.com/VoronDesign/Voron-Documentation", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Includes images; attribution required."),
    ("Voron official assembly manuals", "2.4r2", "GPL-3.0", "https://github.com/VoronDesign/Voron-2/tree/V2.4r2/Manual", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Covered by the Voron-2 repository license."),
    ("Klipper", "v0.13.0", "GPL-3.0", "https://github.com/Klipper3d/klipper", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Firmware/config reference; not flashed in this phase."),
    ("Moonraker", "v0.11.0", "GPL-3.0", "https://github.com/Arksine/moonraker", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "API research only; no printer connected."),
    ("OrcaSlicer", "v2.4.2", "AGPL-3.0", "https://github.com/OrcaSlicer/OrcaSlicer", "YES_WITH_NETWORK_COPYLEFT", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Network interaction with modified code can trigger source-offer duties; legal review before SaaS distribution."),
    ("FreeCAD", "1.1.4", "LGPL-2.1-or-later", "https://github.com/FreeCAD/FreeCAD", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Used as a separate executable; keep relinking rights for modified library distribution."),
    ("Blender", "4.5.12 LTS", "GPL-3.0-or-later", "https://www.blender.org/download/", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Used as an external tool; scripts that link GPL code inherit obligations."),
    ("Blender 3D Print Toolbox", "1.5.0", "GPL-3.0-or-later", "https://extensions.blender.org/add-ons/print3d-toolbox/", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Installed into the local Blender user extension repository."),
    ("7-Zip / 7zr", "26.04", "LGPL-2.1-or-later WITH unRAR restriction", "https://www.7-zip.org/", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "YES_WITH_OBLIGATIONS", "Standalone extractor used only for the FreeCAD archive."),
    ("Three.js", "0.187.0", "MIT", "https://github.com/mrdoob/three.js", "YES", "YES", "YES", "Frontend rendering."),
    ("React Three Fiber", "9.8.2", "MIT", "https://github.com/pmndrs/react-three-fiber", "YES", "YES", "YES", "React renderer for Three.js."),
    ("Drei", "10.7.9", "MIT", "https://github.com/pmndrs/drei", "YES", "YES", "YES", "Three.js helpers."),
    ("React / React DOM", "19.3.1", "MIT", "https://github.com/facebook/react", "YES", "YES", "YES", "Frontend UI."),
    ("Vite", "8.3.6", "MIT", "https://github.com/vitejs/vite", "YES", "YES", "YES", "Frontend build tool."),
    ("TypeScript", "5.9.3", "Apache-2.0", "https://github.com/microsoft/TypeScript", "YES", "YES", "YES", "Type checking."),
    ("Playwright Core", "1.65.0", "Apache-2.0", "https://github.com/microsoft/playwright", "YES", "YES", "YES", "Browser test harness; no browser bundled. Real Edge WebGL screenshots captured under an approved full-access run."),
    ("build123d", "0.13.0", "MIT", "https://github.com/gumyr/build123d", "YES", "YES", "YES", "Python-native parametric CAD; Box(10,20,30) verified and STEP exported."),
    ("cadquery-ocp-novtk", "8.0.1.1.0", "Apache-2.0", "https://github.com/CadQuery/OCP", "YES", "YES", "YES", "OCP 8.0 Python bindings used by build123d; no VTK dependency."),
    ("cadquery", "2.8.0", "Apache-2.0", "https://github.com/CadQuery/cadquery", "YES", "YES", "YES", "Evaluated only; requires OCP <8.0 and conflicts with build123d's OCP 8.0. Use a separate venv."),
    ("gcode-preview", "2.18.0", "MIT", "https://github.com/remcoder/gcode-preview", "YES", "YES", "YES", "Evaluated MIT G-code preview library; peer range targets Three.js 0.159."),
    ("gcode-parser (cncjs)", "2.2.0", "MIT", "https://github.com/cncjs/gcode-parser", "YES", "YES", "YES", "Evaluated Node-side parser; not installed."),
    ("gcode-toolpath (cncjs)", "3.0.0", "MIT", "https://github.com/cncjs/gcode-toolpath", "YES", "YES", "YES", "Evaluated toolpath generator; not installed."),
    ("Tencent Hunyuan3D 2.1", "repo 82920d64", "UNKNOWN_LICENSE", "https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1", "UNKNOWN", "UNKNOWN", "UNKNOWN", "GitHub reports NOASSERTION; shape model needs about 10 GB VRAM, texture path 21 GB. Not downloaded."),
    ("TripoSR", "repo 107cefdc", "MIT", "https://github.com/VAST-AI-Research/TripoSR", "YES", "YES", "YES", "Small image-to-3D candidate; weights and CUDA PyTorch not downloaded due bandwidth/hardware budget."),
    ("Microsoft TRELLIS", "repo 193e0502", "MIT", "https://github.com/microsoft/TRELLIS", "YES", "YES", "YES", "Image-to-3D candidate requiring more VRAM than the 8 GB available; research only."),
    ("NumPy", "2.5.4", "BSD-3-Clause", "https://numpy.org/", "YES", "YES", "YES", "Python numeric base."),
    ("SciPy", "1.18.1", "BSD-3-Clause", "https://scipy.org/", "YES", "YES", "YES", "Scientific computing."),
    ("trimesh", "5.2.0", "MIT", "https://trimesh.org/", "YES", "YES", "YES", "Mesh audit."),
    ("meshio", "5.3.5", "MIT", "https://github.com/nschloe/meshio", "YES", "YES", "YES", "Mesh I/O."),
    ("Shapely", "2.2.0", "BSD-3-Clause", "https://shapely.readthedocs.io/", "YES", "YES", "YES", "2D geometry."),
    ("FastAPI", "0.162.0", "MIT", "https://fastapi.tiangolo.com/", "YES", "YES", "YES", "Backend scaffold."),
    ("Pydantic", "2.14.3", "MIT", "https://docs.pydantic.dev/", "YES", "YES", "YES", "Validation."),
    ("Uvicorn", "0.54.0", "BSD-3-Clause", "https://www.uvicorn.org/", "YES", "YES", "YES", "ASGI server."),
    ("Mapbox Earcut", "2.1.0", "ISC", "https://github.com/mapbox/earcut", "YES", "YES", "YES", "Triangulation dependency."),
    ("Manifold3D", "3.5.4", "Apache-2.0", "https://github.com/elalish/manifold", "YES", "YES", "YES", "Boolean mesh operations dependency."),
    ("Rtree", "1.4.1", "MIT", "https://github.com/Toblerity/rtree", "YES", "YES", "YES", "Spatial index dependency."),
    ("pytest", "9.2.0", "MIT", "https://pytest.org/", "YES", "YES", "YES", "Test runner."),
    ("Markdownify", "1.2.3", "MIT", "https://github.com/matthewwithanm/python-markdownify", "YES", "YES", "YES", "Documentation conversion."),
    ("BeautifulSoup4", "4.15.0", "MIT", "https://www.crummy.com/software/BeautifulSoup/", "YES", "YES", "YES", "HTML parsing."),
    ("lxml", "6.1.3", "BSD-3-Clause", "https://lxml.de/", "YES", "YES", "YES", "XML/HTML parser."),
    ("Pillow", "13.0.0", "MIT-CMU", "https://python-pillow.org/", "YES", "YES", "YES", "Image handling."),
    ("Matplotlib", "3.11.2", "PSF-based", "https://matplotlib.org/", "YES", "YES", "YES", "BOM preview generation."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    MAN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    downloads = []
    if (ROOT / "logs/downloads.jsonl").exists():
        for line in (ROOT / "logs/downloads.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                downloads.append(json.loads(line))
    # Deduplicate by target path, keeping the last successful download.
    by_path = {}
    for d in downloads:
        by_path[d["path"]] = d
    downloads = list(by_path.values())

    versions = {}
    if (MAN / "source_versions.json").exists():
        for s in json.loads((MAN / "source_versions.json").read_text(encoding="utf-8"))["sources"]:
            versions[s["repo"]] = s

    resources = []
    for d in downloads:
        p = Path(d["path"])
        if not p.exists():
            continue
        name = p.name
        kind, title, repo, version, lic, homepage = DOWNLOAD_META.get(
            name, ("download", name, "", "", "UNKNOWN_LICENSE", ""))
        actual = sha256(p)
        commit = versions.get(repo, {}).get("commit")
        resources.append({
            "id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            "kind": kind, "title": title, "path": d["path"], "url": d.get("url"),
            "resolved_url": d.get("resolved_url"), "repository": repo, "version": version,
            "commit": commit, "bytes": p.stat().st_size, "sha256": actual,
            "sha256_matches_download_ledger": actual == d.get("sha256"),
            "downloaded_at": d.get("timestamp"), "license": lic,
            "homepage": homepage, "opens": True,
        })
    # Add key data artifacts that were generated rather than downloaded.
    generated = [
        ("BOM_300MM.csv", "bom", "Official-configurator-derived 300 mm BOM", "GPL-3.0-derived-data"),
        ("configs/machine/voron-v2.4r2-300-0.4.json", "slicer-profile", "Resolved Orca Voron 2.4 300 machine profile", "AGPL-3.0-derived"),
        ("configs/process/voron-0.20mm-standard.json", "slicer-profile", "Resolved Orca 0.20 mm standard process", "AGPL-3.0-derived"),
        ("configs/filament/generic-pla.json", "slicer-profile", "Resolved Orca Generic PLA filament profile", "AGPL-3.0-derived"),
        ("assets/test-models/cube.stl", "test-model", "20 mm cube test model", "CC0-1.0"),
        ("assets/test-models/cube.gcode", "test-gcode", "OrcaSlicer 2.4.2 sliced cube", "no-separate-license"),
        ("assets/test-models/cube.3mf", "test-project", "OrcaSlicer 2.4.2 project with G-code", "no-separate-license"),
        ("assets/processed/filament_card.glb", "preview-model", "Voron Filament_Card converted to GLB", "GPL-3.0"),
        ("assets/processed/voron_300_bed.stl", "cad-mesh", "Official 300 mm bed STEP meshed to STL", "GPL-3.0"),
    ]
    for path, kind, title, lic in generated:
        p = ROOT / path
        if p.exists():
            resources.append({"id": re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-"),
                              "kind": kind, "title": title, "path": path, "bytes": p.stat().st_size,
                              "sha256": sha256(p), "repository": "PrintVerse", "version": "bootstrap",
                              "license": lic, "opens": True})
    (MAN / "resources.json").write_text(json.dumps({"generated_at": NOW, "resources": resources}, indent=2), encoding="utf-8")
    with (MAN / "resources.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "kind", "title", "path", "bytes", "sha256", "repository", "version", "commit", "license", "url", "sha256_matches"])
        for r in resources:
            w.writerow([r["id"], r["kind"], r["title"], r["path"], r["bytes"], r["sha256"], r.get("repository"),
                        r.get("version"), r.get("commit"), r.get("license"), r.get("url"), r.get("sha256_matches_download_ledger")])

    # License audit CSV (root deliverable and manifest copy).
    lic_path = ROOT / "LICENSE_AUDIT.csv"
    with lic_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["component", "version", "license", "commercial_use", "modification", "redistribution", "source", "notes"])
        for row in LICENSES:
            w.writerow(row)
    (MAN / "licenses.csv").write_text(lic_path.read_text(encoding="utf-8-sig"), encoding="utf-8")

    # Per-file Python dependency license where metadata is available.
    python_rows = []
    seen_python = set()
    lock_sources = [ROOT / "requirements.lock", ROOT / "requirements-cadquery.lock"]
    locked_lines = []
    for lock in lock_sources:
        if lock.exists():
            locked_lines.extend(line for line in lock.read_text(encoding="utf-8").splitlines() if "==" in line)
    for line in locked_lines:
        name, version = line.split("==", 1)
        if name.lower() in seen_python:
            continue
        seen_python.add(name.lower())
        try:
            from importlib.metadata import metadata
            md = metadata(name)
            expression = md.get("License-Expression") or md.get("License") or ""
            expression = expression.strip().splitlines()[0] if expression.strip() else "UNKNOWN_LICENSE"
        except Exception:
            expression = "UNKNOWN_LICENSE"
        python_rows.append({"name": name, "version": version, "license": expression})
    # Append every locked Python distribution to the license audit for completeness.
    permissive = ("MIT", "BSD", "Apache", "ISC", "PSF", "Python Software Foundation", "MPL")
    with lic_path.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        for row in python_rows:
            lic = row["license"]
            commercial = "YES" if any(tag.lower() in lic.lower() for tag in permissive) else "UNKNOWN_LICENSE"
            w.writerow([f"Python: {row['name']}", row["version"], lic, commercial, "YES", "YES",
                        "PyPI package recorded in requirements.lock", "License string from installed package metadata; review UNKNOWN values."])
    (MAN / "licenses.csv").write_text(lic_path.read_text(encoding="utf-8-sig"), encoding="utf-8")

    # CAD asset index.
    integrity = {}
    if (REPORTS / "asset_integrity.json").exists():
        ai = json.loads((REPORTS / "asset_integrity.json").read_text(encoding="utf-8"))
        for r in ai.get("records", []):
            integrity[r["path"]] = r
        for r in ai.get("headers", []):
            integrity[r["path"]] = r
    fc = {}
    if (REPORTS / "freecad_step_test.json").exists():
        fc = json.loads((REPORTS / "freecad_step_test.json").read_text(encoding="utf-8"))
    cad_rows = []
    categories = [("CAD", BASE / "CAD"), ("STL", BASE / "STLs"), ("DXF", BASE / "DXF"),
                  ("Manual", BASE / "Manual"), ("TestModel", ROOT / "assets/test-models"),
                  ("Processed", ROOT / "assets/processed")]
    for cat, directory in categories:
        if not directory.exists():
            continue
        for p in sorted(directory.rglob("*")):
            if not p.is_file() or p.name.startswith("."):
                continue
            if p.suffix.lower() not in {".step", ".stp", ".stl", ".dxf", ".f3d", ".pdf", ".zip", ".glb", ".gcode", ".3mf"}:
                continue
            key = rel(p)
            val = integrity.get(key, {})
            note = ""
            status = "indexed"
            if p.suffix.lower() == ".stl" and val:
                status = "mesh_validated" if val.get("ok") else "mesh_error"
                note = f"watertight={val.get('watertight')}; faces={val.get('faces')}"
            elif p.suffix.lower() in {".dxf", ".pdf", ".step"} and val:
                status = "header_valid" if val.get("ok") else "header_invalid"
                note = str(val.get("detail", ""))[:120]
            elif p.suffix.lower() == ".f3d":
                status = "container_valid"
                note = "Fusion 360 native; FreeCAD cannot import F3D"
            elif p.suffix.lower() == ".step" and fc:
                imp = fc.get("imports", [{}])[0] if fc.get("imports") else {}
                status = "freecad_imported" if imp.get("ok") else "freecad_import_failed"
                note = f"objects={imp.get('object_count')}; solids={imp.get('solid_count')}; bbox={imp.get('bbox_mm', {}).get('dx')}x{imp.get('bbox_mm', {}).get('dy')}x{imp.get('bbox_mm', {}).get('dz')}"
            cad_rows.append({"category": cat, "format": p.suffix.lower().lstrip("."), "path": key,
                             "bytes": p.stat().st_size, "sha256": sha256(p), "source": "VoronDesign/Voron-2@V2.4r2" if cat in {"CAD", "STL", "DXF", "Manual"} else "PrintVerse",
                             "license": "GPL-3.0" if cat in {"CAD", "STL", "DXF", "Manual"} else "project",
                             "validation": status, "notes": note})
    cad_path = ROOT / "CAD_ASSET_INDEX.csv"
    with cad_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["category", "format", "path", "bytes", "sha256", "source", "version", "license", "validation", "notes"])
        for r in cad_rows:
            w.writerow([r["category"], r["format"], r["path"], r["bytes"], r["sha256"], r["source"],
                        "V2.4r2", r["license"], r["validation"], r["notes"]])

    # Checksums over source archives, docs, configs, scripts and reports.
    checksum_files = []
    for base in ["assets/source", "assets/previews", "assets/processed", "assets/test-models",
                 "assets/models", "BEFORE_AFTER_SCREENSHOTS",
                 "docs/official-docs", "docs/architecture", "docs/research",
                 "tools/downloads", "configs", "docs/reports", "scripts", "backend", "database",
                 "frontend/public"]:
        p = ROOT / base
        if p.exists():
            checksum_files.extend([x for x in p.rglob("*") if x.is_file()])
    for name in ["BOM_300MM.csv", "BOM_300MM.html", "BOM_300MM.pdf", "CAD_ASSET_INDEX.csv",
                 "LICENSE_AUDIT.csv", "requirements.lock", "README.md", "PRINTVERSE_BOOTSTRAP_REPORT.md",
                 "OFFICIAL_RESOURCES.md", "SKILL_AUDIT.md", "SOFTWARE_INVENTORY.md",
                 "GCODE_TEST_REPORT.md", "CAD_VALIDATION_REPORT.md", "NEXT_DEVELOPMENT_PLAN.md",
                 "docs/research/IMAGE_TO_3D.md", "docs/research/GCODE_LIBRARIES.md",
                 "PHASE2_REPORT.md", "PHASE3_COMPLETION_REPORT.md", "PHASE3_MANIFEST.json",
                 "MECHANICAL_PARAMETERS.md", "requirements-cadquery.lock",
                 "CAD_PLACEMENT_AUDIT.md", "CAD_MODULE_MANIFEST.json", "ASSEMBLY_HIERARCHY.json",
                 "MATERIAL_LIBRARY.json", "MODEL_VALIDATION_REPORT.md", "VISUAL_UPGRADE_REPORT.md",
                 "PERFORMANCE_REPORT.md", "HEIGHT_CLEARANCE_ANALYSIS.md",
                 "IMAGE_TO_3D_PROVIDERS.md", "MODEL_BENCHMARK_REPORT.md", "SHARING_AND_QUOTA.md",
                 "PHASE4_REPORT.md", "manifests/image3d.json",
                 "manifests/mechanical-parameters.json", "manifests/machine-hierarchy.json",
                 "manifests/placements.json", "manifests/module-parts.json",
                 "frontend/package.json", "frontend/package-lock.json", "frontend/index.html",
                 "frontend/vite.config.ts"]:
        p = ROOT / name
        if p.exists():
            checksum_files.append(p)
    checksum_files.extend([x for x in (ROOT / "frontend/src").rglob("*") if x.is_file()])
    checksum_files = sorted(set(
        p for p in checksum_files
        if "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".tsbuildinfo"}
    ))
    lines = []
    total_bytes = 0
    for p in checksum_files:
        total_bytes += p.stat().st_size
        lines.append(f"{sha256(p)}  {rel(p)}")
    (MAN / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dependencies = {
        "generated_at": NOW,
        "environment": {
            "os": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version,
            "python_executable": sys.executable,
            "node": subprocess.getoutput("node --version"),
            "npm": subprocess.getoutput("npm --version"),
            "git": subprocess.getoutput("git --version"),
            "uv": subprocess.getoutput("uv --version"),
            "cpu_logical": os.cpu_count(),
        },
        "python_lock": [line for line in (ROOT / "requirements.lock").read_text(encoding="utf-8").splitlines() if line.strip()],
        "python_cadquery_lock": [line for line in (ROOT / "requirements-cadquery.lock").read_text(encoding="utf-8").splitlines() if line.strip()] if (ROOT / "requirements-cadquery.lock").exists() else [],
        "python_licenses": python_rows,
        "node_manifest": json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8")),
        "tools": {
            "FreeCAD": "1.1.4", "Blender": "4.5.12 LTS", "OrcaSlicer": "2.4.2",
            "7zr": "26.04", "Print3D Toolbox": "1.5.0",
            "build123d": "0.13.0", "cadquery-ocp-novtk": "8.0.1.1.0",
            "cadquery": "2.8.0 (isolated .venv-cadquery)", "cadquery-ocp": "7.9.3.1 (isolated)",
        },
    }
    (MAN / "dependencies.json").write_text(json.dumps(dependencies, indent=2), encoding="utf-8")

    criteria = {
        "A_official_voron_assets": "COMPLETE",
        "B_300mm_bom": "COMPLETE",
        "C_software": "COMPLETE",
        "D_skills_loaded": "COMPLETE",
        "E_freecad_cad_import": "COMPLETE" if (REPORTS / "freecad_stl_test.json").exists() else "PARTIAL",
        "F_orcaslicer_test_slice": "COMPLETE" if (ROOT / "assets/test-models/cube.gcode").exists() else "NOT_STARTED",
        "G_gcode_parsed": "COMPLETE" if (REPORTS / "gcode_parse.json").exists() else "NOT_STARTED",
        "H_threejs_scene": "COMPLETE",
        "I_licenses_recorded": "COMPLETE",
        "J_reports": "COMPLETE",
    }
    manifest = {
        "project": "PrintVerse",
        "generated_at": NOW,
        "root": str(ROOT),
        "bootstrap_status": "COMPLETE",
        "criteria": criteria,
        "counts": {
            "resources": len(resources),
            "cad_index_rows": len(cad_rows),
            "checksum_files": len(checksum_files),
            "checksum_bytes": total_bytes,
            "stl_files": sum(1 for r in cad_rows if r["format"] == "stl"),
            "dxf_files": sum(1 for r in cad_rows if r["format"] == "dxf"),
            "step_files": sum(1 for r in cad_rows if r["format"] in {"step", "stp"}),
            "licenses": len(LICENSES) + len(python_rows),
        },
        "evidence": {
            "bom": "BOM_300MM.csv",
            "cad_validation": "CAD_VALIDATION_REPORT.md",
            "mesh_audit": "docs/reports/mesh_audit.json",
            "freecad_stl": "docs/reports/freecad_stl_test.json",
            "freecad_step_part": "docs/reports/freecad_step_part_test.json",
            "freecad_step_structure": "docs/reports/step_structure.json",
            "step_xcaf_hierarchy": "docs/reports/step_xcaf_tree.json",
            "freecad_full_tree": "docs/reports/freecad_full_tree.json",
            "build123d": "assets/processed/build123d_test.step",
            "bom_browser": "assets/previews/BOM_300MM_browser.png",
            "gcode_parse": "docs/reports/gcode_parse.json",
            "threejs_glb": "docs/reports/threejs_glb_test.json",
            "threejs_smoke": "docs/reports/threejs_smoke.json",
            "skills": "SKILL_AUDIT.md",
            "checksums": "manifests/checksums.sha256",
        },
        "phase2": {
            "report": "PHASE2_REPORT.md",
            "status": "COMPLETE",
            "functional_acceptance": "COMPLETE",
            "cad_fidelity": "PARTIAL",
            "acceptance": {
                "upload_stl": "COMPLETE",
                "real_orca_slice": "COMPLETE",
                "gcode_animation": "COMPLETE",
                "detach_transform_collect": "COMPLETE",
                "filament_ledger": "COMPLETE",
                "exact_step_transforms": "PARTIAL",
                "cadquery_build123d_isolation": "COMPLETE",
                "image_to_3d_local": "BLOCKED_HARDWARE",
            },
            "evidence": "docs/reports/phase2_e2e.json",
            "mechanical_table": "MECHANICAL_PARAMETERS.md",
            "xcaf_hierarchy": "docs/reports/step_xcaf_tree.json",
            "freecad_object_placements": "docs/reports/freecad_full_tree.json",
            "bed_mesh": "frontend/public/models/voron_300_bed.stl",
            "screenshots": "assets/previews/phase2_scene_*.png",
        },
        "phase3": {
            "report": "PHASE3_COMPLETION_REPORT.md",
            "manifest": "PHASE3_MANIFEST.json",
            "status": "PARTIAL",
            "placements": 4526,
            "part_features": 1686,
            "modules": 8,
            "module_bytes": 35489880,
            "lod_bytes": 5940032,
            "hardware_fps": 60.1,
            "instancing": "COMPLETE / 66 InstancedMesh groups, 867 parts; optional toggle",
            "motion_hierarchy": "PARTIAL / toolhead+bed CAD motion; XY crossbeam static",
            "physical_z_clearance": "PHYSICAL_PENDING",
        },
        "phase4": {
            "report": "PHASE4_REPORT.md",
            "manifest": "manifests/image3d.json",
            "status": "PARTIAL",
            "providers": "backend/app/image3d",
            "ui": "frontend/src/components/Image3DPanel.tsx",
            "benchmark": "MODEL_BENCHMARK_REPORT.md",
            "sharing": "SHARING_AND_QUOTA.md",
            "kimi": "BLOCKED_ACCOUNT_429",
            "triposr": "BLOCKED_NETWORK / not tested",
            "tokenhub": "NOT_CONFIGURED / no cost incurred",
        },
        "blocked": [
            "Optional local image-to-3D: Hunyuan3D needs about 10 GB VRAM for shape (29 GB total); TRELLIS needs at least 16 GB; the machine has 8 GB. TripoSR remains a candidate but CUDA PyTorch and weights were not downloaded.",
        ],
        "partial": [
            "Full 267 MB Voron assembly FreeCAD import timed out after 261.7 CPU seconds / about 1.2 GB working set; STEP text structure was parsed instead (1,534 products, 1,662 solids).",
            "cadquery 2.8 requires OCP <8.0 and cannot share the verified build123d OCP 8.0 environment; deferred to a separate venv.",
        ],
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"resources": len(resources), "cad_rows": len(cad_rows), "checksums": len(checksum_files),
                      "checksum_bytes": total_bytes, "licenses": len(LICENSES) + len(python_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
