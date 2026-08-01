[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$SourcePath,
    [Parameter(Mandatory = $true)][ValidatePattern('^om_[A-Za-z0-9_-]+$')][string]$MessageId,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$OriginalFileName,
    [Parameter(Mandatory = $true)][AllowEmptyString()][string]$ContentType,
    [Parameter(Mandatory = $true)][ValidateRange(1, [Int64]::MaxValue)][Int64]$MaxBytes,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$AccountId,
    [Parameter(Mandatory = $true)][ValidatePattern('^oc_[A-Za-z0-9_-]+$')][string]$ChatId,
    [Parameter(Mandatory = $true)][ValidatePattern('^ou_[A-Za-z0-9_-]+$')][string]$SenderId,
    [string]$ReceivedAt = '',
    [string]$InboundRoot = (Join-Path $env:USERPROFILE '.openclaw\media\inbound'),
    [string]$ProjectRoot = $(Split-Path -Parent $PSScriptRoot),
    [ValidatePattern('^[a-z][a-z0-9_-]{2,63}$')][string]$TrustedRootId = 'legacy_default',
    [string]$CanonicalSourcePath = '<redacted>',
    # Multi-attachment extension (007). -1 = legacy single-attachment mode (preserves 32-test layout).
    [int]$AttachmentIndex = -1,
    [int]$AttachmentCount = 1,
    [string]$EventId = '',
    # These parameters are supplied only by mcp_ingest_attachment.py's
    # non-public Channel/Gateway adapter API. They are never present in the
    # public MCP tool schema and cannot make a Router claim trusted.
    [Nullable[Int64]]$DeclaredSizeBytes = $null,
    [ValidateSet('0', '1')][string]$DeclaredSizeTrusted = '0',
    [string]$DeclaredSizeSource = 'none',
    [Nullable[Int64]]$UntrustedSizeClaimBytes = $null,
    [ValidateSet('0', '1')][string]$UntrustedSizeClaimPresent = '0',
    [ValidateSet('0', '1')][string]$UntrustedSizeClaimValid = '1',
    [string]$UntrustedSizeClaimSource = 'none',
    [string]$UntrustedSizeClaimType = 'none'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$isDeclaredSizeTrusted = $DeclaredSizeTrusted -eq '1'
$hasUntrustedSizeClaim = $UntrustedSizeClaimPresent -eq '1'
$untrustedSizeClaimIsValid = $UntrustedSizeClaimValid -eq '1'

function Get-NormalizedAbsolutePath {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Label)
    $pathForCheck = $Path.Replace('/', '\')
    if ($pathForCheck.StartsWith('\\') -or $pathForCheck.StartsWith('\\?\') -or $pathForCheck.StartsWith('\\.\')) {
        throw "$Label cannot be a UNC or device path."
    }
    $drive, $tail = $pathForCheck -split ':', 2
    if ($tail -and $tail.Contains(':')) {
        throw "$Label cannot contain an alternate data stream."
    }
    if (-not [System.IO.Path]::IsPathRooted($Path)) {
        throw "$Label must be an absolute path."
    }
    return [System.IO.Path]::GetFullPath($Path)
}

function Test-PathWithinRoot {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Root)
    $normalizedPath = [System.IO.Path]::GetFullPath($Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $normalizedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    if ($normalizedPath.Equals($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    $rootWithSeparator = $normalizedRoot + [System.IO.Path]::DirectorySeparatorChar
    return $normalizedPath.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoReparseEscape {
    param([Parameter(Mandatory = $true)][System.IO.FileSystemInfo]$Item, [Parameter(Mandatory = $true)][string]$Root)
    $normalizedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $normalizedItemPath = [System.IO.Path]::GetFullPath($Item.FullName)
    if (-not (Test-PathWithinRoot -Path $normalizedItemPath -Root $normalizedRoot)) {
        throw 'Inbound source path did not resolve beneath the approved root.'
    }

    $current = $Item
    while ($true) {
        if ($null -eq $current) {
            throw 'Inbound source path did not resolve beneath the approved root.'
        }
        if (($current.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse point is not allowed in inbound source path: $($current.FullName)"
        }
        $currentFullName = [System.IO.Path]::GetFullPath($current.FullName).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
        if ($currentFullName.Equals($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return
        }

        if ($current -is [System.IO.FileInfo]) {
            $current = $current.Directory
        } elseif ($current -is [System.IO.DirectoryInfo]) {
            $current = $current.Parent
        } else {
            throw 'Inbound source path did not resolve beneath the approved root.'
        }
    }
}

function Mask-Identifier {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    if ($Value.Length -le 7) { return '***' }
    return $Value.Substring(0, 3) + '***' + $Value.Substring($Value.Length - 4)
}

function Normalize-ContentType {
    param([AllowEmptyString()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return ($Value.Split(';', 2)[0].Trim().ToLowerInvariant())
}

function New-IngestValidationFailure {
    param(
        [Parameter(Mandatory = $true)][string]$ErrorCode,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Extension,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$NormalizedContentType,
        [Parameter(Mandatory = $true)][string]$DetectedKind,
        [Parameter(Mandatory = $true)][string]$ExpectedKind,
        [Parameter(Mandatory = $true)][string]$MessageId
    )
    return [pscustomobject]@{
        error_code = $ErrorCode
        extension = $Extension
        normalized_content_type = $NormalizedContentType
        detected_kind = $DetectedKind
        expected_kind = $ExpectedKind
        message_id = $MessageId
    }
}

function Throw-IngestValidationFailure {
    param([Parameter(Mandatory = $true)][psobject]$Failure)
    throw ($Failure | ConvertTo-Json -Compress)
}

function Throw-IngestError {
    param([Parameter(Mandatory = $true)][string]$ErrorCode)
    throw (([pscustomobject]@{ error_code = $ErrorCode } | ConvertTo-Json -Compress))
}

function Set-ReceiptValue {
    param(
        [Parameter(Mandatory = $true)][psobject]$Receipt,
        [Parameter(Mandatory = $true)][string]$Name,
        $Value
    )
    $property = $Receipt.PSObject.Properties[$Name]
    if ($null -eq $property) {
        $Receipt | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
        return $true
    }
    if ($property.Value -ne $Value) {
        $property.Value = $Value
        return $true
    }
    return $false
}

function Remove-PartialStoredCopy {
    param(
        [Parameter(Mandatory = $true)][string]$StoredPath,
        [Parameter(Mandatory = $true)][string]$OriginalDirectory
    )
    if ((Test-Path -LiteralPath $StoredPath -PathType Leaf) -and (Test-PathWithinRoot -Path $StoredPath -Root $OriginalDirectory)) {
        Remove-Item -LiteralPath $StoredPath -Force -ErrorAction SilentlyContinue
    }
}

function Test-SafeOriginalFileName {
    param([Parameter(Mandatory = $true)][string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name) -or $Name -match '[\\/\x00-\x1F\x7F]') {
        return [pscustomobject]@{ success = $false; extension = ''; error_code = 'unsafe_file_name' }
    }
    if ([System.IO.Path]::GetFileName($Name) -ne $Name) {
        return [pscustomobject]@{ success = $false; extension = ''; error_code = 'unsafe_file_name' }
    }
    $extension = [System.IO.Path]::GetExtension($Name).ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($extension)) {
        return [pscustomobject]@{ success = $false; extension = ''; error_code = 'unsupported_extension' }
    }
    if ([System.IO.Path]::GetFileNameWithoutExtension($Name).Contains('.')) {
        return [pscustomobject]@{ success = $false; extension = $extension; error_code = 'unsafe_file_name' }
    }
    return [pscustomobject]@{ success = $true; extension = $extension; error_code = $null }
}

function Get-MediaProbeBytes {
    param([Parameter(Mandatory = $true)][string]$Path, [int]$Count = 16)
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $buffer = New-Object byte[] $Count
        $read = $stream.Read($buffer, 0, $buffer.Length)
        if ($read -eq 0) { return @() }
        if ($read -eq $buffer.Length) { return $buffer }
        return $buffer[0..($read - 1)]
    } finally {
        $stream.Dispose()
    }
}

function Test-FileContainsNulByte {
    param([Parameter(Mandatory = $true)][string]$Path)
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $buffer = New-Object byte[] 4096
        while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            for ($index = 0; $index -lt $read; $index++) {
                if ($buffer[$index] -eq 0) { return $true }
            }
        }
        return $false
    } finally {
        $stream.Dispose()
    }
}

function Get-DetectedMediaKind {
    param([Parameter(Mandatory = $true)][string]$Path)
    $bytes = @(Get-MediaProbeBytes -Path $Path)
    $pngSignature = @(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
    $isPng = $bytes.Length -ge 8
    if ($isPng) {
        for ($index = 0; $index -lt $pngSignature.Count; $index++) {
            if ($bytes[$index] -ne $pngSignature[$index]) { $isPng = $false; break }
        }
    }
    if ($isPng) { return 'png' }

    $isMp4 = $bytes.Length -ge 8 -and $bytes[4] -eq [byte][char]'f' -and $bytes[5] -eq [byte][char]'t' -and $bytes[6] -eq [byte][char]'y' -and $bytes[7] -eq [byte][char]'p'
    if ($isMp4) {
        $boxSize = ([uint64]$bytes[0] * 16777216) + ([uint64]$bytes[1] * 65536) + ([uint64]$bytes[2] * 256) + [uint64]$bytes[3]
        if ($boxSize -ge 8) { return 'mp4' }
    }

    $isWav = $bytes.Length -ge 12 -and
        $bytes[0] -eq [byte][char]'R' -and $bytes[1] -eq [byte][char]'I' -and
        $bytes[2] -eq [byte][char]'F' -and $bytes[3] -eq [byte][char]'F' -and
        $bytes[8] -eq [byte][char]'W' -and $bytes[9] -eq [byte][char]'A' -and
        $bytes[10] -eq [byte][char]'V' -and $bytes[11] -eq [byte][char]'E'
    if ($isWav) { return 'audio' }

    $isOgg = $bytes.Length -ge 4 -and
        $bytes[0] -eq [byte][char]'O' -and $bytes[1] -eq [byte][char]'g' -and
        $bytes[2] -eq [byte][char]'g' -and $bytes[3] -eq [byte][char]'S'
    if ($isOgg) { return 'audio' }

    $isMp3 = $bytes.Length -ge 3 -and
        (($bytes[0] -eq [byte][char]'I' -and $bytes[1] -eq [byte][char]'D' -and $bytes[2] -eq [byte][char]'3') -or
         ($bytes[0] -eq 0xFF -and ($bytes[1] -band 0xE0) -eq 0xE0))
    if ($isMp3) { return 'audio' }

    if (Test-FileContainsNulByte -Path $Path) { return 'binary' }
    return 'txt'
}

function Test-MediaTypeConsistency {
    param(
        [Parameter(Mandatory = $true)][string]$Extension,
        [Parameter(Mandatory = $true)][string]$NormalizedContentType,
        [Parameter(Mandatory = $true)][string]$DetectedKind
    )
    $expectedKind = switch ($Extension) {
        '.txt' { 'txt' }
        '.png' { 'png' }
        '.mp4' { 'mp4' }
        '.wav' { 'audio' }
        '.mp3' { 'audio' }
        '.ogg' { 'audio' }
        '.opus' { 'audio' }
        default { return [pscustomobject]@{ success = $true; expected_kind = ''; error_code = $null } }
    }
    if ($DetectedKind -eq 'binary' -and $expectedKind -eq 'txt') {
        return [pscustomobject]@{ success = $false; expected_kind = $expectedKind; error_code = 'binary_text_rejected' }
    }
    if ($DetectedKind -ne $expectedKind) {
        return [pscustomobject]@{ success = $false; expected_kind = $expectedKind; error_code = 'signature_mismatch' }
    }
    $allowedContentTypes = @{
        txt = @('text/plain', 'application/octet-stream', '', 'unknown')
        png = @('image/png', 'application/octet-stream', '', 'unknown')
        mp4 = @('video/mp4', 'application/octet-stream', '', 'unknown')
        audio = @('audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/ogg', 'audio/opus', 'application/octet-stream', '', 'unknown')
    }
    if ($allowedContentTypes[$expectedKind] -notcontains $NormalizedContentType) {
        return [pscustomobject]@{ success = $false; expected_kind = $expectedKind; error_code = 'mime_conflict' }
    }
    return [pscustomobject]@{ success = $true; expected_kind = $expectedKind; error_code = $null }
}

$normalizedInboundRoot = Get-NormalizedAbsolutePath -Path $InboundRoot -Label 'InboundRoot'
$normalizedProjectRoot = Get-NormalizedAbsolutePath -Path $ProjectRoot -Label 'ProjectRoot'
$normalizedSourcePath = Get-NormalizedAbsolutePath -Path $SourcePath -Label 'SourcePath'

if (-not (Test-Path -LiteralPath $normalizedInboundRoot -PathType Container)) {
    throw "Approved inbound root does not exist: $normalizedInboundRoot"
}
if (-not (Test-PathWithinRoot -Path $normalizedSourcePath -Root $normalizedInboundRoot)) {
    throw 'SourcePath is outside the approved OpenClaw media/inbound root.'
}
if (-not (Test-Path -LiteralPath $normalizedSourcePath -PathType Leaf)) {
    Throw-IngestError -ErrorCode 'missing_source'
}

$sourceItem = Get-Item -LiteralPath $normalizedSourcePath -Force
Assert-NoReparseEscape -Item $sourceItem -Root $normalizedInboundRoot

$fileNameCheck = Test-SafeOriginalFileName -Name $OriginalFileName
if (-not $fileNameCheck.success) {
    Throw-IngestValidationFailure -Failure (New-IngestValidationFailure -ErrorCode $fileNameCheck.error_code -Extension $fileNameCheck.extension -NormalizedContentType (Normalize-ContentType -Value $ContentType) -DetectedKind 'unknown' -ExpectedKind 'unknown' -MessageId $MessageId)
}
if ($sourceItem.Length -gt $MaxBytes) {
    Throw-IngestError -ErrorCode 'file_too_large'
}

$extension = $fileNameCheck.extension
$contentTypeNormalized = Normalize-ContentType -Value $ContentType
$detectedKind = Get-DetectedMediaKind -Path $sourceItem.FullName
$mediaTypeCheck = Test-MediaTypeConsistency -Extension $extension -NormalizedContentType $contentTypeNormalized -DetectedKind $detectedKind
if (-not $mediaTypeCheck.success) {
    Throw-IngestValidationFailure -Failure (New-IngestValidationFailure -ErrorCode $mediaTypeCheck.error_code -Extension $extension -NormalizedContentType $contentTypeNormalized -DetectedKind $detectedKind -ExpectedKind $mediaTypeCheck.expected_kind -MessageId $MessageId)
}
$typePolicy = switch ($extension) {
    '.pdf' { if ($contentTypeNormalized -notmatch '^application/pdf($|;)') { throw 'A .pdf source requires application/pdf ContentType.' }; 'pdf-only-if-downstream-approved' }
    '.docx' { if ($contentTypeNormalized -notmatch '^application/vnd\.openxmlformats-officedocument\.wordprocessingml\.document($|;)') { throw 'A .docx source requires the Office Open XML document ContentType.' }; 'metadata-hash-copy-only' }
    '.txt' { 'metadata-hash-copy-only' }
    '.png' { 'metadata-hash-copy-only' }
    '.mp4' { 'metadata-hash-copy-only' }
    default { 'metadata-hash-copy-only' }
}

$sourceSizeBeforeHash = [Int64]$sourceItem.Length
$sourceModifiedBeforeHash = $sourceItem.LastWriteTimeUtc.Ticks
$declaredSizeBytesForReceipt = $null
if ($isDeclaredSizeTrusted) {
    if ($null -eq $DeclaredSizeBytes -or $DeclaredSizeSource -notin @('channel_attachment_metadata', 'download_content_length')) {
        Throw-IngestError -ErrorCode 'invalid_declared_size'
    }
    $declaredSizeBytesForReceipt = [Int64]$DeclaredSizeBytes
    if ($declaredSizeBytesForReceipt -ne $sourceSizeBeforeHash) {
        Throw-IngestError -ErrorCode 'trusted_declared_size_mismatch'
    }
}
$sha256 = (Get-FileHash -LiteralPath $sourceItem.FullName -Algorithm SHA256).Hash
$sourceAfterHash = Get-Item -LiteralPath $normalizedSourcePath -Force
if ([Int64]$sourceAfterHash.Length -ne $sourceSizeBeforeHash -or $sourceAfterHash.LastWriteTimeUtc.Ticks -ne $sourceModifiedBeforeHash) {
    Throw-IngestError -ErrorCode 'source_changed_during_read'
}
$maskedAccountId = Mask-Identifier $AccountId
$maskedChatId = Mask-Identifier $ChatId
$maskedSenderId = Mask-Identifier $SenderId
$messageRoot = Join-Path (Join-Path (Join-Path $normalizedProjectRoot 'input') 'feishu') $MessageId
if ($AttachmentIndex -ge 0) {
    $attachmentDir = Join-Path $messageRoot ('attachment-{0:D3}' -f $AttachmentIndex)
} else {
    $attachmentDir = $messageRoot
}
$originalDirectory = Join-Path $attachmentDir 'original'
$receiptPath = Join-Path $attachmentDir 'receipt.json'
$storedPath = Join-Path $originalDirectory $OriginalFileName
$normalizedMessageRoot = [System.IO.Path]::GetFullPath($messageRoot)
if (-not (Test-PathWithinRoot -Path $normalizedMessageRoot -Root (Join-Path (Join-Path $normalizedProjectRoot 'input') 'feishu'))) {
    throw 'Computed project storage path escapes input/feishu.'
}

if (Test-Path -LiteralPath $receiptPath -PathType Leaf) {
    $existingReceipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $existingSourceHash = if ($null -ne $existingReceipt.PSObject.Properties['source_sha256']) { $existingReceipt.source_sha256 } else { $existingReceipt.sha256 }
    if ($existingReceipt.message_id -ne $MessageId -or $existingSourceHash -ne $sha256 -or $existingReceipt.stored_path -ne $storedPath) {
        Throw-IngestError -ErrorCode 'idempotency_conflict'
    }
    if ([string]::IsNullOrWhiteSpace([string]$existingReceipt.trusted_root_id) -or $existingReceipt.trusted_root_id -ne $TrustedRootId) {
        Throw-IngestError -ErrorCode 'idempotency_conflict'
    }
    if (-not (Test-Path -LiteralPath $storedPath -PathType Leaf)) {
        Throw-IngestError -ErrorCode 'idempotency_conflict'
    }
    $storedItem = Get-Item -LiteralPath $storedPath -Force
    if ([Int64]$storedItem.Length -ne $sourceSizeBeforeHash) {
        Throw-IngestError -ErrorCode 'stored_size_mismatch'
    }
    $storedHash = (Get-FileHash -LiteralPath $storedPath -Algorithm SHA256).Hash
    if ($storedHash -ne $sha256) {
        Throw-IngestError -ErrorCode 'stored_hash_mismatch'
    }
    $receiptRepaired = $false
    foreach ($identityField in @('account_id', 'chat_id', 'sender_id')) {
        if ([string]::IsNullOrWhiteSpace([string]$existingReceipt.$identityField)) {
            $receiptRepaired = $true
        }
    }
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'declared_size_bytes' -Value $declaredSizeBytesForReceipt) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'declared_size_trusted' -Value $isDeclaredSizeTrusted) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'declared_size_source' -Value $(if ($isDeclaredSizeTrusted) { $DeclaredSizeSource } else { 'none' })) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'actual_size_bytes' -Value $sourceSizeBeforeHash) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'stored_size_bytes' -Value ([Int64]$storedItem.Length)) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'size_match' -Value $true) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'source_sha256' -Value $sha256) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'stored_sha256' -Value $storedHash) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'source_stable_during_read' -Value $true) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'untrusted_size_claim_bytes' -Value $(if ($hasUntrustedSizeClaim -and $untrustedSizeClaimIsValid) { $UntrustedSizeClaimBytes } else { $null })) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'untrusted_size_claim_present' -Value $hasUntrustedSizeClaim) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'untrusted_size_claim_valid' -Value $untrustedSizeClaimIsValid) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'untrusted_size_claim_source' -Value $UntrustedSizeClaimSource) -or $receiptRepaired
    $receiptRepaired = (Set-ReceiptValue -Receipt $existingReceipt -Name 'untrusted_size_claim_type' -Value $UntrustedSizeClaimType) -or $receiptRepaired
    if ($receiptRepaired) {
        $existingReceipt.account_id = $maskedAccountId
        $existingReceipt.chat_id = $maskedChatId
        $existingReceipt.sender_id = $maskedSenderId
        [System.IO.File]::WriteAllText($receiptPath, ($existingReceipt | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))
    } elseif ($existingReceipt.account_id -ne $maskedAccountId -or $existingReceipt.chat_id -ne $maskedChatId -or $existingReceipt.sender_id -ne $maskedSenderId) {
        throw 'MessageId receipt identity fields do not match this authorized route.'
    }
    [pscustomobject]@{ success = $true; idempotent = $true; receipt_repaired = $receiptRepaired; receipt_path = $receiptPath; stored_path = $storedPath; sha256 = $sha256; size_bytes = $sourceSizeBeforeHash; declared_size_bytes = $declaredSizeBytesForReceipt; declared_size_trusted = $isDeclaredSizeTrusted; declared_size_source = $(if ($isDeclaredSizeTrusted) { $DeclaredSizeSource } else { 'none' }); actual_size_bytes = $sourceSizeBeforeHash; stored_size_bytes = [Int64]$storedItem.Length; size_match = $true; source_sha256 = $sha256; stored_sha256 = $storedHash; source_stable_during_read = $true; detected_kind = $detectedKind; normalized_content_type = $contentTypeNormalized; attachment_index = $AttachmentIndex; trusted_root_id = $TrustedRootId; content_parsed = $false; quarantined = $true } | ConvertTo-Json -Compress
    exit 0
}

