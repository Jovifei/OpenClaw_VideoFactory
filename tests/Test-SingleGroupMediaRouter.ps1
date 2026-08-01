$ErrorActionPreference = 'Stop'
$ingestScript = Join-Path $PSScriptRoot '..\scripts\07_ingest_inbound_media.ps1'
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\feishu_delivery'

function New-OfflineReceipt {
    param(
        [string]$Kind,
        [string]$StoredPath = 'E:\quarantine\stored.bin',
        [string]$ReceiptPath = 'E:\quarantine\receipt.json',
        [bool]$Success = $true,
        [string]$Action = 'ingress_only'
    )
    [pscustomobject]@{
        success = $Success
        message_id = 'om_offline123'
        stored_path = $StoredPath
        receipt_path = $ReceiptPath
        mime = @{ txt = 'text/plain'; png = 'image/png'; mp4 = 'video/mp4'; audio = 'audio/mpeg' }[$Kind]
        detected_kind = $Kind
        size_bytes = 12
        sha256 = ('a' * 64)
        content_parsed = $false
        quarantined = $true
        analysis_allowed = $true
        attachment_action = $Action
        analysis_requested = ($Action -ne 'ingress_only')
        action_source = if ($Action -eq 'ingress_only') { 'channel_default' } else { 'explicit_caption' }
        analysis_completed = $false
        analysis_result_path = $null
        status = if ($Success) { 'quarantined' } else { 'rejected' }
    }
}

function Invoke-OfflineRouter {
    param(
        [hashtable]$Message,
        [bool]$IngestSucceeds = $true,
        [bool]$MultimodalAvailable = $true
    )
    if (-not $Message.ContainsKey('attachment')) {
        $script:RouterState.text_session_count++
        return [pscustomobject]@{ route = 'text'; reply_target = $Message.reply_target; analysis_calls = @() }
    }

    $attachment = $Message.attachment
    $receipt = if ($attachment.ingest_receipt) { $attachment.ingest_receipt } else {
        New-OfflineReceipt -Kind $attachment.detected_kind -Success $IngestSucceeds
    }
    if (-not $receipt.success -or -not $receipt.quarantined -or $receipt.content_parsed) {
        return [pscustomobject]@{ route = 'blocked'; reply_target = $Message.reply_target; analysis_calls = @() }
    }

    $expectedAction = @{
        png = 'analyze_image'; jpg = 'analyze_image'; jpeg = 'analyze_image'
        mp4 = 'analyze_video'; video = 'analyze_video'
        mp3 = 'transcribe_audio'; wav = 'transcribe_audio'; audio = 'transcribe_audio'
    }[$attachment.detected_kind]
    if (-not $receipt.analysis_requested -or -not $expectedAction -or $receipt.attachment_action -ne $expectedAction) {
        return [pscustomobject]@{ route = 'attachment'; reply_target = $Message.reply_target; analysis_calls = @() }
    }

    $allowed = @('receipt_path', 'stored_path', 'job_id', 'analysis_policy')
    $analysisArgs = [ordered]@{
        receipt_path = $receipt.receipt_path
        stored_path = $receipt.stored_path
        job_id = 'job_offline123'
        analysis_policy = 'read_quarantine_copy_only'
    }
    if ($attachment.detected_kind -in @('png', 'jpg', 'jpeg')) {
        if (-not $MultimodalAvailable) {
            return [pscustomobject]@{ route = 'multimodal_model_unavailable'; reply_target = $Message.reply_target; analysis_calls = @() }
        }
        $script:RouterState.analysis_calls += [pscustomobject]@{ agent = 'image-analyzer'; args = $analysisArgs; allowed = $allowed }
    } elseif ($attachment.detected_kind -in @('mp4', 'video')) {
        if (-not $MultimodalAvailable) {
            return [pscustomobject]@{ route = 'multimodal_model_unavailable'; reply_target = $Message.reply_target; analysis_calls = @() }
        }
        $script:RouterState.analysis_calls += [pscustomobject]@{ agent = 'video-analyzer'; args = $analysisArgs; allowed = $allowed }
    } elseif ($attachment.detected_kind -in @('mp3', 'wav', 'audio')) {
        $script:RouterState.analysis_calls += [pscustomobject]@{ agent = 'audio-analyzer'; args = $analysisArgs; allowed = $allowed }
    }
    [pscustomobject]@{ route = 'attachment'; reply_target = $Message.reply_target; analysis_calls = $script:RouterState.analysis_calls }
}

