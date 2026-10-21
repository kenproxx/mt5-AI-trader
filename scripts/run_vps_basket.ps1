# Preview by default. No passwords are accepted or stored by this launcher.
param(
    [switch]$ExecuteDemo,
    [long]$AccountLogin = 0
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing .venv. Install the project first." }
if ($ExecuteDemo -and $AccountLogin -le 0) { throw "Demo execution requires -AccountLogin." }
$botArgs = @("-m", "app.basket.worker", "--mode", "mt5", "--config", "config/basket.example.json")
if ($AccountLogin -gt 0) { $botArgs += @("--account-login", "$AccountLogin") }
if ($ExecuteDemo) { $botArgs += "--execute-demo" }
& $python @botArgs
exit $LASTEXITCODE
