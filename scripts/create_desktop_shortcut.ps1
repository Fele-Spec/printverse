# Create a real Windows desktop shortcut to the built Tauri executable.
# Run from the repository root:
#   powershell -ExecutionPolicy Bypass -File scripts/create_desktop_shortcut.ps1
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root "desktop\src-tauri\target\release\printverse-desktop.exe"
if (-not (Test-Path $exe)) {
    throw "Tauri executable missing: $exe"
}
$desktop = [Environment]::GetFolderPath("Desktop")
$link = Join-Path $desktop "PrintVerse Desktop Pet.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($link)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = $root
$shortcut.Description = "PrintVerse Desktop Pet"
$shortcut.IconLocation = (Join-Path $root "desktop\src-tauri\icons\icon.ico")
$shortcut.Save()
Write-Output "CREATED $link"
Write-Output "TARGET $exe"