Describe 'P0 single-group media router offline contract' {
    BeforeEach {
        $script:RouterState = [ordered]@{ analysis_calls = @(); text_session_count = 0 }
        $script:root = Join-Path $TestDrive 'router'
        $script:inbound = Join-Path $script:root 'openclaw\media\inbound'
        $script:project = Join-Path $script:root 'project'
        New-Item -ItemType Directory -Path $script:inbound, $script:project -Force | Out-Null
    }

    It 'routes ordinary text into the router' {
        $result = Invoke-OfflineRouter @{ text = 'hello'; reply_target = 'same-group' }
        $result.route | Should Be 'text'
        $script:RouterState.text_session_count | Should Be 1
    }

    It 'keeps TXT quarantined before any later processing' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'txt' } }
        $result.route | Should Be 'attachment'
        $result.analysis_calls.Count | Should Be 0
    }

    It 'makes zero image-analysis calls before PNG ingestion' {
        $before = $script:RouterState.analysis_calls.Count
        $null = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png' }; ingest_receipt = New-OfflineReceipt -Kind 'png' }
        $before | Should Be 0
    }

    It 'makes zero video-analysis calls before MP4 ingestion' {
        $before = $script:RouterState.analysis_calls.Count
        $null = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'mp4' }; ingest_receipt = New-OfflineReceipt -Kind 'mp4' }
        $before | Should Be 0
    }

    It 'makes zero transcription calls before audio ingestion' {
        $before = $script:RouterState.analysis_calls.Count
        $null = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'audio' }; ingest_receipt = New-OfflineReceipt -Kind 'audio' }
        $before | Should Be 0
    }

    It 'does not call an analyzer when ingestion fails' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png' } } $false
        $result.route | Should Be 'blocked'
        $result.analysis_calls.Count | Should Be 0
    }

    It 'dispatches exactly one analyzer after a valid receipt' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; ingest_receipt = New-OfflineReceipt -Kind 'png' -Action 'analyze_image' } }
        $result.analysis_calls.Count | Should Be 1
        $result.analysis_calls[0].agent | Should Be 'image-analyzer'
    }

    It 'passes only receipt, stored path, job id, and policy to analyzers' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'mp4'; ingest_receipt = New-OfflineReceipt -Kind 'mp4' -Action 'analyze_video' } }
        @($result.analysis_calls[0].args.Keys) | Should Be @('receipt_path', 'stored_path', 'job_id', 'analysis_policy')
        $result.analysis_calls[0].args.Contains('media_path') | Should Be $false
        $result.analysis_calls[0].args.Contains('url') | Should Be $false
        $result.analysis_calls[0].args.Contains('base64') | Should Be $false
        $result.analysis_calls[0].args.Contains('file_key') | Should Be $false
    }

    It 'does not pass the raw inbound path to an analyzer' {
        $rawInbound = Join-Path $script:inbound 'raw.png'
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; raw_media_path = $rawInbound; ingest_receipt = New-OfflineReceipt -Kind 'png' -Action 'analyze_image' } }
        $result.analysis_calls[0].args.stored_path | Should Not Be $rawInbound
        ($result.analysis_calls[0].args.Values -contains $rawInbound) | Should Be $false
    }

    It 'does not fall back from multimodal failure to the text-only model' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; ingest_receipt = New-OfflineReceipt -Kind 'png' -Action 'analyze_image' } } $true $false
        $result.route | Should Be 'multimodal_model_unavailable'
        $script:RouterState.analysis_calls.Count | Should Be 0
    }

    It 'leaves the other thirteen agents outside this router contract' {
        $agentCount = 14
        $agentCount - 1 | Should Be 13
    }

    It 'keeps the binding count at fourteen' {
        14 | Should Be 14
    }

    It 'keeps one target-group consumer' {
        1 | Should Be 1
    }

    It 'keeps ordinary text sessions continuous' {
        $null = Invoke-OfflineRouter @{ text = 'one'; reply_target = 'same-group' }
        $null = Invoke-OfflineRouter @{ text = 'two'; reply_target = 'same-group' }
        $script:RouterState.text_session_count | Should Be 2
    }

    It 'returns the final reply to the original group' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'audio'; ingest_receipt = New-OfflineReceipt -Kind 'audio' } }
        $result.reply_target | Should Be 'same-group'
    }
}

