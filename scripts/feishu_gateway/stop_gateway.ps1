[CmdletBinding()]
param([int]$TimeoutSeconds = 10)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot); $pidPath = Join-Path $root 'runtime/gateway.pid'
if (-not (Test-Path $pidPath)) { '{"running":false,"status":"pid_missing"}'; exit 0 }
$targetPid = [int](Get-Content -Raw -LiteralPath $pidPath)
$process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
if ($null -ne $process) {
  $statusPath = Join-Path $root 'runtime/gateway.status.json'; $port = if (Test-Path $statusPath) { (Get-Content -Raw $statusPath | ConvertFrom-Json).port } else { 18990 }
  try { Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:$port/shutdown" -TimeoutSec 2 | Out-Null } catch { }
  $process.WaitForExit($TimeoutSeconds * 1000) | Out-Null
  if (-not $process.HasExited) { Stop-Process -Id $targetPid -Force }
}
Remove-Item -LiteralPath $pidPath -Force
'{"running":false,"status":"stopped"}'
