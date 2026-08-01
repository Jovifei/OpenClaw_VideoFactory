# scripts/run_ingest_safe.ps1
# Thin try/catch adapter around 07_ingest_inbound_media.ps1.
#
# Purpose: the inner script throws a compact JSON error object on validation
# failure, but PowerShell's native error formatting wraps long lines at ~120
# chars and can insert the wrap INSIDE a JSON string value, corrupting it on
# stderr. This adapter catches the exception and echoes the clean, single-line
# JSON (the exception message) to STDOUT so the MCP server can parse it.
#
# This is NOT a second safety implementation. All path/MIME/signature/hash/
# receipt safety logic remains in 07_ingest_inbound_media.ps1. This wrapper
# only normalizes the process boundary.
#
# Exit codes: 0 success (JSON on stdout), 1 validation failure (error JSON on
# stdout), 2 internal invocation error.
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$SourcePath,
  [Parameter(Mandatory = $true)][string]$MessageId,
  [Parameter(Mandatory = $true)][string]$OriginalFileName,
  [Parameter(Mandatory = $true)][AllowEmptyString()][string]$ContentType,
  [Parameter(Mandatory = $true)][Int64]$MaxBytes,
  [Parameter(Mandatory = $true)][string]$AccountId,
  [Parameter(Mandatory = $true)][string]$ChatId,
  [Parameter(Mandatory = $true)][string]$SenderId,
  [string]$ReceivedAt = '',
  [string]$InboundRoot = (Join-Path $env:USERPROFILE '.openclaw\media\inbound'),
  [string]$ProjectRoot = $(Split-Path -Parent $PSScriptRoot),
  [ValidatePattern('^[a-z][a-z0-9_-]{2,63}$')][string]$TrustedRootId = 'legacy_default',
   [string]$CanonicalSourcePath = '<redacted>',
   [int]$AttachmentIndex = -1,
   [int]$AttachmentCount = 1,
   [string]$EventId = '',
   [Nullable[Int64]]$DeclaredSizeBytes = $null,
   [ValidateSet('0', '1')][string]$DeclaredSizeTrusted = '0',
   [string]$DeclaredSizeSource = 'none',
   [Nullable[Int64]]$UntrustedSizeClaimBytes = $null,
   [ValidateSet('0', '1')][string]$UntrustedSizeClaimPresent = '0',
   [ValidateSet('0', '1')][string]$UntrustedSizeClaimValid = '1',
   [string]$UntrustedSizeClaimSource = 'none',
   [string]$UntrustedSizeClaimType = 'none'
)

$ErrorActionPreference = 'Stop'
$inner = Join-Path $PSScriptRoot '07_ingest_inbound_media.ps1'
$innerArgs = @{
    SourcePath = $SourcePath
    MessageId = $MessageId
    OriginalFileName = $OriginalFileName
    ContentType = $ContentType
    MaxBytes = $MaxBytes
    AccountId = $AccountId
    ChatId = $ChatId
    SenderId = $SenderId
    ReceivedAt = $ReceivedAt
    InboundRoot = $InboundRoot
    ProjectRoot = $ProjectRoot
    TrustedRootId = $TrustedRootId
    CanonicalSourcePath = $CanonicalSourcePath
    AttachmentIndex = $AttachmentIndex
    AttachmentCount = $AttachmentCount
    EventId = $EventId
}
if ($null -ne $DeclaredSizeBytes) {
    $innerArgs.DeclaredSizeBytes = [Int64]$DeclaredSizeBytes
}
if ($DeclaredSizeTrusted -eq '1') {
    $innerArgs.DeclaredSizeTrusted = '1'
    $innerArgs.DeclaredSizeSource = $DeclaredSizeSource
}
if ($null -ne $UntrustedSizeClaimBytes) {
    $innerArgs.UntrustedSizeClaimBytes = [Int64]$UntrustedSizeClaimBytes
}
$innerArgs.UntrustedSizeClaimPresent = $UntrustedSizeClaimPresent
$innerArgs.UntrustedSizeClaimValid = $UntrustedSizeClaimValid
$innerArgs.UntrustedSizeClaimSource = $UntrustedSizeClaimSource
$innerArgs.UntrustedSizeClaimType = $UntrustedSizeClaimType

try {
    & $inner @innerArgs
}
catch {
    $msg = [string]$_.Exception.Message
    # The inner script throws a compact JSON error object (Throw-IngestValidationFailure).
    # Echo it verbatim if it parses as JSON; otherwise wrap as a generic ingest_failed.
    $parsed = $null
    try { $parsed = $msg | ConvertFrom-Json -ErrorAction Stop } catch { }
    if ($null -ne $parsed -and $parsed.error_code) {
        [Console]::Out.WriteLine($msg)
    } else {
        $safe = ($msg -replace '[\r\n]+', ' ')
        [Console]::Out.WriteLine(([pscustomobject]@{ error_code = 'ingest_failed'; detail = $safe } | ConvertTo-Json -Compress))
    }
    exit 1
}
