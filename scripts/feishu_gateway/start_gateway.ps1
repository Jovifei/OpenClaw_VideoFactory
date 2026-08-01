[CmdletBinding()]
param(
    [int]$Port = 18990,
    [ValidateSet('offline', 'production-preflight', 'production')]
    [string]$Mode = 'offline',
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$runtime = Join-Path $root 'runtime'
$pidPath = Join-Path $runtime 'gateway.pid'
$statusPath = Join-Path $runtime 'gateway.status.json'
$logPath = Join-Path $runtime 'logs/gateway.jsonl'
$tokenPresent = $false
if ($Mode -eq 'production-preflight') {
    $tokenPresent = -not [string]::IsNullOrWhiteSpace($env:OPENCLAW_GATEWAY_TOKEN)
}

function Test-GatewayCommandLineSecretSafe {
    param([int]$ProcessId)
    $deadline = (Get-Date).AddSeconds(3)
    do {
        $processRecord = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
        if ($null -ne $processRecord) {
            $commandLine = [string]$processRecord.CommandLine
            return $commandLine -notmatch '(?i)(--token\b|--password\b|OPENCLAW_GATEWAY_TOKEN|OPENCLAW_GATEWAY_PASSWORD)'
        }
        Start-Sleep -Milliseconds 100
    } while ((Get-Date) -lt $deadline)
    throw 'gateway_command_line_inspection_unavailable'
}

if ($Mode -eq 'production') {
    [ordered]@{
        running = $false
        ready = $false
        mode = $Mode
        status = 'production_transport_unavailable'
    } | ConvertTo-Json -Compress
    exit 2
}

if ($Mode -eq 'production-preflight' -and -not $tokenPresent) {
    [ordered]@{
        running = $false
        ready = $false
        mode = $Mode
        status = 'RPC_CREDENTIAL_REQUIRED'
    } | ConvertTo-Json -Compress
    exit 2
}

if ($ValidateOnly) {
    [ordered]@{
        running = $false
        ready = $false
        mode = $Mode
        credential_present = $tokenPresent
        status = if ($Mode -eq 'production-preflight') { 'RPC_PRECHECK_NOT_EXECUTED' } else { 'OFFLINE_ISOLATED' }
    } | ConvertTo-Json -Compress
    exit 0
}

if (Test-Path -LiteralPath $pidPath) {
    throw 'gateway_pid_exists; use status_gateway.ps1 or stop_gateway.ps1'
}

$python = Join-Path $root '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'project_venv_python_missing'
}

Remove-Item -LiteralPath $statusPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path (Join-Path $runtime 'logs') | Out-Null
$env:FEISHU_GATEWAY_CONFIG_FINGERPRINT = (Get-FileHash (Join-Path $root 'config/feishu_gateway.example.yaml') -Algorithm SHA256).Hash
$env:FEISHU_GATEWAY_PORT = [string]$Port
$launchArguments = @(
    '-m', 'services.feishu_gateway.runtime_server',
    '--port', [string]$Port,
    '--status-file', "`"$statusPath`"",
    '--log-file', "`"$logPath`"",
    '--mode', $Mode
)
$process = Start-Process -FilePath $python -ArgumentList $launchArguments -WorkingDirectory $root -WindowStyle Hidden -PassThru
$deadline = (Get-Date).AddSeconds(25)
while (-not (Test-Path -LiteralPath $statusPath) -and (Get-Date) -lt $deadline) {
    if ($process.HasExited) { break }
    Start-Sleep -Milliseconds 100
}
if (-not (Test-Path -LiteralPath $statusPath)) {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
    throw 'gateway_start_timeout'
}

if (-not (Test-GatewayCommandLineSecretSafe -ProcessId $process.Id)) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw 'gateway_command_line_credential_detected'
}

$server = Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
$server | Add-Member -NotePropertyName command_line_secret_safe -NotePropertyValue $true -Force
$server | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statusPath -Encoding utf8
if ($Mode -eq 'production-preflight' -and $server.ready -ne $true) {
    if (-not $process.HasExited) {
        try {
            Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/shutdown" -TimeoutSec 2 | Out-Null
            $process.WaitForExit(3000) | Out-Null
        } catch {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Get-Content -Raw -LiteralPath $statusPath
    exit 2
}

$server.pid | Set-Content -LiteralPath $pidPath -Encoding ascii
Get-Content -Raw -LiteralPath $statusPath