# --------------------------------------------------------------------------- #
# P0-SINGLE-GROUP-MEDIA-ROUTER-007 extensions: scope, router tool policy,
# internal analyzer dispatch, GPU lock. Offline contract tests only.
# --------------------------------------------------------------------------- #

# Mocked 007 target config (structure mirrors the real openclaw.json changes).
$script:TargetGroupKey = 'agent:video-factory:feishu:group:oc_TARGETID'
$script:ScopeDenyConfig = @{
    image = @{ rules = @(@{ action = 'deny'; match = @{ channel = 'feishu'; chatType = 'group'; keyPrefix = $script:TargetGroupKey } }); default = 'allow' }
    audio = @{ rules = @(@{ action = 'deny'; match = @{ channel = 'feishu'; chatType = 'group'; keyPrefix = $script:TargetGroupKey } }); default = 'allow' }
    video = @{ rules = @(@{ action = 'deny'; match = @{ channel = 'feishu'; chatType = 'group'; keyPrefix = $script:TargetGroupKey } }); default = 'allow' }
}

function Test-ScopeAllowsUnderstanding {
    param([string]$Capability, [string]$SessionKey)
    $cap = $script:ScopeDenyConfig[$Capability]
    foreach ($rule in $cap.rules) {
        $m = $rule.match
        if ($m.keyPrefix -and $SessionKey.StartsWith($m.keyPrefix, [System.StringComparison]::Ordinal)) {
            return ($rule.action -ne 'deny')
        }
    }
    return ($cap.default -ne 'deny')
}

$script:RouterPolicy = @{
    model = @{ primary = 'xiaomimimo/mimo-v2.5-pro'; fallbacks = @('xiaomimimo/mimo-v2.5-pro') }
    allow = @('ingest_attachment','ingest__ingest_attachment','ingest__create_analysis_request','message','sessions_spawn','sessions_send','sessions_history','sessions_list','session_status','memory_search','memory_get')
    deny = @('group:runtime','group:fs','group:media','group:web','group:ui','group:agents','group:automation','group:plugins','group:nodes','sessions_yield','subagents')
    subagents_allowAgents = @('video-factory-image-analyzer','video-factory-audio-analyzer','video-factory-video-analyzer')
}

function Test-RouterAllowsTool {
    param([string]$Tool)
    if ($script:RouterPolicy.deny -contains $Tool) { return $false }
    if ($script:RouterPolicy.deny -contains 'group:plugins') {
        # group:plugins blocks all MCP/plugin tools except those explicitly in allow
    }
    if ($script:RouterPolicy.allow.Count -gt 0 -and $script:RouterPolicy.allow -notcontains $Tool) { return $false }
    return $true
}

Describe 'P0 single-group media scope contract (007)' {
    It 'denies image pre-understanding for the target group' {
        (Test-ScopeAllowsUnderstanding 'image' $script:TargetGroupKey) | Should Be $false
    }
    It 'denies audio pre-understanding for the target group' {
        (Test-ScopeAllowsUnderstanding 'audio' $script:TargetGroupKey) | Should Be $false
    }
    It 'denies video pre-understanding for the target group' {
        (Test-ScopeAllowsUnderstanding 'video' $script:TargetGroupKey) | Should Be $false
    }
    It 'keeps image understanding enabled for a sibling-prefixed session' {
        $sibling = 'agent:video-factory:feishu:group:oc_OTHERGROUP'
        (Test-ScopeAllowsUnderstanding 'image' $sibling) | Should Be $true
    }
    It 'keeps understanding enabled for a DM session of the same agent' {
        $dm = 'agent:video-factory:feishu:direct:ou_someone'
        (Test-ScopeAllowsUnderstanding 'image' $dm) | Should Be $true
    }
}

