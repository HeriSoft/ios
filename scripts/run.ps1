# Chạy App Builder AI từ source
$root = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "Chưa có .venv — chạy .\scripts\setup.ps1 trước." -ForegroundColor Yellow
    exit 1
}
$env:PYTHONPATH = Join-Path $root "src"
& $venvPy -m app_builder @args