New-Item -ItemType Directory -Path $originalDirectory -Force | Out-Null
if (Test-Path -LiteralPath $storedPath -PathType Leaf) {
    Throw-IngestError -ErrorCode 'idempotency_conflict'
}
try {
    Copy-Item -LiteralPath $sourceItem.FullName -Destination $storedPath -ErrorAction Stop
    $storedItem = Get-Item -LiteralPath $storedPath -Force
    if ([Int64]$storedItem.Length -ne $sourceSizeBeforeHash) {
        Throw-IngestError -ErrorCode 'stored_size_mismatch'
    }
    $storedHash = (Get-FileHash -LiteralPath $storedItem.FullName -Algorithm SHA256).Hash
    if ($storedHash -ne $sha256) {
        Throw-IngestError -ErrorCode 'stored_hash_mismatch'
    }
    $sourceAfterCopy = Get-Item -LiteralPath $normalizedSourcePath -Force
    $sourceHashAfterCopy = (Get-FileHash -LiteralPath $sourceAfterCopy.FullName -Algorithm SHA256).Hash
    if ([Int64]$sourceAfterCopy.Length -ne $sourceSizeBeforeHash -or $sourceAfterCopy.LastWriteTimeUtc.Ticks -ne $sourceModifiedBeforeHash -or $sourceHashAfterCopy -ne $sha256) {
        Throw-IngestError -ErrorCode 'source_changed_during_read'
    }
} catch {
    Remove-PartialStoredCopy -StoredPath $storedPath -OriginalDirectory $originalDirectory
    throw
}
$storedItem.IsReadOnly = $true

