param(
    [switch]$StartAppConfiguration,
    [switch]$CheckStatus,
    [switch]$EnableUserDriveDocs
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command lark-cli -ErrorAction SilentlyContinue)) {
    throw "lark-cli is not installed. Run install_lark_cli.ps1 first."
}

if ($StartAppConfiguration) {
    Write-Host "Starting official app configuration flow."
    Write-Host "Codex/OpenClaw must show the returned URL and QR code to the user without modifying it."
    & lark-cli config init --new
}

if ($EnableUserDriveDocs) {
    Write-Host "User identity is optional. Starting minimal Drive/Docs authorization."
    & lark-cli auth login --domain drive --domain docs --no-wait --json
    Write-Host "Use lark-cli auth qrcode on the returned verification URL."
}

if ($CheckStatus -or (-not $StartAppConfiguration -and -not $EnableUserDriveDocs)) {
    & lark-cli auth status --json --verify
    & lark-cli whoami
}

Write-Host "Bot sending does not require a user OAuth login, but the app must have the required bot scopes and be present in the target chat."
