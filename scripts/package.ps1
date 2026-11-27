# Đóng gói desktop bằng PyInstaller (onedir). Installer Inno Setup: milestone M8.
# Không nhúng API key / secret vào bản build.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
& $venvPy -m PyInstaller --noconfirm --clean --onedir --windowed `
    --name AppBuilderAI `
    --paths src `
    --collect-data app_builder `
    --collect-submodules app_builder `
    src\app_builder\__main__.py
$exe = Join-Path $root "dist\AppBuilderAI\AppBuilderAI.exe"
if (Test-Path $exe) {
    Write-Host "Build OK: $exe"
    $we = Get-ChildItem -Recurse (Join-Path $root "dist\AppBuilderAI") -Filter "QtWebEngineProcess.exe" | Select-Object -First 1
    if ($we) { Write-Host "QtWebEngineProcess: $($we.FullName)" } else { Write-Host "CẢNH BÁO: thiếu QtWebEngineProcess.exe" -ForegroundColor Yellow }
} else {
    Write-Host "Build thất bại" -ForegroundColor Red; exit 1
}