if ([string]::IsNullOrWhiteSpace($ReceivedAt)) {
    $ReceivedAt = (Get-Date).ToString('o')
}
$receipt = [ordered]@{
    channel = 'feishu'
    trusted_root_id = $TrustedRootId
    source_root_match = $true
    account_id = $maskedAccountId
    chat_id = $maskedChatId
    sender_id = $maskedSenderId
    message_id = $MessageId
    attachment_index = if ($AttachmentIndex -ge 0) { $AttachmentIndex } else { $null }
    attachment_count = $AttachmentCount
    event_id = $EventId
    original_name = $OriginalFileName
    canonical_source_path = $CanonicalSourcePath
    stored_path = $storedItem.FullName
    content_type = $ContentType
    extension = $extension
    detected_kind = $detectedKind
    size_bytes = [Int64]$storedItem.Length
    sha256 = $sha256
    declared_size_bytes = $declaredSizeBytesForReceipt
    declared_size_trusted = $isDeclaredSizeTrusted
    declared_size_source = if ($isDeclaredSizeTrusted) { $DeclaredSizeSource } else { 'none' }
    actual_size_bytes = $sourceSizeBeforeHash
    stored_size_bytes = [Int64]$storedItem.Length
    size_match = $true
    source_sha256 = $sha256
    stored_sha256 = $storedHash
    source_stable_during_read = $true
    untrusted_size_claim_bytes = if ($hasUntrustedSizeClaim -and $untrustedSizeClaimIsValid) { $UntrustedSizeClaimBytes } else { $null }
    untrusted_size_claim_present = $hasUntrustedSizeClaim
    untrusted_size_claim_valid = $untrustedSizeClaimIsValid
    untrusted_size_claim_source = $UntrustedSizeClaimSource
    untrusted_size_claim_type = $UntrustedSizeClaimType
    source_created_at = $sourceItem.CreationTimeUtc.ToString('o')
    source_modified_at = $sourceItem.LastWriteTimeUtc.ToString('o')
    received_at = $ReceivedAt
    quarantined = $true
    content_parsed = $false
    analysis_allowed = $true
    processing_policy = $typePolicy
}
[System.IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{ success = $true; idempotent = $false; receipt_path = $receiptPath; stored_path = $storedPath; sha256 = $sha256; size_bytes = [Int64]$storedItem.Length; declared_size_bytes = $declaredSizeBytesForReceipt; declared_size_trusted = $isDeclaredSizeTrusted; declared_size_source = if ($isDeclaredSizeTrusted) { $DeclaredSizeSource } else { 'none' }; actual_size_bytes = $sourceSizeBeforeHash; stored_size_bytes = [Int64]$storedItem.Length; size_match = $true; source_sha256 = $sha256; stored_sha256 = $storedHash; source_stable_during_read = $true; detected_kind = $detectedKind; normalized_content_type = $contentTypeNormalized; attachment_index = $AttachmentIndex; trusted_root_id = $TrustedRootId; content_parsed = $false; quarantined = $true } | ConvertTo-Json -Compress
