# Thiết lập môi trường phát triển App Builder AI (không cần quyền admin)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $python = "py"; $pyArgs = @("-3.11") } else { $python = "python"; $pyArgs = @() }

if (-not (Test-Path ".venv")) {
    Write-Host "Tạo virtualenv .venv ..."
    & $python @pyArgs -m venv .venv
}
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -e ".[dev]"
Write-Host ""
Write-Host "Kiểm tra công cụ (Doctor):"
& $venvPy -m app_builder doctor
Write-Host ""
Write-Host "Xong. Chạy ứng dụng: .\scripts\run.ps1"
