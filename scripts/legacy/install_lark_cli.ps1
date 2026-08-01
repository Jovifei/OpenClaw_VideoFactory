param(
    [string]$Version = "latest",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required."
}
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    throw "npx is required."
}

$display = "npx @larksuite/cli@$Version install"
Write-Host $display

if (-not $Apply) {
    Write-Host "Dry run only. Review the official repository and rerun with -Apply."
    exit 0
}

& npx "@larksuite/cli@$Version" install
if ($LASTEXITCODE -ne 0) {
    throw "lark-cli installer failed."
}

& lark-cli --version
& lark-cli auth status --json --verify

Write-Host ""
Write-Host "Installation finished."
Write-Host "Record the installed version in config\versions.lock.yaml."
Write-Host "Credentials and app configuration are intentionally not created by this script."
