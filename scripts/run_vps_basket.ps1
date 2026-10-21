# Preview by default. No passwords are accepted or stored by this launcher.
[CmdletBinding(PositionalBinding=$false)]
param(
    [switch]$Execute,
    [long]$AccountLogin = 0
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing .venv. Install the project first." }
if ($Execute -and $AccountLogin -le 0) { throw "Execution requires -AccountLogin." }
$botArgs = @("-m", "app.basket.worker", "--mode", "mt5", "--config", "config/basket.example.json")
if ($AccountLogin -gt 0) { $botArgs += @("--account-login", "$AccountLogin") }
if ($Execute) { $botArgs += "--execute" }
& $python @botArgs
exit $LASTEXITCODE
