$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
Set-ExecutionPolicy -Scope Process Bypass -Force

Write-Host "[0/3] Project-local Python bootstrap"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\00_bootstrap_python.ps1 -Apply
if ($LASTEXITCODE -ne 0) { throw "Python bootstrap failed." }

Write-Host "[1/3] Package integrity"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\00_package_check.ps1
if ($LASTEXITCODE -ne 0) { throw "Package check failed." }

Write-Host "[2/3] Machine preflight"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\01_machine_preflight.ps1
if ($LASTEXITCODE -ne 0) { throw "Machine preflight found blockers. Read reports." }

Write-Host "[3/3] OpenClaw state capture"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\02_capture_openclaw_state.ps1
if ($LASTEXITCODE -ne 0) { throw "OpenClaw state capture failed." }

Write-Host "P0 read-only preflight completed. Codex must now review reports before changing the system."
