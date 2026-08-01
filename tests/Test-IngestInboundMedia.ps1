$ErrorActionPreference = 'Stop'
$scriptUnderTest = Join-Path $PSScriptRoot '..\scripts\07_ingest_inbound_media.ps1'
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\feishu_delivery'

Describe '07_ingest_inbound_media.ps1' {
    BeforeEach {
        $root = Join-Path $TestDrive 'case'
        $inbound = Join-Path $root 'openclaw\media\inbound'
        $project = Join-Path $root 'project'
        New-Item -ItemType Directory -Path $inbound -Force | Out-Null
        New-Item -ItemType Directory -Path $project -Force | Out-Null
        $script:Root = $root
        $script:Inbound = $inbound
        $script:Project = $project
    }

    function Copy-Fixture([string]$FixtureName, [string]$DestinationName = '', [string]$DestinationDirectory = '') {
        if ([string]::IsNullOrWhiteSpace($DestinationName)) { $DestinationName = $FixtureName }
        if ([string]::IsNullOrWhiteSpace($DestinationDirectory)) { $DestinationDirectory = $script:Inbound }
        $destination = Join-Path $DestinationDirectory $DestinationName
        Copy-Item -LiteralPath (Join-Path $fixtureRoot $FixtureName) -Destination $destination
        return $destination
    }

    function Invoke-Ingest([string]$Source, [string]$MessageId, [string]$Name, [Int64]$MaxBytes = 5242880, [string]$ContentType = 'text/plain') {
        & $scriptUnderTest -SourcePath $Source -MessageId $MessageId -OriginalFileName $Name -ContentType $ContentType -MaxBytes $MaxBytes -InboundRoot $script:Inbound -ProjectRoot $script:Project -AccountId 'zhongshu' -ChatId 'oc_test1234' -SenderId 'ou_test1234' | ConvertFrom-Json
    }

    function Get-IngestValidationFailure([string]$Source, [string]$MessageId, [string]$Name, [string]$ContentType, [Int64]$MaxBytes = 5242880) {
        try {
            & $scriptUnderTest -SourcePath $Source -MessageId $MessageId -OriginalFileName $Name -ContentType $ContentType -MaxBytes $MaxBytes -InboundRoot $script:Inbound -ProjectRoot $script:Project -AccountId 'zhongshu' -ChatId 'oc_test1234' -SenderId 'ou_test1234' | Out-Null
        } catch {
            return $_.Exception.Message | ConvertFrom-Json
        }
        throw 'Expected ingest validation failure.'
    }

    function Assert-NoSuccessReceipt([string]$MessageId) {
        (Test-Path -LiteralPath (Join-Path $script:Project "input\feishu\$MessageId\original")) | Should Be $false
        (Test-Path -LiteralPath (Join-Path $script:Project "input\feishu\$MessageId\receipt.json")) | Should Be $false
    }

    It 'copies a normal TXT fixture and writes a safe receipt' {
        $source = Copy-Fixture 'p0-file-test.txt' 'normal.txt'
        $result = Invoke-Ingest $source 'om_normal123' 'normal.txt'
        $result.success | Should Be $true
        $result.idempotent | Should Be $false
        Test-Path -LiteralPath $result.stored_path | Should Be $true
        $receipt = Get-Content -LiteralPath $result.receipt_path -Raw -Encoding UTF8 | ConvertFrom-Json
        $receipt.content_parsed | Should Be $false
        $receipt.quarantined | Should Be $true
        $receipt.account_id | Should Not Be 'zhongshu'
    }

    It 'accepts a Chinese TXT fixture filename via LiteralPath' {
        $source = Copy-Fixture 'p0-file-test.txt' '中文文件.txt'
        $result = Invoke-Ingest $source 'om_chinese123' '中文文件.txt'
        (Split-Path -Leaf $result.stored_path) | Should Be '中文文件.txt'
    }

    It 'rejects a source path outside inbound root' {
        $outside = Join-Path $script:Root 'outside.txt'
        Copy-Item -LiteralPath (Join-Path $fixtureRoot 'p0-file-test.txt') -Destination $outside
        { Invoke-Ingest $outside 'om_traversal123' 'outside.txt' } | Should Throw
    }

    It 'rejects a missing source file' {
        { Invoke-Ingest (Join-Path $script:Inbound 'missing.txt') 'om_missing123' 'missing.txt' } | Should Throw
    }

    It 'rejects an over-size source' {
        $source = Copy-Fixture 'p0-file-test.txt' 'large.txt'
        { Invoke-Ingest $source 'om_large123' 'large.txt' 1 } | Should Throw
    }

    It 'rejects a mismatched TXT extension and ContentType' {
        $source = Copy-Fixture 'p0-file-test.txt' 'wrong.txt'
        { Invoke-Ingest $source 'om_type123' 'wrong.txt' 5242880 'video/mp4' } | Should Throw
    }

    It 'requires an authorized route identity for every receipt' {
        $source = Copy-Fixture 'p0-file-test.txt' 'identity.txt'
        { & $scriptUnderTest -SourcePath $source -MessageId 'om_identity123' -OriginalFileName 'identity.txt' -ContentType 'text/plain' -MaxBytes 5242880 -InboundRoot $script:Inbound -ProjectRoot $script:Project -AccountId 'zhongshu' -ChatId '' -SenderId 'ou_test1234' } | Should Throw
    }

    It 'is idempotent for the same message id and source hash' {
        $source = Copy-Fixture 'p0-file-test.txt' 'again.txt'
        $first = Invoke-Ingest $source 'om_repeat123' 'again.txt'
        $second = Invoke-Ingest $source 'om_repeat123' 'again.txt'
        $first.idempotent | Should Be $false
        $second.idempotent | Should Be $true
        $second.sha256 | Should Be $first.sha256
    }

    It 'accepts TXT with application/octet-stream' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-file-test.txt' 'octet.txt') 'om_txtoctet123' 'octet.txt' 5242880 'application/octet-stream'
        $result.success | Should Be $true
    }

    It 'rejects a TXT extension with PNG content' {
        $messageId = 'om_txtpng123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-image-test.png' 'pretends.txt') $messageId 'pretends.txt' 'text/plain'
        $failure.error_code | Should Be 'signature_mismatch'
        $failure.detected_kind | Should Be 'png'
        $failure.expected_kind | Should Be 'txt'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a TXT fixture containing a NUL byte' {
        $source = Copy-Fixture 'p0-file-test.txt' 'with-nul.txt'
        [System.IO.File]::WriteAllBytes($source, ([System.IO.File]::ReadAllBytes($source) + [byte]0))
        $messageId = 'om_txtnul123'
        $failure = Get-IngestValidationFailure $source $messageId 'with-nul.txt' 'text/plain'
        $failure.error_code | Should Be 'binary_text_rejected'
        $failure.detected_kind | Should Be 'binary'
        Assert-NoSuccessReceipt $messageId
    }

    It 'accepts a PNG fixture with image/png' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-image-test.png') 'om_pngplain123' 'p0-image-test.png' 5242880 'image/png'
        $result.success | Should Be $true
    }

    It 'accepts a PNG fixture with application/octet-stream' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-image-test.png' 'octet.png') 'om_pngoctet123' 'octet.png' 5242880 'application/octet-stream'
        $result.success | Should Be $true
    }

    It 'rejects a PNG fixture declared as text/plain' {
        $messageId = 'om_pngtext123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-image-test.png') $messageId 'p0-image-test.png' 'text/plain'
        $failure.error_code | Should Be 'mime_conflict'
        $failure.detected_kind | Should Be 'png'
        $failure.expected_kind | Should Be 'png'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a PNG fixture declared as image/jpeg' {
        $messageId = 'om_pngjpeg123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-image-test.png') $messageId 'p0-image-test.png' 'image/jpeg'
        $failure.error_code | Should Be 'mime_conflict'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a PNG extension with an invalid signature' {
        $source = Copy-Fixture 'p0-image-test.png' 'bad.png'
        $bytes = [System.IO.File]::ReadAllBytes($source)
        $bytes[0] = 0
        [System.IO.File]::WriteAllBytes($source, $bytes)
        $messageId = 'om_pngsig123'
        $failure = Get-IngestValidationFailure $source $messageId 'bad.png' 'image/png'
        $failure.error_code | Should Be 'signature_mismatch'
        Assert-NoSuccessReceipt $messageId
    }

    It 'normalizes PNG ContentType parameters and case' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-image-test.png' 'normalized.png') 'om_pngnorm123' 'normalized.png' 5242880 'IMAGE/PNG; charset=binary'
        $result.success | Should Be $true
    }

    It 'accepts an MP4 fixture with video/mp4' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-video-test.mp4') 'om_mp4plain123' 'p0-video-test.mp4' 5242880 'video/mp4'
        $result.success | Should Be $true
    }

    It 'accepts an MP4 fixture with application/octet-stream' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-video-test.mp4' 'octet.mp4') 'om_mp4octet123' 'octet.mp4' 5242880 'application/octet-stream'
        $result.success | Should Be $true
    }

    It 'rejects an MP4 fixture declared as image/png' {
        $messageId = 'om_mp4image123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-video-test.mp4') $messageId 'p0-video-test.mp4' 'image/png'
        $failure.error_code | Should Be 'mime_conflict'
        $failure.detected_kind | Should Be 'mp4'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects an MP4 extension without an ftyp box' {
        $messageId = 'om_mp4sig123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-file-test.txt' 'bad.mp4') $messageId 'bad.mp4' 'video/mp4'
        $failure.error_code | Should Be 'signature_mismatch'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a double extension before copying a fixture' {
        $messageId = 'om_double123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-image-test.png') $messageId 'file.png.exe' 'image/png'
        $failure.error_code | Should Be 'unsafe_file_name'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a filename containing a path separator before copying a fixture' {
        $messageId = 'om_separator123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-image-test.png') $messageId 'folder\file.png' 'image/png'
        $failure.error_code | Should Be 'unsafe_file_name'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a filename containing a control character before copying a fixture' {
        $messageId = 'om_control123'
        $failure = Get-IngestValidationFailure (Copy-Fixture 'p0-image-test.png') $messageId ("control$([char]1).png") 'image/png'
        $failure.error_code | Should Be 'unsafe_file_name'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a reparse-point escape derived from a TXT fixture' {
        $outside = Join-Path $script:Root 'outside'
        New-Item -ItemType Directory -Path $outside -Force | Out-Null
        Copy-Fixture 'p0-file-test.txt' 'linked.txt' $outside | Out-Null
        $junction = Join-Path $script:Inbound 'escape'
        New-Item -ItemType Junction -Path $junction -Target $outside | Out-Null
        { Invoke-Ingest (Join-Path $junction 'linked.txt') 'om_reparse123' 'linked.txt' } | Should Throw
        Assert-NoSuccessReceipt 'om_reparse123'
    }

    It 'walks a nested staging directory to the exact approved root' {
        $staging = Join-Path $script:Inbound 'openclaw-staged-test\nested'
        New-Item -ItemType Directory -Path $staging -Force | Out-Null
        $source = Copy-Fixture 'p0-file-test.txt' 'nested.txt' $staging
        $result = Invoke-Ingest $source 'om_nested123' 'nested.txt'
        $result.success | Should Be $true
    }

    It 'rejects a separator-prefix sibling such as safe2 for safe' {
        $prefixSibling = $script:Inbound + '2'
        New-Item -ItemType Directory -Path $prefixSibling -Force | Out-Null
        $source = Copy-Fixture 'p0-file-test.txt' 'prefix.txt' $prefixSibling
        { Invoke-Ingest $source 'om_prefix123' 'prefix.txt' } | Should Throw
        Assert-NoSuccessReceipt 'om_prefix123'
    }

    It 'rejects an approved root that is itself a reparse point' {
        $realInbound = Join-Path $script:Root 'real-inbound'
        New-Item -ItemType Directory -Path $realInbound -Force | Out-Null
        $source = Copy-Fixture 'p0-file-test.txt' 'root-link.txt' $realInbound
        $linkedRoot = Join-Path $script:Root 'linked-inbound'
        New-Item -ItemType Junction -Path $linkedRoot -Target $realInbound | Out-Null
        { & $scriptUnderTest -SourcePath (Join-Path $linkedRoot 'root-link.txt') -MessageId 'om_rootlink123' -OriginalFileName 'root-link.txt' -ContentType 'text/plain' -MaxBytes 5242880 -InboundRoot $linkedRoot -ProjectRoot $script:Project -AccountId 'zhongshu' -ChatId 'oc_test1234' -SenderId 'ou_test1234' } | Should Throw
        Assert-NoSuccessReceipt 'om_rootlink123'
    }

    It 'rejects a source item that is itself a reparse point without file-symlink privilege' {
        $tokens = $null
        $parseErrors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($scriptUnderTest, [ref]$tokens, [ref]$parseErrors)
        $parseErrors.Count | Should Be 0
        $functionNames = @('Test-PathWithinRoot', 'Assert-NoReparseEscape')
        $definitions = $ast.FindAll({
            param($node)
            $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $functionNames -contains $node.Name
        }, $true)
        . ([scriptblock]::Create(($definitions.Extent.Text -join [Environment]::NewLine)))

        $target = Join-Path $script:Root 'source-item-target'
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        $sourceJunction = Join-Path $script:Inbound 'source-item-link'
        New-Item -ItemType Junction -Path $sourceJunction -Target $target | Out-Null
        { Assert-NoReparseEscape -Item (Get-Item -LiteralPath $sourceJunction -Force) -Root $script:Inbound } | Should Throw
    }

    It 'records equal SHA-256 values for a successful PNG quarantine copy' {
        $source = Copy-Fixture 'p0-image-test.png' 'hash.png'
        $result = Invoke-Ingest $source 'om_hash123' 'hash.png' 5242880 'image/png'
        (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash | Should Be (Get-FileHash -LiteralPath $result.stored_path -Algorithm SHA256).Hash
    }

    It 'accepts a correctly signed PNG with unknown ContentType only after signature detection' {
        $result = Invoke-Ingest (Copy-Fixture 'p0-image-test.png' 'unknown.png') 'om_pngunknown123' 'unknown.png' 5242880 'unknown'
        $result.success | Should Be $true
    }

    It 'records the complete trusted-size receipt contract' {
        $source = Copy-Fixture 'p0-file-test.txt' 'size-contract.txt'
        $result = Invoke-Ingest $source 'om_sizecontract123' 'size-contract.txt'
        $receipt = Get-Content -LiteralPath $result.receipt_path -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($name in @('declared_size_bytes', 'declared_size_trusted', 'declared_size_source', 'actual_size_bytes', 'stored_size_bytes', 'size_match', 'source_sha256', 'stored_sha256', 'source_stable_during_read', 'trusted_root_id')) {
            ($receipt.PSObject.Properties.Name -contains $name) | Should Be $true
        }
        $receipt.actual_size_bytes | Should Be $receipt.stored_size_bytes
        $receipt.source_sha256 | Should Be $receipt.stored_sha256
    }

    It 'rejects a trusted declared-size mismatch before creating a receipt' {
        $source = Copy-Fixture 'p0-file-test.txt' 'trusted-size.txt'
        $messageId = 'om_trustedsize123'
        try {
            & $scriptUnderTest -SourcePath $source -MessageId $messageId -OriginalFileName 'trusted-size.txt' -ContentType 'text/plain' -MaxBytes 5242880 -InboundRoot $script:Inbound -ProjectRoot $script:Project -AccountId 'zhongshu' -ChatId 'oc_test1234' -SenderId 'ou_test1234' -DeclaredSizeBytes 1 -DeclaredSizeTrusted '1' -DeclaredSizeSource 'download_content_length' | Out-Null
            throw 'Expected trusted declared-size mismatch.'
        } catch {
            $failure = $_.Exception.Message | ConvertFrom-Json
        }
        $failure.error_code | Should Be 'trusted_declared_size_mismatch'
        Assert-NoSuccessReceipt $messageId
    }

    It 'rejects a partial quarantined copy by stored size and removes the file' {
        $source = Copy-Fixture 'p0-file-test.txt' 'partial.txt'
        $messageId = 'om_partialcopy123'
        Mock Copy-Item {
            param($LiteralPath, $Destination)
            [System.IO.File]::WriteAllBytes($Destination, [byte[]]@(1, 2))
        } -ParameterFilter { $Destination -like '*\original\*' }
        $failure = Get-IngestValidationFailure $source $messageId 'partial.txt' 'text/plain'
        $failure.error_code | Should Be 'stored_size_mismatch'
        (Test-Path -LiteralPath (Join-Path $script:Project "input\feishu\$messageId\original\partial.txt")) | Should Be $false
        (Test-Path -LiteralPath (Join-Path $script:Project "input\feishu\$messageId\receipt.json")) | Should Be $false
    }

    It 'rejects an equal-size quarantined copy with a different SHA-256' {
        $source = Copy-Fixture 'p0-file-test.txt' 'hash-mismatch.txt'
        $messageId = 'om_hashmismatch123'
        (Get-Item -LiteralPath $source).Length | Should Be 55
        Mock Copy-Item {
            param($LiteralPath, $Destination)
            [System.IO.File]::WriteAllBytes($Destination, [byte[]]::new(55))
        } -ParameterFilter { $Destination -like '*\original\*' }
        $failure = Get-IngestValidationFailure $source $messageId 'hash-mismatch.txt' 'text/plain'
        $failure.error_code | Should Be 'stored_hash_mismatch'
        (Test-Path -LiteralPath (Join-Path $script:Project "input\feishu\$messageId\original\hash-mismatch.txt")) | Should Be $false
        (Test-Path -LiteralPath (Join-Path $script:Project "input\feishu\$messageId\receipt.json")) | Should Be $false
    }

    It 'keeps inbound originals and receipts Git-ignored' {
        $repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
        & git -C $repoRoot check-ignore --quiet --no-index -- 'input/feishu/om_gitignore123/original/p0-file-test.txt'
        $LASTEXITCODE | Should Be 0
        & git -C $repoRoot check-ignore --quiet --no-index -- 'input/feishu/om_gitignore123/receipt.json'
        $LASTEXITCODE | Should Be 0
    }

}
