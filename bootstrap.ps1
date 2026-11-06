# PrintVerse reproducible bootstrap (Windows, no admin required)
# Pins the official versions used by the 2026-11-06 bootstrap. Existing files are reused.
param(
    [switch]$SkipDownloads,
    [switch]$SkipTests,
    [switch]$FullCad
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Write-Step([string]$Text) { Write-Host "`n=== $Text ===" -ForegroundColor Cyan }
function Ensure-Dir([string]$Path) { if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }

$VoronTag = "V2.4r2"
$KlipperTag = "v0.13.0"
$MoonrakerTag = "v0.11.0"
$OrcaVersion = "v2.4.2"
$FreeCadVersion = "1.1.4"
$BlenderVersion = "4.5.12"

Ensure-Dir ".cache/npm"; Ensure-Dir ".cache/uv"; Ensure-Dir "logs"; Ensure-Dir "tools/downloads"
Ensure-Dir ".cache/freecad/home"; Ensure-Dir ".cache/freecad/data"; Ensure-Dir ".cache/freecad/temp"
Ensure-Dir ".cache/orca-data"
$env:npm_config_cache = "$Root/.cache/npm"
$env:UV_CACHE_DIR = "$Root/.cache/uv"
$env:FREECAD_USER_HOME = "$Root/.cache/freecad/home"
$env:FREECAD_USER_DATA = "$Root/.cache/freecad/data"
$env:FREECAD_USER_TEMP = "$Root/.cache/freecad/temp"

Write-Step "1. Git and directories"
if (-not (Test-Path ".git")) { git init -q; git config user.name "PrintVerse Bootstrap"; git config user.email "bootstrap@printverse.local" }
$dirs = @(".dsh/skills", ".agents/skills", "assets/source/voron-v2.4r2-300/CAD", "assets/source/voron-v2.4r2-300/STLs",
    "assets/source/voron-v2.4r2-300/DXF", "assets/source/voron-v2.4r2-300/Manual", "assets/source/voron-v2.4r2-300/BOM",
    "assets/source/voron-v2.4r2-300/Firmware", "assets/processed", "assets/previews", "assets/test-models",
    "configs/machine", "configs/filament", "configs/process", "configs/motion", "docs/official-docs",
    "docs/research", "docs/architecture", "docs/reports", "backend", "frontend", "database", "scripts", "logs", "manifests")
$dirs | ForEach-Object { Ensure-Dir $_ }

if (-not $SkipDownloads) {
    Write-Step "2. Official Voron design archive ($VoronTag)"
    if (-not (Test-Path "assets/source/voron-v2.4r2-300/Voron-2-V2.4r2.zip")) {
        node scripts/fetch.mjs --url "https://codeload.github.com/VoronDesign/Voron-2/zip/refs/tags/$VoronTag" `
            --out "assets/source/voron-v2.4r2-300/Voron-2-V2.4r2.zip" --retries 4
    }

    Write-Step "3. Klipper and Moonraker source"
    if (-not (Test-Path "assets/source/voron-v2.4r2-300/Firmware/klipper-$KlipperTag.zip")) {
        node scripts/fetch.mjs --url "https://codeload.github.com/Klipper3d/klipper/zip/refs/tags/$KlipperTag" `
            --out "assets/source/voron-v2.4r2-300/Firmware/klipper-$KlipperTag.zip"
    }
    if (-not (Test-Path "assets/source/voron-v2.4r2-300/Firmware/moonraker-$MoonrakerTag.zip")) {
        node scripts/fetch.mjs --url "https://codeload.github.com/Arksine/moonraker/zip/refs/tags/$MoonrakerTag" `
            --out "assets/source/voron-v2.4r2-300/Firmware/moonraker-$MoonrakerTag.zip"
    }

    Write-Step "4. OrcaSlicer / FreeCAD / Blender / Blender extension / 7zr"
    if (-not (Test-Path "tools/downloads/OrcaSlicer_Windows_V2.4.2_x64_portable.zip")) {
        node scripts/fetch.mjs --github-repo OrcaSlicer/OrcaSlicer `
            --github-asset OrcaSlicer_Windows_V2.4.2_x64_portable.zip `
            --out "tools/downloads/OrcaSlicer_Windows_V2.4.2_x64_portable.zip"
    }
    if (-not (Test-Path "tools/downloads/FreeCAD_${FreeCadVersion}-Windows-x86_64-py311.7z")) {
        node scripts/fetch.mjs --github-repo FreeCAD/FreeCAD `
            --github-asset "FreeCAD_${FreeCadVersion}-Windows-x86_64-py311.7z" `
            --out "tools/downloads/FreeCAD_${FreeCadVersion}-Windows-x86_64-py311.7z"
    }
    if (-not (Test-Path "tools/downloads/blender-${BlenderVersion}-windows-x64.zip")) {
        node scripts/fetch.mjs --url "https://download.blender.org/release/Blender4.5/blender-${BlenderVersion}-windows-x64.zip" `
            --out "tools/downloads/blender-${BlenderVersion}-windows-x64.zip"
    }
    if (-not (Test-Path "tools/downloads/7zr.exe")) {
        node scripts/fetch.mjs --url "https://www.7-zip.org/a/7zr.exe" --out "tools/downloads/7zr.exe"
    }
    if (-not (Test-Path "tools/downloads/print3d-toolbox-1.5.0.zip")) {
        node scripts/fetch.mjs --url "https://extensions.blender.org/download/sha256:3e3121a8052d52ce1fe8fd13bc6431679018f0cf1cb51ac0224fc47073a8e12a/add-on-print3d-toolbox-v1.5.0.zip?repository=%2Fapi%2Fv1%2Fextensions%2F&blender_version_min=4.2.0" `
            --sha256 "3e3121a8052d52ce1fe8fd13bc6431679018f0cf1cb51ac0224fc47073a8e12a" `
            --out "tools/downloads/print3d-toolbox-1.5.0.zip"
    }
    if (-not (Test-Path "docs/official-docs/Voron-Documentation-main.zip")) {
        node scripts/fetch.mjs --url "https://codeload.github.com/VoronDesign/Voron-Documentation/zip/refs/heads/main" `
            --out "docs/official-docs/Voron-Documentation-main.zip"
    }
}

Write-Step "5. Extract tools (only when missing)"
python -c "import zipfile,os; p='assets/source/voron-v2.4r2-300/Voron-2-V2.4r2.zip'; o='assets/source/voron-v2.4r2-300'; zipfile.ZipFile(p).extractall(o) if os.path.exists(p) and not os.path.exists(os.path.join(o,'Voron-2-2.4r2')) else None"
python -c "import zipfile,os; p='assets/source/voron-v2.4r2-300/Firmware/klipper-$KlipperTag.zip'; o='assets/source/voron-v2.4r2-300/Firmware'; zipfile.ZipFile(p).extractall(o) if os.path.exists(p) and not os.path.exists(os.path.join(o,'klipper-0.13.0')) else None"
python -c "import zipfile,os; p='assets/source/voron-v2.4r2-300/Firmware/moonraker-$MoonrakerTag.zip'; o='assets/source/voron-v2.4r2-300/Firmware'; zipfile.ZipFile(p).extractall(o) if os.path.exists(p) and not os.path.exists(os.path.join(o,'moonraker-0.11.0')) else None"
if (-not (Test-Path "tools/OrcaSlicer-2.4.2/orca-slicer.exe")) {
    python -c "import zipfile; zipfile.ZipFile('tools/downloads/OrcaSlicer_Windows_V2.4.2_x64_portable.zip').extractall('tools/OrcaSlicer-2.4.2')"
}
if (-not (Test-Path "tools/Blender-4.5.12/blender.exe")) {
    python -c "import zipfile,os; zipfile.ZipFile('tools/downloads/blender-4.5.12-windows-x64.zip').extractall('tools'); os.rename('tools/blender-4.5.12-windows-x64','tools/Blender-4.5.12') if os.path.isdir('tools/blender-4.5.12-windows-x64') else None"
}
if (-not (Test-Path "tools/FreeCAD-1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311/FreeCADCmd.exe")) {
    & .\tools\downloads\7zr.exe x .\tools\downloads\FreeCAD_1.1.4-Windows-x86_64-py311.7z "-o$Root\tools\FreeCAD-1.1.4" -y | Out-Null
}

# Canonical category copies plus the nested STEP archive.
python -c "import shutil,os; b='assets/source/voron-v2.4r2-300'; o=os.path.join(b,'Voron-2-2.4r2'); [shutil.copytree(os.path.join(o,s),os.path.join(b,d),dirs_exist_ok=True) for s,d in [('STLs','STLs'),('Drawing_DXFs','DXF'),('Manual','Manual'),('CAD','CAD'),('firmware',os.path.join('Firmware','voron-official'))]] if os.path.isdir(o) else None"
python -c "import zipfile,os; p='assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step.zip'; o='assets/source/voron-v2.4r2-300/CAD'; zipfile.ZipFile(p).extractall(o) if os.path.exists(p) and not os.path.exists(os.path.join(o,'VORON2.4_Assembly.step')) else None"

# Official documentation source and the Blender 3D Print Toolbox.
python -c "import zipfile,os; p='docs/official-docs/Voron-Documentation-main.zip'; o='docs/official-docs'; zipfile.ZipFile(p).extractall(o) if os.path.exists(p) and not os.path.isdir(os.path.join(o,'Voron-Documentation-main')) else None"
$env:BLENDER_USER_CONFIG = "$Root/.cache/blender/config"
$env:BLENDER_USER_SCRIPTS = "$Root/.cache/blender/scripts"
$env:BLENDER_USER_DATAFILES = "$Root/.cache/blender/datafiles"
$env:BLENDER_USER_EXTENSIONS = "$Root/.cache/blender/extensions"
Ensure-Dir $env:BLENDER_USER_CONFIG; Ensure-Dir $env:BLENDER_USER_SCRIPTS
Ensure-Dir $env:BLENDER_USER_DATAFILES; Ensure-Dir $env:BLENDER_USER_EXTENSIONS
if (-not (Test-Path "$env:BLENDER_USER_EXTENSIONS/user_default/print3d_toolbox")) {
    & "$Root/tools/Blender-4.5.12/blender.exe" --command extension install-file -r user_default -e "$Root/tools/downloads/print3d-toolbox-1.5.0.zip" | Out-Null
}

Write-Step "6. Python environment and lock"
if (-not (Test-Path ".venv/Scripts/python.exe")) { uv venv --python 3.12 .venv }
uv pip install --python .venv/Scripts/python.exe -r requirements.lock
uv pip freeze --python .venv/Scripts/python.exe | Set-Content -Encoding utf8 requirements.lock

Write-Step "7. Frontend dependencies and build"
npm install --prefix frontend
python scripts/patch_vite_windows.py
npm run build --prefix frontend

Write-Step "8. Resolve official Orca profiles"
.\.venv\Scripts\python.exe scripts\build_orca_profiles.py

Write-Step "9. Official documentation mirror"
.\.venv\Scripts\python.exe scripts\build_docs.py

if (-not $SkipTests) {
    Write-Step "10. FreeCAD STL import"
    $fc = "$Root/tools/FreeCAD-1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311/FreeCADCmd.exe"
    $env:PV_SCRIPT = "$Root/scripts/freecad_validate.py"
    $env:PV_OUT = "$Root/docs/reports/freecad_stl_test.json"
    $env:PV_STL = "$Root/assets/source/voron-v2.4r2-300/STLs/Test_Prints/Filament_Card.stl"
    $env:PV_STEP = ""
    cmd /c "type scripts\freecad_entry.py | `"$fc`" -c"

    if ($FullCad) {
        Write-Step "10b. FreeCAD full STEP assembly (slow)"
        $env:PV_OUT = "$Root/docs/reports/freecad_step_test.json"
        $env:PV_STL = ""
        $env:PV_STEP = "$Root/assets/source/voron-v2.4r2-300/CAD/VORON2.4_Assembly.step"
        cmd /c "type scripts\freecad_entry.py | `"$fc`" -c"
    }

    Write-Step "11. OrcaSlicer test slice"
    & "$Root/tools/OrcaSlicer-2.4.2/orca-slicer.exe" "$Root/assets/test-models/cube.stl" `
        --load-settings "$Root/configs/process/voron-0.20mm-standard.json;$Root/configs/machine/voron-v2.4r2-300-0.4.json" `
        --load-filaments "$Root/configs/filament/generic-pla.json" `
        --slice 0 --outputdir "$Root/assets/test-models" --export-3mf "cube.3mf" `
        --datadir "$Root/.cache/orca-data" --logfile "$Root/logs/orca-slice.log" --debug 3
    if ((Test-Path "$Root/assets/test-models/plate_1.gcode") -and -not (Test-Path "$Root/assets/test-models/cube.gcode")) {
        Copy-Item "$Root/assets/test-models/plate_1.gcode" "$Root/assets/test-models/cube.gcode"
    }

    Write-Step "12. Mesh / G-code / Three.js checks"
    .\.venv\Scripts\python.exe scripts\asset_integrity.py
    .\.venv\Scripts\python.exe scripts\mesh_audit.py
    .\.venv\Scripts\python.exe scripts\parse_gcode.py assets\test-models\cube.gcode --out docs\reports\gcode_parse.json --expected-size 20,20,20
    .\.venv\Scripts\python.exe scripts\gcode_parser_test.py
    node scripts/threejs_glb_test.mjs
}

Write-Step "13. Rebuild BOM, manifests and checksums"
node scripts/generate_bom.mjs
.\.venv\Scripts\python.exe scripts\build_manifest.py
.\.venv\Scripts\python.exe scripts\render_bom.py

Write-Host "`nBootstrap complete. Overall status remains PARTIAL while the browser screenshot," -ForegroundColor Yellow
Write-Host "build123d/cadquery and image-to-3D installation are blocked; see PRINTVERSE_BOOTSTRAP_REPORT.md." -ForegroundColor Yellow
