$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$required = @("START_HERE_CODEX.md","PROJECT_STATUS.yaml","AGENTS.md","skills","config","scripts","runbook","handoff")
$missing = @()
foreach ($item in $required) { if (-not (Test-Path (Join-Path $Root $item))) { $missing += $item } }
if (Test-Path (Join-Path $Root "工作区\skills")) { throw "Invalid nested workspace: 工作区\skills" }
if ($missing.Count -gt 0) { throw "Missing: $($missing -join ', ')" }
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python is required." }
    $Python = (Get-Command python).Source
}
& $Python -c "import yaml, jsonschema, websockets.sync.client" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Bootstrap dependencies are missing. Run scripts\00_bootstrap_python.ps1 -Apply first."
}
& $Python .\scripts\90_acceptance_gate.py --gate package
exit $LASTEXITCODE