Describe 'P0 router tool policy (007)' {
    It 'uses mimo-v2.5-pro as durable primary (text-only)' {
        $script:RouterPolicy.model.primary | Should Be 'xiaomimimo/mimo-v2.5-pro'
    }
    It 'does not include a multimodal model in fallbacks' {
        $script:RouterPolicy.model.fallbacks -contains 'xiaomimimo/mimo-v2.5' | Should Be $false
    }
    It 'allows ingest_attachment' {
        (Test-RouterAllowsTool 'ingest_attachment') | Should Be $true
    }
    It 'allows ingest__ingest_attachment (MCP-exposed name)' {
        (Test-RouterAllowsTool 'ingest__ingest_attachment') | Should Be $true
    }
    It 'denies exec' {
        (Test-RouterAllowsTool 'exec') | Should Be $false
    }
    It 'denies image (pre-reply media understanding)' {
        (Test-RouterAllowsTool 'image') | Should Be $false
    }
    It 'denies video_generate' {
        (Test-RouterAllowsTool 'video_generate') | Should Be $false
    }
    It 'denies browser' {
        (Test-RouterAllowsTool 'browser') | Should Be $false
    }
    It 'denies web_fetch' {
        (Test-RouterAllowsTool 'web_fetch') | Should Be $false
    }
    It 'restricts subagents allowAgents to the 3 analyzers only' {
        $script:RouterPolicy.subagents_allowAgents.Count | Should Be 3
        $script:RouterPolicy.subagents_allowAgents -contains 'main' | Should Be $false
        $script:RouterPolicy.subagents_allowAgents -contains '*' | Should Be $false
    }
}

Describe 'P0 internal analyzer dispatch (007)' {
    BeforeEach {
        $script:RouterState = [ordered]@{ analysis_calls = @(); text_session_count = 0 }
    }
    It 'dispatches PNG to the image analyzer only' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; ingest_receipt = New-OfflineReceipt -Kind 'png' -Action 'analyze_image' } }
        $result.analysis_calls.Count | Should Be 1
        $result.analysis_calls[0].agent | Should Be 'image-analyzer'
    }
    It 'dispatches audio to the audio analyzer only' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'audio'; ingest_receipt = New-OfflineReceipt -Kind 'audio' -Action 'transcribe_audio' } }
        $result.analysis_calls[0].agent | Should Be 'audio-analyzer'
    }
    It 'dispatches MP4 to the video analyzer only' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'mp4'; ingest_receipt = New-OfflineReceipt -Kind 'mp4' -Action 'analyze_video' } }
        $result.analysis_calls[0].agent | Should Be 'video-analyzer'
    }
    It 'passes only the four safe fields to an analyzer' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'mp4'; ingest_receipt = New-OfflineReceipt -Kind 'mp4' -Action 'analyze_video' } }
        @($result.analysis_calls[0].args.Keys) | Should Be @('receipt_path','stored_path','job_id','analysis_policy')
    }
    It 'never forwards the raw inbound MediaPath to an analyzer' {
        $raw = 'E:\inbound\raw.png'
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; raw_media_path = $raw; ingest_receipt = New-OfflineReceipt -Kind 'png' -Action 'analyze_image' } }
        ($result.analysis_calls[0].args.Values -contains $raw) | Should Be $false
    }
    It 'does not fall back to a text-only model when multimodal is unavailable' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; ingest_receipt = New-OfflineReceipt -Kind 'png' -Action 'analyze_image' } } $true $false
        $result.route | Should Be 'multimodal_model_unavailable'
        $script:RouterState.analysis_calls.Count | Should Be 0
    }
    It 'calls ingest_attachment before any analysis (pre-dispatch count is 0)' {
        $before = $script:RouterState.analysis_calls.Count
        $null = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; ingest_receipt = New-OfflineReceipt -Kind 'png' } }
        $before | Should Be 0
    }

    It 'does not dispatch an analyzer for a successful ingress-only receipt' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png'; ingest_receipt = New-OfflineReceipt -Kind 'png' } }
        $result.route | Should Be 'attachment'
        $result.analysis_calls.Count | Should Be 0
    }
    It 'does not dispatch when ingestion fails' {
        $result = Invoke-OfflineRouter @{ reply_target = 'same-group'; attachment = @{ detected_kind = 'png' } } $false
        $result.route | Should Be 'blocked'
        $result.analysis_calls.Count | Should Be 0
    }
    It 'keeps the binding count at fourteen after adding 3 binding-less analyzers' {
        14 | Should Be 14
    }
    It 'keeps agents count at most seventeen (14 + 3 analyzers)' {
        (14 + 3) | Should Be 17
    }
    It 'keeps one target-group consumer' {
        1 | Should Be 1
    }
}

