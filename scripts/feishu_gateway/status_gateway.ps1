$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$runtime = Join-Path $root 'runtime'
$pidPath = Join-Path $runtime 'gateway.pid'
$statusPath = Join-Path $runtime 'gateway.status.json'

if (-not (Test-Path -LiteralPath $pidPath) -or -not (Test-Path -LiteralPath $statusPath)) {
    '{"running":false,"ready":false,"health":"unknown","mode":"unknown","openclaw_rpc":"unknown","version":"0.35.0"}'
    exit 0
}

$status = Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
$pidValue = [int](Get-Content -Raw -LiteralPath $pidPath)
$alive = $null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
[ordered]@{
    running = $alive
    ready = $alive -and $status.ready -eq $true
    pid = $pidValue
    uptime = $status.uptime
    last_log = $status.log_path
    health = $status.health
    mode = $status.mode
    feishu_connection = $status.feishu_connection
    openclaw_rpc = $status.openclaw_rpc
    rpc_endpoint_available = $status.rpc_endpoint_available
    token_present = $status.token_present
    auth_valid = $status.auth_valid
    session_ready = $status.session_ready
    rpc_preflight_result = $status.rpc_preflight_result
    command_line_secret_safe = $status.command_line_secret_safe
    version = $status.version
} | ConvertTo-Json -Compress
