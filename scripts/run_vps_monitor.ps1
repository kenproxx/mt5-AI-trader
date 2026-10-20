# Run in a logged-on Windows VPS session with MT5 LiteFinance Demo open.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force (Join-Path $root "logs") | Out-Null
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing Python virtual environment" }
& $python -m app.automation.worker --mode mt5 --interval 30 *>> (Join-Path $root "logs\worker.log")
exit $LASTEXITCODE
