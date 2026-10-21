# Localhost-only UI. Open http://127.0.0.1:8765 inside the VPS.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing Python virtual environment" }
& $python -m app.automation.dashboard --port 8765
exit $LASTEXITCODE