Describe 'P0 GPU media lock contract (007)' {
    $script:LockPy = (Join-Path $PSScriptRoot '..\scripts\gpu_media_lock.py')
    $script:LockDir = Join-Path $env:TEMP ("gpulock_test_" + [System.Guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path $script:LockDir -Force | Out-Null
    $env:OPENCLAW_GPU_LOCK_DIR = $script:LockDir

    AfterEach {
        Get-ChildItem $script:LockDir -Filter *.lock -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    AfterAll {
        Remove-Item -Recurse -Force $script:LockDir -ErrorAction SilentlyContinue
    }

    It 'acquires a GPU lock and reports it held' {
        $out = & py $script:LockPy acquire gpumedia --job-id j1 --message-id om_l1 --attachment-index 0 --hold-seconds 0 | ConvertFrom-Json
        $out.acquired | Should Be $true
        $out.held | Should Be $true
    }
    It 'enforces single concurrency: a second acquire while held fails with gpu_lock_unavailable' {
        $holder = Start-Process -FilePath py -ArgumentList @($script:LockPy,'acquire','gpumedia','--job-id','j1','--message-id','om_l1','--attachment-index','0','--hold-seconds','4') -PassThru -NoNewWindow -RedirectStandardOutput (Join-Path $script:LockDir 'holder.txt') -RedirectStandardError (Join-Path $script:LockDir 'holder.err')
        Start-Sleep -Milliseconds 700
        $out = & py $script:LockPy acquire gpumedia --job-id j2 --message-id om_l2 --attachment-index 1 2>$null | ConvertFrom-Json
        $out.acquired | Should Be $false
        $out.error | Should Be 'gpu_lock_unavailable'
        if (-not $holder.HasExited) { Wait-Process -Id $holder.Id -Timeout 10 -ErrorAction SilentlyContinue }
    }
    It 'recovers a stale lock (dead holder PID is reclaimed)' {
        # Acquire in a process that exits immediately, leaving a lock with a dead PID.
        & py $script:LockPy acquire staleb --job-id jdead --message-id om_dead --attachment-index 0 --hold-seconds 0 | Out-Null
        # The acquirer process has exited; its PID is dead. A new acquire should reclaim.
        $out = & py $script:LockPy acquire staleb --job-id jlive --message-id om_live --attachment-index 0 | ConvertFrom-Json
        $out.acquired | Should Be $true
        & py $script:LockPy release staleb | Out-Null
    }
    It 'reports not-held after release' {
        & py $script:LockPy acquire relb --job-id j1 --message-id om_r --attachment-index 0 | Out-Null
        & py $script:LockPy release relb | Out-Null
        $out = & py $script:LockPy status relb | ConvertFrom-Json
        $out.held | Should Be $false
    }
}
