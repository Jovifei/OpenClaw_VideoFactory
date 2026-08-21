[CmdletBinding()]
param(
    [ValidateSet('005R', '005S', '005T', '005V', '005V3')][string]$QualificationProfile = '005S',
    [ValidateSet('Preflight', 'Rehearse', 'Start', 'Supervisor', 'Worker', 'Status', 'Verify')][string]$Mode = 'Preflight',
    [switch]$Apply,
    [switch]$Finalize,
    [string]$RunManifest,
    [switch]$Rehearsal,
    [string]$LaunchTokenFile,
    # Test-only loader switch.  It exposes the deterministic freeze helpers
    # without executing a Preflight, Provider, Worker, or external run.
    [switch]$LoadOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = 'E:\project\OpenClaw_VideoFactory'
$PowerShellExecutable = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$PythonExecutable = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
$CachePath = 'C:\Users\Admin\.codex\models_cache.json'
$ModulePath = Join-Path $RepoRoot 'scripts\lib\ProviderQualification.psm1'
Import-Module $ModulePath -Force -WarningAction SilentlyContinue
$Profile = Get-PQProfile -QualificationProfile $QualificationProfile
$script:PQInvocationAuthenticated = $false
$script:PQPreflightExpectedBoundary = $null
# The bounded command sequence can include a 30-minute acceptance, four
# bounded regression suites, media validation and frame extraction.  Keep the
# lease and supervisor deadline longer than that declared worst case so a
# healthy, slow run cannot be classified as a worker death mid-command.
$script:PQWorkerLeaseMinutes = 240
$script:PQWorkerWallClockMinutes = 240

function Write-PQCliObject {
    param([Parameter(Mandatory)]$Value, [int]$ExitCode = 0)
    $Value | ConvertTo-Json -Depth 12 -Compress
    if ($ExitCode -ne 0) {
        exit $ExitCode
    }
}

function New-PQPreflightFailureEnvelope {
    param(
        [AllowNull()][string]$Gate = $null,
        [AllowNull()][string]$Substep = $null,
        [AllowNull()][string]$Reason = $null,
        [AllowNull()][Nullable[int]]$ExitCode = $null
    )
    return [ordered]@{
        status = 'error'
        error = [ordered]@{
            code = 'provider_qualification_preflight_failed'
            message = 'Provider preflight stopped.'
            context = [ordered]@{
                stage = 'preflight'
                gate = if ([string]::IsNullOrWhiteSpace($Gate)) { 'authorization' } else { $Gate }
                substep = if ([string]::IsNullOrWhiteSpace($Substep)) { 'change_request' } else { $Substep }
                reason = Get-PQStablePreflightReason -RawReason $Reason
                exit_code = if ($null -eq $ExitCode) { $null } else { [int]$ExitCode }
            }
        }
    }
}

function Write-PQCliFailure {
    param(
        [Parameter(Mandatory)][string]$Code,
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][string]$Reason,
        [AllowNull()][string]$Gate = $null,
        [AllowNull()][string]$Substep = $null,
        [AllowNull()][Nullable[int]]$FailureExitCode = $null
    )
    if ($Code -eq 'provider_qualification_preflight_failed') {
        Write-PQCliObject -Value (New-PQPreflightFailureEnvelope -Gate $Gate -Substep $Substep -Reason $Reason -ExitCode $FailureExitCode) -ExitCode 1
        return
    }
    Write-PQCliObject -Value ([ordered]@{
        status = 'error'
        error = Get-PQSanitizedError -Code $Code -Stage $Stage -Reason $Reason
    }) -ExitCode 2
}

function Get-PQProtectedBoundary {
    $paths = @(
        'PROJECT_STATUS.yaml',
        'reports/P0_ACCEPTANCE_MATRIX_V2.yaml',
        'scripts/analysis_request.py',
        'scripts/analyzer_mcp.py',
        'scripts/mcp_ingest_attachment.py',
        'scripts/media_action_ticket.py'
    )
    $hashes = [ordered]@{}
    foreach ($relative in $paths) {
        $absolute = Join-Path $RepoRoot $relative
        Test-PQNoReparseComponents -Path $absolute | Out-Null
        $hashes[$relative] = Get-PQSha256 -Path $absolute
    }
    git -C $RepoRoot diff --cached --quiet
    $indexExitCode = $LASTEXITCODE
    return [ordered]@{
        branch = (git -C $RepoRoot branch --show-current).Trim()
        head = (git -C $RepoRoot rev-parse HEAD).Trim()
        index_empty = ($indexExitCode -eq 0)
        protected_dirty_sha256 = $hashes
    }
}

function Assert-PQProtectedBoundary {
    param([Parameter(Mandatory)]$Expected)
    $current = Get-PQProtectedBoundary
    if (-not [bool]$current.index_empty -or -not [bool]$Expected.index_empty) {
        throw 'provider_qualification_git_index_changed'
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$Expected.branch) -and [string]$current.branch -ne [string]$Expected.branch) {
        throw 'provider_qualification_git_branch_changed'
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$Expected.head) -and [string]$current.head -ne [string]$Expected.head) {
        throw 'provider_qualification_git_head_changed'
    }
    foreach ($name in $Expected.protected_dirty_sha256.PSObject.Properties.Name) {
        if ([string]$current.protected_dirty_sha256.$name -ne [string]$Expected.protected_dirty_sha256.$name) {
            throw 'provider_qualification_dirty_file_changed'
        }
    }
    return $current
}

function Get-PQEnvironmentHashes {
    foreach ($path in @('C:\Users\Admin\.codex\config.toml', 'C:\Users\Admin\.codex\auth.json')) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'provider_qualification_environment_baseline_missing' }
        Test-PQNoReparseComponents -Path $path | Out-Null
    }
    $mediaTools = Assert-PQMediaTools
    return [ordered]@{
        config_sha256 = Get-PQSha256 -Path 'C:\Users\Admin\.codex\config.toml'
        auth_sha256 = Get-PQSha256 -Path 'C:\Users\Admin\.codex\auth.json'
        media_tool_sha256 = [ordered]@{
            ffmpeg = Get-PQSha256 -Path ([string]$mediaTools.ffmpeg)
            ffprobe = Get-PQSha256 -Path ([string]$mediaTools.ffprobe)
        }
    }
}

function Assert-PQEnvironmentHashes {
    param([Parameter(Mandatory)]$Expected)

    if ($null -eq $Expected -or [string]::IsNullOrWhiteSpace([string]$Expected.config_sha256) -or
        [string]::IsNullOrWhiteSpace([string]$Expected.auth_sha256)) {
        throw 'provider_qualification_environment_baseline_missing'
    }
    $current = Get-PQEnvironmentHashes
    if ([string]$current.config_sha256 -ne [string]$Expected.config_sha256) {
        throw 'provider_qualification_config_changed'
    }
    if ([string]$current.auth_sha256 -ne [string]$Expected.auth_sha256) {
        throw 'provider_qualification_auth_changed'
    }
    if ($Expected.PSObject.Properties.Name -contains 'media_tool_sha256') {
        $mediaTools = Assert-PQMediaTools
        if ([string]$current.media_tool_sha256.ffmpeg -ne [string]$Expected.media_tool_sha256.ffmpeg -or
            [string]$current.media_tool_sha256.ffprobe -ne [string]$Expected.media_tool_sha256.ffprobe) {
            throw 'provider_qualification_media_tool_changed'
        }
    }
    return $current
}

function Get-PQ005VProductionFreezeTargets {
    # The 005V provider invokes generate_video.py in Director mode.  Freeze the
    # complete local import closure and the contracts it reads, rather than just
    # the launcher and the first two Director modules.
    return @(
        'generate_video.py',
        'src/factory/__init__.py',
        'src/factory/assets/__init__.py',
        'src/factory/assets/pink_pig/__init__.py',
        'src/factory/assets/pink_pig/loader.py',
        'src/factory/assets/pink_pig/registry.json',
        'src/factory/assets/pink_pig/registry.schema.json',
        'src/factory/assets/pink_pig/style_profile.json',
        'src/factory/director/__init__.py',
        'src/factory/director/ai_director.py',
        'src/factory/director/asset_selector.py',
        'src/factory/director/context.py',
        'src/factory/director/director_contract.py',
        'src/factory/director/factual.py',
        'src/factory/director/provider.py',
        'src/factory/director/script_planner.py',
        'src/factory/director/storyboard_assembler.py',
        'video_factory/__init__.py',
        'video_factory/pipeline/__init__.py',
        'video_factory/pipeline/asset_loader.py',
        'video_factory/pipeline/audio.py',
        'video_factory/pipeline/audio_planner.py',
        'video_factory/pipeline/composition.py',
        'video_factory/pipeline/errors.py',
        'video_factory/pipeline/export.py',
        'video_factory/pipeline/failure_contract.py',
        'video_factory/pipeline/job_state.py',
        'video_factory/pipeline/mascot.py',
        'video_factory/pipeline/pink_pig_quality.py',
        'video_factory/pipeline/registry.py',
        'video_factory/pipeline/renderer.py',
        'video_factory/pipeline/render_report.py',
        'video_factory/pipeline/storyboard.py',
        'video_factory/pipeline/subtitle.py',
        'video_factory/pipeline/timeline.py',
        'video_factory/pipeline/transition.py',
        'video_factory/pipeline/validation.py',
        'video_factory/pipeline/voice_generator.py',
        'video_factory/configs/director_job.defaults.yaml',
        'video_factory/configs/video_config.yaml',
        'video_factory/configs/compositions/knowledge_illustration.json',
        'config/account.yaml',
        'config/account_columns.yaml',
        'config/topic_rules.yaml',
        'config/mascot_usage.yaml',
        'schemas/video/asset_selection_report.schema.json',
        'schemas/video/composition.schema.json',
        'schemas/video/director_draft.schema.json',
        'schemas/video/director_factual_brief.schema.json',
        'schemas/video/director_quality_report.schema.json',
        'schemas/video/director_run_report.schema.json',
        'schemas/video/director_script.schema.json',
        'schemas/video/storyboard.schema.json',
        'schemas/video/timeline.schema.json',
        'schemas/video/video_job.schema.json',
        'schemas/video/video_job_state.schema.json',
        'skills/pink-pig-mascot-director/SKILL.md',
        'assets/pink_pig/pig01.png',
        'assets/pink_pig/pig02.png',
        'assets/pink_pig/pig03.png',
        'assets/pink_pig/pig04.png',
        'assets/pink_pig/pig05.png',
        'assets/pink_pig/signature.png',
        'assets/pink_pig/demo_music.wav',
        'assets/modbus_rtu_illustrations/01-master-slave.png',
        'assets/modbus_rtu_illustrations/02-frame-layout.png',
        'assets/modbus_rtu_illustrations/03-serial-parameters.png',
        'assets/modbus_rtu_illustrations/04-troubleshooting.png',
        'assets/modbus_rtu_illustrations/05-summary.png'
    )
}

function Get-PQ005TImmutableEvidenceTargets {
    return @(
        'reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005T.md',
        'reports/CODEX_DESKTOP_QUIESCENCE_AUDIT_005T.json',
        'reports/CODEX_PROVIDER_DETACHED_RUN_005T.json',
        'reports/CODEX_PROVIDER_PRELAUNCH_AUDIT_005T.json',
        'reports/CODEX_PROVIDER_PRELAUNCH_REVIEW_005T.json',
        'reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T.json'
    )
}

function Get-PQ005V2ImmutableEvidenceTargets {
    return @(
        'reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2.json',
        'reports/AI_DIRECTOR_PHASE2_PROVIDER_PREFLIGHT_005V2.md'
    )
}

function Get-PQ005V2ImmutableEvidenceFreeze {
    $entries = @()
    foreach ($relative in Get-PQ005V2ImmutableEvidenceTargets) {
        $path = Join-Path $RepoRoot ($relative -replace '/', '\\')
        $entries += New-PQImmutableEvidenceEntry -Path $path -Reference ('repo:' + $relative)
    }
    $bridgePath = Join-Path $RepoRoot 'reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2.json'
    $bridge = Read-PQJson -Path $bridgePath
    if ([string]$bridge.id -ne 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2' -or
        [string]$bridge.execution_status -ne 'preflight_blocked' -or
        [string]$bridge.result.status -ne 'PREFLIGHT_BLOCKED' -or
        [int]$bridge.result.command_count -ne 1 -or
        [int]$bridge.result.exit_code -ne 1 -or
        [int]$bridge.result.smoke_attempts -ne 0 -or
        [int]$bridge.result.acceptance_attempts -ne 0 -or
        [int]$bridge.result.mp4_count -ne 0) {
        throw 'provider_qualification_005v2_immutable_evidence_invalid'
    }
    $canonical = [ordered]@{
        schema_version = '1.0'
        task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2'
        execution_status = 'preflight_blocked'
        result_status = 'PREFLIGHT_BLOCKED'
        command_count = 1
        exit_code = 1
        smoke_attempts = 0
        acceptance_attempts = 0
        mp4_count = 0
        entries = $entries
    } | ConvertTo-Json -Depth 8 -Compress
    $sha = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($canonical))
    return [ordered]@{
        schema_version = '1.0'
        task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2'
        execution_status = 'preflight_blocked'
        result_status = 'PREFLIGHT_BLOCKED'
        command_count = 1
        exit_code = 1
        smoke_attempts = 0
        acceptance_attempts = 0
        mp4_count = 0
        entries = $entries
        sha256 = ([System.BitConverter]::ToString($sha)).Replace('-', '').ToLowerInvariant()
    }
}

function Assert-PQ005V2ImmutableEvidenceFreezeDocument {
    param([Parameter(Mandatory)]$Evidence)
    if ([string]$Evidence.schema_version -ne '1.0' -or
        [string]$Evidence.task_id -ne 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2' -or
        [string]$Evidence.execution_status -ne 'preflight_blocked' -or
        [string]$Evidence.result_status -ne 'PREFLIGHT_BLOCKED' -or
        [int]$Evidence.command_count -ne 1 -or [int]$Evidence.exit_code -ne 1 -or
        [int]$Evidence.smoke_attempts -ne 0 -or [int]$Evidence.acceptance_attempts -ne 0 -or
        [int]$Evidence.mp4_count -ne 0 -or @($Evidence.entries).Count -ne 2 -or
        [string]$Evidence.sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'provider_qualification_005v2_immutable_evidence_binding_invalid'
    }
    $current = Get-PQ005V2ImmutableEvidenceFreeze
    if ([string]$current.sha256 -ne [string]$Evidence.sha256) {
        throw 'provider_qualification_005v2_immutable_evidence_drift'
    }
    return $true
}

function New-PQImmutableEvidenceEntry {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Reference
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'provider_qualification_005t_immutable_evidence_missing'
    }
    Test-PQNoReparseComponents -Path $Path | Out-Null
    $item = Get-Item -LiteralPath $Path -Force
    return [ordered]@{
        reference = $Reference
        bytes = [int64]$item.Length
        sha256 = Get-PQSha256 -Path $Path
    }
}

function Get-PQ005TImmutableEvidenceFreeze {
    param(
        [string]$EvidenceRepoRoot = $RepoRoot,
        [string]$EvidenceExternalRoot = 'E:\Claude_allow\Download\codex-provider-recovery-005t',
        [string]$ExpectedRunId = 'session_20260811T175916Z_43092'
    )
    $entries = @()
    foreach ($relative in Get-PQ005TImmutableEvidenceTargets) {
        $path = Join-Path $EvidenceRepoRoot ($relative -replace '/', '\\')
        $entries += New-PQImmutableEvidenceEntry -Path $path -Reference ('repo:' + $relative)
    }

    # 005T is closed. Bind only the declared immutable failed run instead of
    # enumerating a mutable external root, which prevents unrelated sessions
    # from altering 005V's historical evidence digest.
    if ([string]$ExpectedRunId -ne 'session_20260811T175916Z_43092') {
        throw 'provider_qualification_005t_immutable_evidence_invalid'
    }
    if (-not (Test-Path -LiteralPath $EvidenceExternalRoot -PathType Container)) {
        throw 'provider_qualification_005t_immutable_evidence_missing'
    }
    Test-PQNoReparseComponents -Path $EvidenceExternalRoot | Out-Null
    $runRoot = Join-Path $EvidenceExternalRoot $ExpectedRunId
    $statePath = Join-Path $runRoot 'state.json'
    $terminalPath = Join-Path $EvidenceExternalRoot ('.qualification.terminal.' + $ExpectedRunId + '.lock')
    foreach ($path in @($statePath, $terminalPath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw 'provider_qualification_005t_immutable_evidence_missing'
        }
        Test-PQNoReparseComponents -Path $path | Out-Null
    }
    $state = Read-PQJson -Path $statePath
    $terminal = Get-Item -LiteralPath $terminalPath -Force
    $ledger = Read-PQJson -Path $terminalPath
    if ([string]$state.task_id -ne 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T' -or
        [string]$state.qualification_profile -ne '005T' -or
        [string]$state.run_id -ne $ExpectedRunId -or
        [string]$ledger.task_id -ne 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T' -or
        [string]$ledger.qualification_profile -ne '005T' -or
        [string]$ledger.run_id -ne $ExpectedRunId -or
        -not ($terminal.Attributes -band [System.IO.FileAttributes]::ReadOnly)) {
        throw 'provider_qualification_005t_immutable_evidence_invalid'
    }
    $entries += New-PQImmutableEvidenceEntry -Path $statePath -Reference ('005T-run:' + $ExpectedRunId + '/state.json')
    $entries += New-PQImmutableEvidenceEntry -Path $terminalPath -Reference ('005T-terminal:' + $ExpectedRunId)
    $canonical = $entries | ConvertTo-Json -Depth 6 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($canonical)
    $sha = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return [ordered]@{
        schema_version = '1.0'
        task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
        run_id = $ExpectedRunId
        entries = $entries
        sha256 = ([System.BitConverter]::ToString($sha)).Replace('-', '').ToLowerInvariant()
    }
}

function Get-PQFixtureFreezeTargets {
    param(
        [Parameter(Mandatory)]$QualificationProfile,
        [switch]$IncludeFixture
    )
    if (-not $IncludeFixture) {
        return @()
    }

    $targets = @(
        ([string]$QualificationProfile.fixture_directory + '/topic.txt'),
        ([string]$QualificationProfile.fixture_directory + '/factual_brief.json')
    )
    if ([string]$QualificationProfile.profile -in @('005V', '005V3')) {
        # The README is a run-bound fixture contract for the isolated 005V
        # evidence namespace, not merely optional documentation.
        $targets += ([string]$QualificationProfile.fixture_directory + '/README.md')
    }
    return @($targets)
}

function Assert-PQFixtureFreezeEntries {
    param(
        [Parameter(Mandatory)]$Files,
        [Parameter(Mandatory)]$QualificationProfile,
        [Parameter(Mandatory)][string]$EvidenceRepoRoot,
        [switch]$IncludeFixture
    )

    foreach ($relative in @(Get-PQFixtureFreezeTargets -QualificationProfile $QualificationProfile -IncludeFixture:$IncludeFixture)) {
        $matches = @($Files | Where-Object { [string]$_.path -eq $relative })
        if ($matches.Count -ne 1) {
            throw 'provider_qualification_fixture_freeze_binding_invalid'
        }
        $absolute = [System.IO.Path]::GetFullPath((Join-Path $EvidenceRepoRoot ($relative -replace '/', '\\')))
        $root = [System.IO.Path]::GetFullPath($EvidenceRepoRoot).TrimEnd('\') + '\'
        if (-not $absolute.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'provider_qualification_fixture_freeze_path_invalid'
        }
        Test-PQNoReparseComponents -Path $absolute | Out-Null
        if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) {
            throw 'provider_qualification_fixture_freeze_missing'
        }
        $item = Get-Item -LiteralPath $absolute -Force
        if ([int64]$matches[0].bytes -ne [int64]$item.Length -or
            [string]$matches[0].sha256 -ne (Get-PQSha256 -Path $absolute)) {
            throw 'provider_qualification_fixture_freeze_drift'
        }
    }
    return $true
}

function Assert-PQ005TImmutableEvidenceFreezeDocument {
    param(
        [Parameter(Mandatory)]$Evidence,
        [string]$EvidenceRepoRoot = $RepoRoot,
        [string]$EvidenceExternalRoot = 'E:\Claude_allow\Download\codex-provider-recovery-005t'
    )
    if ([string]$Evidence.schema_version -ne '1.0' -or
        [string]$Evidence.task_id -ne 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T' -or
        [string]$Evidence.run_id -ne 'session_20260811T175916Z_43092' -or
        $null -eq $Evidence.entries -or @($Evidence.entries).Count -lt 6 -or
        [string]$Evidence.sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'provider_qualification_005t_immutable_evidence_binding_invalid'
    }
    $current = Get-PQ005TImmutableEvidenceFreeze -EvidenceRepoRoot $EvidenceRepoRoot -EvidenceExternalRoot $EvidenceExternalRoot -ExpectedRunId ([string]$Evidence.run_id)
    if ([string]$current.sha256 -ne [string]$Evidence.sha256) {
        throw 'provider_qualification_005t_immutable_evidence_drift'
    }
    return $true
}

function Get-PQSourceFreezeTargetList {
    param([switch]$IncludeFixture)
    $targets = @(
        'scripts/provider_qualification.ps1',
        'scripts/lib/ProviderQualification.psm1',
        'scripts/provider_qualification_005r.ps1',
        'scripts/lib/ProviderQualification005R.psm1',
        'schemas/ops/provider_qualification_run.schema.json',
        'tests/Test-ProviderQualification005R.ps1',
        'tests/Test-ProviderQualification005S.ps1',
        'generate_video.py',
        'src/factory/director/provider.py',
        'src/factory/director/ai_director.py',
        'schemas/video/director_draft.schema.json'
    )
    if ([string]$Profile.profile -eq '005T') {
        $targets += 'tests/Test-ProviderQualification005T.ps1'
    }
    if ([string]$Profile.profile -in @('005V', '005V3')) {
        $targets += @(
            'schemas/ops/provider_qualification_final_review.schema.json',
            'tests/Test-ProviderQualification005V.ps1',
            'tests/Test-ProviderQualification005U.ps1',
            'tests/Test-ProviderQualification005U1.ps1'
        )
        if ([string]$Profile.profile -eq '005V3') {
            $targets += @(
                'schemas/ops/provider_qualification_preflight_error.schema.json',
                'tests/Test-ProviderQualification005V3.ps1'
            )
        }
        $targets += Get-PQ005VProductionFreezeTargets
    }
    $targets += Get-PQFixtureFreezeTargets -QualificationProfile $Profile -IncludeFixture:$IncludeFixture
    return @($targets | Select-Object -Unique)
}

function Get-PQSourceFreeze {
    param([switch]$IncludeFixture)
    $targets = Get-PQSourceFreezeTargetList -IncludeFixture:$IncludeFixture
    $files = @()
    foreach ($relative in @($targets)) {
        $absolute = Join-Path $RepoRoot $relative
        if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) {
            throw 'provider_qualification_source_freeze_missing'
        }
        Test-PQNoReparseComponents -Path $absolute | Out-Null
        $item = Get-Item -LiteralPath $absolute
        $files += [ordered]@{ path = $relative; bytes = [int64]$item.Length; sha256 = Get-PQSha256 -Path $absolute }
    }
    $immutableEvidence = if ([string]$Profile.profile -in @('005V', '005V3')) { Get-PQ005TImmutableEvidenceFreeze } else { $null }
    $immutable005V2Evidence = if ([string]$Profile.profile -eq '005V3') { Get-PQ005V2ImmutableEvidenceFreeze } else { $null }
    $canonical = if ($null -ne $immutableEvidence -or $null -ne $immutable005V2Evidence) {
        [ordered]@{
            files = $files
            immutable_005t_evidence = $immutableEvidence
            immutable_005v2_evidence = $immutable005V2Evidence
        } | ConvertTo-Json -Depth 8 -Compress
    } else {
        $files | ConvertTo-Json -Depth 6 -Compress
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($canonical)
    $sha = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    $digest = ([System.BitConverter]::ToString($sha)).Replace('-', '').ToLowerInvariant()
    return [ordered]@{
        files = $files
        immutable_005t_evidence = $immutableEvidence
        immutable_005v2_evidence = $immutable005V2Evidence
        sha256 = $digest
    }
}

function Assert-PQSourceFreeze {
    param([Parameter(Mandatory)][string]$ExpectedSha256, [switch]$IncludeFixture)
    $current = Get-PQSourceFreeze -IncludeFixture:$IncludeFixture
    if ([string]$current.sha256 -ne $ExpectedSha256) {
        throw 'provider_qualification_source_freeze_drift'
    }
    return $current
}

function Assert-PQSourceFreezeDocument {
    param(
        [Parameter(Mandatory)]$Freeze,
        [switch]$IncludeFixture
    )

    if ($null -eq $Freeze.files -or @($Freeze.files).Count -eq 0 -or
        [string]$Freeze.sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'provider_qualification_source_freeze_binding_invalid'
    }
    Assert-PQFixtureFreezeEntries -Files @($Freeze.files) -QualificationProfile $Profile -EvidenceRepoRoot $RepoRoot -IncludeFixture:$IncludeFixture | Out-Null
    $items = @()
    $repoFull = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\') + '\'
    foreach ($entry in @($Freeze.files)) {
        $relative = [string]$entry.path
        if ([string]::IsNullOrWhiteSpace($relative) -or [System.IO.Path]::IsPathRooted($relative) -or
            $relative -match '(^|[\\/])\.\.([\\/]|$)') {
            throw 'provider_qualification_source_freeze_path_invalid'
        }
        $absolute = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot ($relative -replace '/', '\')))
        if (-not $absolute.StartsWith($repoFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'provider_qualification_source_freeze_path_invalid'
        }
        Test-PQNoReparseComponents -Path $absolute | Out-Null
        if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) {
            throw 'provider_qualification_source_freeze_missing'
        }
        $item = Get-Item -LiteralPath $absolute
        $sha = Get-PQSha256 -Path $absolute
        if ([int64]$entry.bytes -ne [int64]$item.Length -or [string]$entry.sha256 -ne $sha) {
            throw 'provider_qualification_source_freeze_drift'
        }
        $items += [ordered]@{ path = $relative; bytes = [int64]$item.Length; sha256 = $sha }
    }
    $immutableEvidence = $null
    if ([string]$Profile.profile -in @('005V', '005V3')) {
        $hasImmutableEvidence = if ($Freeze -is [System.Collections.IDictionary]) {
            $Freeze.Contains('immutable_005t_evidence')
        } else {
            $Freeze.PSObject.Properties.Name -contains 'immutable_005t_evidence'
        }
        if (-not $hasImmutableEvidence) {
            throw 'provider_qualification_005t_immutable_evidence_binding_invalid'
        }
        $immutableEvidence = $Freeze.immutable_005t_evidence
        Assert-PQ005TImmutableEvidenceFreezeDocument -Evidence $immutableEvidence | Out-Null
    }
    $immutable005V2Evidence = $null
    if ([string]$Profile.profile -eq '005V3') {
        $has005V2Evidence = if ($Freeze -is [System.Collections.IDictionary]) {
            $Freeze.Contains('immutable_005v2_evidence')
        } else {
            $Freeze.PSObject.Properties.Name -contains 'immutable_005v2_evidence'
        }
        if (-not $has005V2Evidence) {
            throw 'provider_qualification_005v2_immutable_evidence_binding_invalid'
        }
        $immutable005V2Evidence = $Freeze.immutable_005v2_evidence
        Assert-PQ005V2ImmutableEvidenceFreezeDocument -Evidence $immutable005V2Evidence | Out-Null
    }
    $canonical = if ($null -ne $immutableEvidence -or $null -ne $immutable005V2Evidence) {
        [ordered]@{
            files = $items
            immutable_005t_evidence = $immutableEvidence
            immutable_005v2_evidence = $immutable005V2Evidence
        } | ConvertTo-Json -Depth 8 -Compress
    } else {
        $items | ConvertTo-Json -Depth 6 -Compress
    }
    $digestBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($canonical))
    $digest = ([System.BitConverter]::ToString($digestBytes)).Replace('-', '').ToLowerInvariant()
    if ($digest -ne [string]$Freeze.sha256) {
        throw 'provider_qualification_source_freeze_binding_invalid'
    }
    $current = Get-PQSourceFreeze -IncludeFixture:$IncludeFixture
    if ([string]$current.sha256 -ne [string]$Freeze.sha256) {
        throw 'provider_qualification_source_freeze_drift'
    }
    return $true
}

function Assert-PQLauncherPath {
    param([Parameter(Mandatory)]$Freeze)

    $expected = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot 'scripts\provider_qualification.ps1'))
    $actual = [System.IO.Path]::GetFullPath($PSCommandPath)
    if (-not $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_launcher_path_invalid'
    }
    Test-PQNoReparseComponents -Path $actual | Out-Null
    $entry = @($Freeze.files | Where-Object { ([string]$_.path -replace '\\', '/') -eq 'scripts/provider_qualification.ps1' }) | Select-Object -First 1
    if ($null -eq $entry -or [string]$entry.sha256 -ne (Get-PQSha256 -Path $actual)) {
        throw 'provider_qualification_launcher_source_changed'
    }
    return $true
}

function Assert-PQPrelaunchApproval {
    param([Parameter(Mandatory)]$Freeze)

    $changeRequestPath = Join-Path $RepoRoot ('reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-' + [string]$Profile.profile + '.json')
    if (-not (Test-Path -LiteralPath $changeRequestPath -PathType Leaf)) { throw 'PRELAUNCH_REVIEW_FAILED' }
    Test-PQNoReparseComponents -Path $changeRequestPath | Out-Null
    $changeRequest = Read-PQJson -Path $changeRequestPath
    if ([string]$changeRequest.id -ne [string]$Profile.task_id -or
        [int]$changeRequest.maximum_smoke_commands -ne 1 -or [int]$changeRequest.maximum_acceptance_commands -ne 1 -or
        [bool]$changeRequest.does_not_authorize_oauth_profile_model_changes -ne $true -or
        [string]$changeRequest.execution_status -notin @('contract_review_approved_pending_preflight', 'ready_for_worker')) {
        throw 'PRELAUNCH_REVIEW_FAILED'
    }
    $auditPath = Join-Path $RepoRoot ([string]$Profile.prelaunch_audit_path)
    if (-not (Test-Path -LiteralPath $auditPath -PathType Leaf)) {
        throw 'PRELAUNCH_REVIEW_FAILED'
    }
    $audit = Read-PQJson -Path $auditPath
    if ([string]$audit.task_id -ne [string]$Profile.task_id -or
        [string]$audit.source_freeze_sha256 -ne [string]$Freeze.sha256 -or
        [string]$audit.verdict -ne 'APPROVED' -or
        [string]$audit.reviewer_result_sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'PRELAUNCH_REVIEW_FAILED'
    }
    return [ordered]@{
        audit_sha256 = Get-PQSha256 -Path $auditPath
        reviewer_result_sha256 = [string]$audit.reviewer_result_sha256
    }
}

function Get-PQOperationalChangeRequest {
    param([Parameter(Mandatory)][string]$Mode)
    if ([string]$Profile.profile -notin @('005V', '005V3')) {
        return $null
    }
    $path = if ([string]$Profile.profile -eq '005V3') {
        Join-Path $RepoRoot 'reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-DIAGNOSTICS-005V3.json'
    } elseif ($Mode -eq 'Preflight') {
        Join-Path $RepoRoot 'reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2.json'
    } else {
        Join-Path $RepoRoot 'reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005V.json'
    }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw 'provider_qualification_change_request_missing'
    }
    Test-PQNoReparseComponents -Path $path | Out-Null
    return Read-PQJson -Path $path
}

function Invoke-PQPreflightGate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Gate,
        [Parameter(Mandatory)][string]$Substep,
        [Parameter(Mandatory)][scriptblock]$Action
    )
    try {
        return (& $Action)
    } catch {
        $existing = Get-PQPreflightFailureContext -Exception $_.Exception
        if ($null -ne $existing) {
            throw $_.Exception
        }
        $reason = Get-PQStablePreflightReason -RawReason ([string]$_.Exception.Message)
        throw (New-PQPreflightFailure -Gate $Gate -Substep $Substep -Reason $reason)
    }
}

function Assert-PQActiveLockBinding {
    param(
        [Parameter(Mandatory)]$Context,
        [switch]$Canary
    )

    $lock = Read-PQActiveLock -ExternalRoot ([string]$Profile.external_root)
    if ($null -eq $lock -or [string]$lock.task_id -ne [string]$Profile.task_id -or
        [string]$lock.qualification_profile -ne [string]$Profile.profile -or
        [string]$lock.run_id -ne [string]$Context.manifest.run_id) {
        throw 'provider_qualification_active_lock_binding_mismatch'
    }
    $manifestPath = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'run_manifest.json'
    $freezePath = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'source_freeze.json'
    if ([bool]$lock.canary -ne [bool]$Canary -or
        [string]$lock.manifest_sha256 -ne (Get-PQSha256 -Path $manifestPath) -or
        [string]$lock.source_freeze_sha256 -ne [string]$Context.manifest.source_freeze_sha256) {
        throw 'provider_qualification_active_lock_binding_mismatch'
    }
    $freeze = Read-PQJson -Path $freezePath
    Assert-PQSourceFreezeDocument -Freeze $freeze -IncludeFixture:(-not ([string]$Context.manifest.kind -eq 'rehearsal')) | Out-Null
    if (-not $Canary) {
        $auditPath = Join-Path $RepoRoot ([string]$Profile.prelaunch_audit_path)
        if ([string]$lock.prelaunch_audit_sha256 -ne (Get-PQSha256 -Path $auditPath)) {
            throw 'provider_qualification_active_lock_binding_mismatch'
        }
        if ([string]$lock.prelaunch_reviewer_result_sha256 -ne [string]$Context.manifest.prelaunch_reviewer_result_sha256) {
            throw 'provider_qualification_active_lock_binding_mismatch'
        }
    }
    return $lock
}

function Assert-PQCodexContract {
    param([scriptblock]$SupervisorLivenessProbe = $null)

    $command = Get-Command codex -ErrorAction Stop | Select-Object -First 1
    $commandPath = [string]$command.Source
    if ([string]::IsNullOrWhiteSpace($commandPath)) {
        $commandPath = [string]$command.Path
    }
    if ([string]::IsNullOrWhiteSpace($commandPath)) {
        $commandPath = [string]$command.Definition
    }
    $trustedCliPaths = @(
        'C:\Users\Admin\AppData\Roaming\npm\codex.ps1',
        'C:\Users\Admin\AppData\Roaming\npm\codex.cmd'
    )
    $commandPath = [System.IO.Path]::GetFullPath($commandPath)
    if (@($trustedCliPaths | Where-Object { $_.Equals($commandPath, [System.StringComparison]::OrdinalIgnoreCase) }).Count -ne 1) {
        throw 'provider_qualification_cli_not_npm'
    }
    $versionOut = [System.IO.Path]::GetTempFileName()
    $versionErr = [System.IO.Path]::GetTempFileName()
    $helpOut = [System.IO.Path]::GetTempFileName()
    $helpErr = [System.IO.Path]::GetTempFileName()
    try {
        $versionExit = Invoke-PQBoundedProcess -FilePath $PowerShellExecutable -Arguments @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $commandPath, '--version') -WorkingDirectory $RepoRoot -StdOutPath $versionOut -StdErrPath $versionErr -TimeoutSeconds 30 -SupervisorLivenessProbe $SupervisorLivenessProbe
        $version = (Get-Content -LiteralPath $versionOut -Raw -Encoding UTF8).Trim()
        if ($versionExit -ne 0 -or $version -notmatch '0\.146\.0') {
            throw 'provider_qualification_cli_version_unsupported'
        }
        $helpExit = Invoke-PQBoundedProcess -FilePath $PowerShellExecutable -Arguments @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $commandPath, 'exec', '--help') -WorkingDirectory $RepoRoot -StdOutPath $helpOut -StdErrPath $helpErr -TimeoutSeconds 30 -SupervisorLivenessProbe $SupervisorLivenessProbe
        $help = Get-Content -LiteralPath $helpOut -Raw -Encoding UTF8
        if ($helpExit -ne 0) {
            throw 'provider_qualification_cli_help_unavailable'
        }
    } finally {
        foreach ($temp in @($versionOut, $versionErr, $helpOut, $helpErr)) {
            if (Test-Path -LiteralPath $temp -PathType Leaf) { Remove-Item -LiteralPath $temp -Force }
        }
    }
    foreach ($flag in @('--ephemeral', '--sandbox', '--skip-git-repo-check', '--ignore-user-config', '--color', '--output-schema', '--output-last-message', '-C')) {
        if ($help -notmatch [regex]::Escape($flag)) {
            throw 'provider_qualification_cli_flag_missing'
        }
    }
    return [ordered]@{ provider = 'npm_codex_cli'; version = '0.146.0'; command_path = $commandPath; command_sha256 = Get-PQSha256 -Path $commandPath; required_flags_valid = $true }
}

function Get-PQPreflight {
    $externalRoot = Invoke-PQPreflightGate -Gate 'external_root' -Substep 'external_root_path' -Action {
        Assert-PQExternalRoot -Profile $Profile -ExternalRoot ([string]$Profile.external_root)
    }
    $activeLock = Invoke-PQPreflightGate -Gate 'active_lock' -Substep 'active_lock_probe' -Action {
        $lockPath = Join-Path $externalRoot '.qualification.active.lock'
        if (Test-Path -LiteralPath $lockPath -PathType Leaf) { throw 'provider_qualification_active_run_exists' }
        return $lockPath
    }
    $fixture = Invoke-PQPreflightGate -Gate 'fresh_job' -Substep 'job_path' -Action {
        $candidate = Get-PQQualificationFixture
        if (Test-Path -LiteralPath $candidate.work_dir) { throw 'BLOCKED_FRESH_JOB_REQUIRED' }
        return $candidate
    }
    $null = Invoke-PQPreflightGate -Gate 'fresh_evidence' -Substep 'external_root_entries' -Action {
        if (Test-Path -LiteralPath $externalRoot -PathType Container) {
            $entries = @(Get-ChildItem -LiteralPath $externalRoot -Force -ErrorAction Stop)
            if ($entries.Count -ne 0) { throw 'BLOCKED_FRESH_EVIDENCE_REQUIRED' }
        }
        return $true
    }
    $boundary = Invoke-PQPreflightGate -Gate 'git_boundary' -Substep 'git_index' -Action {
        Get-PQProtectedBoundary
    }
    if (-not [bool]$boundary.index_empty) {
        throw (New-PQPreflightFailure -Gate 'git_boundary' -Substep 'git_index' -Reason 'git_index_changed')
    }
    if ($null -ne $script:PQPreflightExpectedBoundary) {
        if ([string]$boundary.branch -ne [string]$script:PQPreflightExpectedBoundary.branch) {
            throw (New-PQPreflightFailure -Gate 'git_boundary' -Substep 'git_branch' -Reason 'git_branch_changed')
        }
        if ([string]$boundary.head -ne [string]$script:PQPreflightExpectedBoundary.head) {
            throw (New-PQPreflightFailure -Gate 'git_boundary' -Substep 'git_head' -Reason 'git_head_changed')
        }
        foreach ($name in @($script:PQPreflightExpectedBoundary.protected_dirty_sha256.PSObject.Properties.Name)) {
            if ([string]$boundary.protected_dirty_sha256.$name -ne [string]$script:PQPreflightExpectedBoundary.protected_dirty_sha256.$name) {
                throw (New-PQPreflightFailure -Gate 'git_boundary' -Substep 'dirty_files' -Reason 'dirty_file_changed')
            }
        }
    }
    $cli = Invoke-PQPreflightGate -Gate 'codex_cli' -Substep 'path_resolution' -Action {
        Assert-PQCodexContract
    }
    $mediaTools = Invoke-PQPreflightGate -Gate 'media_tools' -Substep 'tool_path' -Action {
        Assert-PQMediaTools
    }
    $immutable005TEvidence = if ([string]$Profile.profile -in @('005V', '005V3')) {
        Invoke-PQPreflightGate -Gate 'immutable_005t' -Substep 'evidence_hash' -Action { Get-PQ005TImmutableEvidenceFreeze }
    } else { $null }
    $cache = Invoke-PQPreflightGate -Gate 'cache_snapshot' -Substep 'json_parse' -Action {
        $snapshot = Get-PQCacheSnapshot -Path $CachePath
        $health = Get-PQCacheHealth -Snapshot $snapshot
        if ([string]$health.status -ne 'healthy') { throw 'provider_qualification_cache_unhealthy' }
        return $snapshot
    }
    $environment = Invoke-PQPreflightGate -Gate 'environment_hashes' -Substep 'baseline_hash' -Action {
        foreach ($path in @('C:\Users\Admin\.codex\config.toml', 'C:\Users\Admin\.codex\auth.json')) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'provider_qualification_environment_baseline_missing' }
            Test-PQNoReparseComponents -Path $path | Out-Null
        }
        return [ordered]@{
            config_sha256 = Get-PQSha256 -Path 'C:\Users\Admin\.codex\config.toml'
            auth_sha256 = Get-PQSha256 -Path 'C:\Users\Admin\.codex\auth.json'
        }
    }
    $desktop = Invoke-PQPreflightGate -Gate 'desktop_snapshot' -Substep 'process_probe' -Action {
        @(Get-PQDesktopProcessSnapshot).Count
    }
    return [ordered]@{
        task_id = [string]$Profile.task_id
        qualification_profile = [string]$Profile.profile
        branch = $boundary.branch
        head = $boundary.head
        index_empty = $boundary.index_empty
        protected_dirty_sha256 = $boundary.protected_dirty_sha256
        provider = $cli.provider
         provider_version = $cli.version
         provider_command_sha256 = $cli.command_sha256
         media_tool_sha256 = [ordered]@{
             ffmpeg = Get-PQSha256 -Path ([string]$mediaTools.ffmpeg)
             ffprobe = Get-PQSha256 -Path ([string]$mediaTools.ffprobe)
         }
        required_flags_valid = $cli.required_flags_valid
        immutable_005t_evidence_sha256 = if ($null -ne $immutable005TEvidence) { [string]$immutable005TEvidence.sha256 } else { $null }
        cache = $cache
        config_sha256 = $environment.config_sha256
        auth_sha256 = $environment.auth_sha256
        desktop_process_count = [int]$desktop
    }
}

function Assert-PQMediaTools {
    # Do not trust an arbitrary PATH entry for media evidence.  These are the
    # machine-approved WinGet binaries used by the existing factory.  Their
    # exact paths are never emitted into a report; only the command results
    # and output hashes are retained.
    $tools = [ordered]@{
        ffmpeg = 'C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
        ffprobe = 'C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffprobe.exe'
    }
    $expectedHashes = @{
        ffmpeg = '09948d4cdd0650da6ff5a87577469f2a218dc2615ae379f8f734d24c49de0f73'
        ffprobe = 'a6618e99bb58869ded3c6f37b53aa1a8d701c3591dbb7b5b317d47369c112be2'
    }
    foreach ($name in @('ffmpeg', 'ffprobe')) {
        $path = [string]$tools[$name]
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw 'provider_qualification_media_tool_unavailable'
        }
        Test-PQNoReparseComponents -Path $path | Out-Null
        if ((Get-PQSha256 -Path $path) -ne $expectedHashes[$name]) {
            throw 'provider_qualification_media_tool_changed'
        }
        $tools[$name] = $path
    }
    return [pscustomobject]$tools
}

function ConvertTo-PQProcessArgument {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)
    if ($Value -notmatch '[\s"]') { return $Value }
    # Windows CommandLineToArgvW quoting: double trailing backslashes before
    # the closing quote and escape embedded quotes.
    $quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $quoted = [regex]::Replace($quoted, '(\\+)$', '$1$1')
    return '"' + $quoted + '"'
}

if ($null -eq ('PQJobTree.Native' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace PQJobTree {
    public static class Native {
        [StructLayout(LayoutKind.Sequential)]
        struct IoCounters { public UInt64 ReadOps; public UInt64 WriteOps; public UInt64 OtherOps; public UInt64 ReadBytes; public UInt64 WriteBytes; public UInt64 OtherBytes; }
        [StructLayout(LayoutKind.Sequential)]
        struct BasicLimits { public Int64 PerProcessUserTimeLimit; public Int64 PerJobUserTimeLimit; public UInt32 LimitFlags; public UIntPtr MinimumWorkingSetSize; public UIntPtr MaximumWorkingSetSize; public UInt32 ActiveProcessLimit; public UIntPtr Affinity; public UInt32 PriorityClass; public UInt32 SchedulingClass; }
        [StructLayout(LayoutKind.Sequential)]
        struct ExtendedLimits { public BasicLimits Basic; public IoCounters Io; public UIntPtr ProcessMemoryLimit; public UIntPtr JobMemoryLimit; public UIntPtr PeakProcessMemoryUsed; public UIntPtr PeakJobMemoryUsed; }
        const Int32 ExtendedInformation = 9;
        const UInt32 KillOnClose = 0x2000;
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr attributes, string name);
        [DllImport("kernel32.dll", SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job, Int32 infoClass, IntPtr info, UInt32 length);
        [DllImport("kernel32.dll", SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateJobObject(IntPtr job, UInt32 code);
        [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
        public static IntPtr CreateKillOnCloseJob() {
            IntPtr job = CreateJobObject(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new InvalidOperationException("job_create_failed");
            ExtendedLimits limits = new ExtendedLimits();
            limits.Basic.LimitFlags = KillOnClose;
            IntPtr buffer = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(ExtendedLimits)));
            try {
                Marshal.StructureToPtr(limits, buffer, false);
                if (!SetInformationJobObject(job, ExtendedInformation, buffer, (UInt32)Marshal.SizeOf(typeof(ExtendedLimits)))) {
                    CloseHandle(job); throw new InvalidOperationException("job_configure_failed");
                }
            } finally { Marshal.FreeHGlobal(buffer); }
            return job;
        }
        public static void Assign(IntPtr job, IntPtr process) {
            if (!AssignProcessToJobObject(job, process)) throw new InvalidOperationException("job_assign_failed");
        }
        public static void EndTree(IntPtr job, UInt32 code) { if (job != IntPtr.Zero) TerminateJobObject(job, code); }
        public static void Close(IntPtr job) { if (job != IntPtr.Zero) CloseHandle(job); }
    }
}
'@ -Language CSharp
}

function Invoke-PQBoundedProcess {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$StdOutPath,
        [Parameter(Mandatory)][string]$StdErrPath,
        [string]$InputText = $null,
        [Parameter(Mandatory)][ValidateRange(1, 3600)][int]$TimeoutSeconds,
        [scriptblock]$SupervisorLivenessProbe = $null,
        [ValidateRange(50, 5000)][int]$LivenessPollMilliseconds = 250
    )

    return ProviderQualification\Invoke-PQBoundedProcess @PSBoundParameters
}

function New-PQRunManifest {
    param(
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)]$Boundary,
        [Parameter(Mandatory)]$Freeze,
        [Parameter(Mandatory)][string]$SupervisorTokenHash,
        $Environment = $null,
        [string]$PrelaunchReviewerResultSha256 = $null
    )
    return [ordered]@{
        schema_version = '1.1'
        task_id = [string]$Profile.task_id
        qualification_profile = [string]$Profile.profile
        run_id = $RunId
        run_root = $RunRoot
        boundary = $Boundary
        source_freeze_sha256 = [string]$Freeze.sha256
        immutable_005t_evidence_sha256 = if ([string]$Profile.profile -eq '005V') { [string]$Freeze.immutable_005t_evidence.sha256 } else { $null }
        supervisor_token_sha256 = $SupervisorTokenHash
        prelaunch_reviewer_result_sha256 = $PrelaunchReviewerResultSha256
        environment = $Environment
        created_utc = [DateTime]::UtcNow.ToString('o')
    }
}

function Read-PQRunContext {
    param([Parameter(Mandatory)][string]$ManifestPath)
    $safeManifest = Assert-PQManifestPath -Profile $Profile -ManifestPath $ManifestPath
    $manifest = Read-PQJson -Path $safeManifest.manifest_path
    $runRoot = Assert-PQManifestIdentity -Manifest $manifest -Profile $Profile -ManifestPath $safeManifest.manifest_path
    $statePath = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'state.json'
    $state = Read-PQJson -Path $statePath
    Assert-PQStateSchema -State $state
    Assert-PQStateIdentity -State $state -Profile $Profile -RunId ([string]$manifest.run_id)
    if ([string]$Profile.schema_version -eq '1.1') {
        $freezePath = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'source_freeze.json'
        $freeze = Read-PQJson -Path $freezePath
        if ([string]$freeze.sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$freeze.sha256 -ne [string]$manifest.source_freeze_sha256) {
            throw 'provider_qualification_source_freeze_binding_invalid'
        }
        if ($manifest.PSObject.Properties.Name -contains 'kind' -and
            [string]$manifest.kind -notin @('production', 'rehearsal')) {
            throw 'provider_qualification_manifest_kind_invalid'
        }
        Assert-PQSourceFreezeDocument -Freeze $freeze -IncludeFixture:(-not ([string]$manifest.kind -eq 'rehearsal')) | Out-Null
        if ([string]$Profile.profile -eq '005V' -and
            ((-not ($manifest.PSObject.Properties.Name -contains 'immutable_005t_evidence_sha256')) -or
             [string]$manifest.immutable_005t_evidence_sha256 -ne [string]$freeze.immutable_005t_evidence.sha256)) {
            throw 'provider_qualification_005t_immutable_evidence_binding_invalid'
        }
        if ($manifest.PSObject.Properties.Name -contains 'prelaunch_reviewer_result_sha256' -and
            [string]$manifest.prelaunch_reviewer_result_sha256 -notmatch '^[0-9a-f]{64}$') {
            throw 'provider_qualification_prelaunch_review_binding_invalid'
        }
        if ([string]$manifest.kind -ne 'rehearsal' -and
            (-not ($state.PSObject.Properties.Name -contains 'prelaunch_review_result_sha256') -or
             [string]$state.prelaunch_review_result_sha256 -ne [string]$manifest.prelaunch_reviewer_result_sha256)) {
            throw 'provider_qualification_prelaunch_review_binding_invalid'
        }
    }
    return [pscustomobject]@{ manifest = $manifest; run_root = $runRoot; state_path = $statePath; state = $state }
}

function Write-PQRunMarker {
    param([Parameter(Mandatory)][string]$RunRoot, [Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Content)
    $path = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath $Name
    Write-PQTextAtomic -Path $path -Content $Content
    return $path
}

function Start-PQProcess {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory
    )
    return Start-Process -FilePath $PowerShellExecutable -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru
}

function Test-PQProcessAlive {
    param([Parameter(Mandatory)][int]$ProcessId)
    return ($null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue))
}

function Write-PQWorkerHeartbeat {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$HeartbeatPath,
        [Parameter(Mandatory)][string]$LeaseId,
        [Parameter(Mandatory)][string]$Stage
    )

    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $current = $context.state
    if ([int]$current.worker_pid -ne $PID -or [string]$current.lease_id -ne $LeaseId) {
        throw 'provider_qualification_worker_heartbeat_owner_mismatch'
    }
    $next = Update-PQRunState -State $current -StatePath $context.state_path -Patch @{
        heartbeat_sequence = [int]$current.heartbeat_sequence + 1
        lease_expires_utc = [DateTime]::UtcNow.AddMinutes($script:PQWorkerLeaseMinutes).ToString('o')
    } -Stage $Stage
    Write-PQHeartbeat -Path $HeartbeatPath -State $next -ProcessId $PID -LeaseId $LeaseId | Out-Null
    return $next
}

function Read-PQLaunchTokenFile {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$TokenFile,
        [Parameter(Mandatory)][ValidateSet('supervisor.token', 'worker.token')][string]$ExpectedLeaf
    )
    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $expected = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath $ExpectedLeaf
    $actual = [System.IO.Path]::GetFullPath($TokenFile)
    if (-not $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $actual -PathType Leaf)) {
        throw 'provider_qualification_launch_token_file_invalid'
    }
    Test-PQNoReparseComponents -Path $actual | Out-Null
    $token = (Get-Content -LiteralPath $actual -Raw -Encoding UTF8).Trim()
    if ($token -notmatch '^[0-9a-f]{64}$') {
        throw 'provider_qualification_launch_token_invalid'
    }
    Remove-Item -LiteralPath $actual -Force
    if (Test-Path -LiteralPath $actual) {
        throw 'provider_qualification_launch_token_cleanup_failed'
    }
    return $token
}

function New-PQRehearsalLedger {
    param([Parameter(Mandatory)]$Profile)

    $root = Assert-PQExternalRoot -Profile $Profile -ExternalRoot ([string]$Profile.external_root)
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        New-Item -ItemType Directory -Path $root -Force | Out-Null
    }
    $ledger = Join-Path $root ('.rehearsal.' + ([string]$Profile.profile).ToLowerInvariant() + '.consumed.lock')
    $payload = ([ordered]@{ task_id = [string]$Profile.task_id; created_utc = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Compress)
    try {
        $stream = [System.IO.File]::Open($ledger, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    } catch {
        throw 'provider_qualification_rehearsal_already_consumed'
    }
    try {
        $writer = New-Object System.IO.StreamWriter($stream, (New-Object System.Text.UTF8Encoding($false)))
        try {
            $writer.Write($payload)
            $writer.Flush()
            $stream.Flush($true)
        } finally {
            $writer.Dispose()
        }
    } finally {
        $stream.Dispose()
    }
    return $ledger
}

function Assert-PQLeaseCurrent {
    param([Parameter(Mandatory)]$State)
    if (Test-PQLeaseExpired -State $State) {
        throw 'BLOCKED_WORKER_LEASE_EXPIRED'
    }
}

function Assert-PQWorkerSupervisorLiveness {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$LeaseId
    )

    # A long child process must remain bound to this exact Worker, lease, run,
    # and Supervisor.  The active-lock check binds the run; the PID comparison
    # prevents a stale lock from making a replacement Supervisor appear live.
    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $state = $context.state
    if ([int]$state.worker_pid -ne $PID -or [string]$state.lease_id -ne $LeaseId) {
        throw 'provider_qualification_worker_heartbeat_owner_mismatch'
    }
    Assert-PQLeaseCurrent -State $state
    $lock = Assert-PQActiveLockBinding -Context $context -Canary:$false
    if ([int]$state.supervisor_pid -le 0 -or
        [int]$lock.supervisor_pid -ne [int]$state.supervisor_pid -or
        -not (Test-PQProcessAlive -ProcessId ([int]$state.supervisor_pid))) {
        throw 'BLOCKED_SUPERVISOR_DIED'
    }
    return $true
}

function New-PQWorkerSupervisorLivenessProbe {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$LeaseId
    )

    $capturedManifestPath = $ManifestPath
    $capturedLeaseId = $LeaseId
    return {
        Assert-PQWorkerSupervisorLiveness -ManifestPath $capturedManifestPath -LeaseId $capturedLeaseId
    }.GetNewClosure()
}

function Test-PQLeaseExpired {
    param([Parameter(Mandatory)]$State)

    if ([string]::IsNullOrWhiteSpace([string]$State.lease_expires_utc)) {
        throw 'provider_qualification_lease_invalid'
    }
    try {
        $raw = [string]$State.lease_expires_utc
        if ($raw -notmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?Z$') {
            throw 'provider_qualification_lease_invalid'
        }
        return ([DateTime]::Parse($raw).ToUniversalTime() -le [DateTime]::UtcNow)
    } catch {
        throw 'provider_qualification_lease_invalid'
    }
}

function Wait-PQLeaseExpiry {
    param([Parameter(Mandatory)]$State)

    while (-not (Test-PQLeaseExpired -State $State)) {
        Start-Sleep -Seconds 1
        $remaining = ([DateTime]::Parse([string]$State.lease_expires_utc).ToUniversalTime() - [DateTime]::UtcNow).TotalSeconds
        if ($remaining -gt 35) {
            throw 'provider_qualification_lease_duration_invalid'
        }
    }
}

function Start-PQSupervisor {
    if (-not $Apply) {
        throw 'provider_qualification_start_requires_apply'
    }
    if ([bool]$Profile.start_closed) {
        throw 'provider_qualification_run_closed'
    }
    # Start is not an alternate path around the preflight/fresh-evidence gate.
    # This call must happen before creating the active lock or any child process.
    $null = Get-PQPreflight
    $externalRoot = [string]$Profile.external_root
    Test-PQNoReparseComponents -Path $externalRoot | Out-Null
    if (-not (Test-Path -LiteralPath $externalRoot -PathType Container)) {
        New-Item -ItemType Directory -Path $externalRoot -Force | Out-Null
    }
    $runId = 'session_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '_' + $PID
    $runRoot = Assert-PQRunRoot -Profile $Profile -RunRoot (Join-Path $externalRoot $runId) -RunId $runId
    if (Test-Path -LiteralPath $runRoot) {
        throw 'provider_qualification_run_exists'
    }
    $boundary = Get-PQProtectedBoundary
    $freeze = Get-PQSourceFreeze -IncludeFixture
    Assert-PQLauncherPath -Freeze $freeze | Out-Null
    $prelaunch = Assert-PQPrelaunchApproval -Freeze $freeze
    $null = Assert-PQCodexContract
    $environment = Get-PQEnvironmentHashes
    $supervisorToken = New-PQLaunchToken
    $supervisorTokenHash = Get-PQTokenHash -Token $supervisorToken
    $prelaunchAuditPath = Join-Path $RepoRoot ([string]$Profile.prelaunch_audit_path)
    $prelaunchAuditHash = Get-PQSha256 -Path $prelaunchAuditPath
    $lock = $null
    $statePath = $null
    try {
        New-Item -ItemType Directory -Path $runRoot | Out-Null
        $manifest = New-PQRunManifest -RunId $runId -RunRoot $runRoot -Boundary $boundary -Freeze $freeze -SupervisorTokenHash $supervisorTokenHash -Environment $environment -PrelaunchReviewerResultSha256 ([string]$prelaunch.reviewer_result_sha256)
        $manifest.kind = 'production'
        $manifestPath = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'run_manifest.json'
        Write-PQJsonAtomic -Path $manifestPath -Value $manifest
        Write-PQJsonAtomic -Path (Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'source_freeze.json') -Value $freeze
        $lock = New-PQActiveLock -ExternalRoot $externalRoot -Profile $Profile -RunId $runId -SupervisorPid 0 -SupervisorTokenHash $supervisorTokenHash -SourceFreezeSha256 ([string]$freeze.sha256) -PrelaunchAuditSha256 $prelaunchAuditHash -PrelaunchReviewerResultSha256 ([string]$prelaunch.reviewer_result_sha256)
        Set-PQActiveLockManifestBinding -ExternalRoot $externalRoot -Profile $Profile -RunId $runId -ManifestSha256 (Get-PQSha256 -Path $manifestPath) | Out-Null
        $state = New-PQInitialState -Profile $Profile -RunId $runId
        $state.supervisor_token_sha256 = $supervisorTokenHash
        $state.review_result_sha256 = $null
        $state.prelaunch_review_result_sha256 = [string]$prelaunch.reviewer_result_sha256
        $state.final_review_result_sha256 = $null
        $statePath = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'state.json'
        Write-PQJsonAtomic -Path $statePath -Value $state
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'prelaunch_validated' -Stage 'preflight'
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'source_frozen' -Stage 'source_freeze' -Patch @{ source_freeze_sha256 = [string]$freeze.sha256 }
        $supervisorTokenFile = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'supervisor.token'
        Write-PQTextAtomic -Path $supervisorTokenFile -Content $supervisorToken
        $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-QualificationProfile', [string]$Profile.profile, '-Mode', 'Supervisor', '-RunManifest', $manifestPath, '-LaunchTokenFile', $supervisorTokenFile)
        $supervisor = Start-PQProcess -Arguments $arguments -WorkingDirectory $RepoRoot
        Claim-PQActiveLockSupervisor -ExternalRoot $externalRoot -Profile $Profile -RunId $runId -SupervisorPid $supervisor.Id -SupervisorToken $supervisorToken -ManifestSha256 (Get-PQSha256 -Path $manifestPath) -SourceFreezeSha256 ([string]$freeze.sha256) -PrelaunchAuditSha256 $prelaunchAuditHash -PrelaunchReviewerResultSha256 ([string]$prelaunch.reviewer_result_sha256) | Out-Null
        Write-PQTextAtomic -Path (Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'supervisor.pid') -Content ([string]$supervisor.Id)
        $handoff = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'CLOSE_CODEX_DESKTOP_NOW.txt'
        $stateFile = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'state.json'
        $handoffDeadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $handoffDeadline) {
            if (-not (Test-PQProcessAlive -ProcessId $supervisor.Id)) { throw 'BLOCKED_DETACHED_WORKER_DIED' }
            if (Test-Path -LiteralPath $stateFile -PathType Leaf) {
                $handoffState = Read-PQJson -Path $stateFile
                $handoffSuffix = ([int]$handoffState.worker_generation).ToString() + ':' + [string]$handoffState.lease_id + ':' + ([int]$handoffState.worker_pid).ToString() + ':' + ([int]$handoffState.supervisor_pid).ToString()
                if (Test-PQRunBoundMarker -MarkerPath $handoff -RunId $runId -Prefix 'close_desktop_now' -Suffix $handoffSuffix) { break }
            }
            Start-Sleep -Milliseconds 250
        }
        if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) { throw 'BLOCKED_WORKER_NOT_ARMED' }
        $handoffState = Read-PQJson -Path $stateFile
        $handoffSuffix = ([int]$handoffState.worker_generation).ToString() + ':' + [string]$handoffState.lease_id + ':' + ([int]$handoffState.worker_pid).ToString() + ':' + ([int]$handoffState.supervisor_pid).ToString()
        if (-not (Test-PQRunBoundMarker -MarkerPath $handoff -RunId $runId -Prefix 'close_desktop_now' -Suffix $handoffSuffix)) { throw 'BLOCKED_WORKER_NOT_ARMED' }
        return [ordered]@{ status = 'ready_for_desktop_close'; run_id = $runId; supervisor_pid = $supervisor.Id; state_ref = 'state.json'; handoff_ref = 'CLOSE_CODEX_DESKTOP_NOW.txt' }
    } catch {
        # Never silently leave an active lock after a post-lock launch failure.
        # If a valid state exists, persist a bound blocked snapshot; otherwise
        # preserve the partial run root so the next Preflight fails closed.
        try {
            if ($null -ne $statePath -and (Test-Path -LiteralPath $statePath -PathType Leaf)) {
                $partial = Read-PQRunContext -ManifestPath $manifestPath
                if (@('completed', 'failed', 'blocked') -notcontains [string]$partial.state.state) {
                    $failure = Get-PQSanitizedError -Code 'WORKER_CONTRACT_FAILED' -Stage 'start' -Reason 'launch_initialization_failed'
                    Move-PQRunState -State $partial.state -StatePath $partial.state_path -NewState 'blocked' -Stage 'start' -ErrorObject $failure | Out-Null
                }
                foreach ($tokenLeaf in @('supervisor.token', 'worker.token')) {
                    $tokenPath = Resolve-PQRunChild -RunRoot $partial.run_root -RelativePath $tokenLeaf
                    if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
                        Test-PQNoReparseComponents -Path $tokenPath | Out-Null
                        Remove-Item -LiteralPath $tokenPath -Force
                    }
                }
            }
        } catch { }
        throw
    }
}

function Get-PQArtifactRecord {
    param(
        [Parameter(Mandatory)][string]$Kind,
        [Parameter(Mandatory)][string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'provider_qualification_artifact_missing'
    }
    Test-PQNoReparseComponents -Path $Path | Out-Null
    $item = Get-Item -LiteralPath $Path
    return [ordered]@{ kind = $Kind; sha256 = Get-PQSha256 -Path $Path; size_bytes = [int64]$item.Length }
}

function Get-PQCommandFingerprint {
    param(
        [Parameter(Mandatory)][ValidateSet('smoke','acceptance')][string]$Name,
        [string]$TaskId = [string]$Profile.task_id
    )

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($TaskId + ':' + $Name + ':v1')
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
}

function Test-PQJsonAgainstSchema {
    param(
        [Parameter(Mandatory)][string]$JsonPath,
        [Parameter(Mandatory)][string]$SchemaPath,
        [Parameter(Mandatory)][string]$ErrorPath
    )

    $code = 'import json,sys,jsonschema; jsonschema.validate(json.load(open(sys.argv[1],encoding="utf-8-sig")),json.load(open(sys.argv[2],encoding="utf-8-sig")))'
    $priorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $ignored = & $PythonExecutable -c $code $JsonPath $SchemaPath 2> $ErrorPath
        return ($LASTEXITCODE -eq 0)
    } finally {
        $ErrorActionPreference = $priorPreference
    }
}

function New-PQRawDirectory {
    param(
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][string]$Name
    )

    if ($Name -notmatch '^[a-z0-9_-]{1,32}$') {
        throw 'provider_qualification_raw_name_invalid'
    }
    $relative = Join-Path 'raw' $Name
    $path = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath $relative
    $parent = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath 'raw'
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    if (Test-Path -LiteralPath $path) {
        throw 'provider_qualification_raw_directory_exists'
    }
    New-Item -ItemType Directory -Path $path | Out-Null
    Test-PQNoReparseComponents -Path $path | Out-Null
    return $path
}

function Remove-PQRawDirectory {
    param(
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][string]$Name
    )

    if ($Name -notmatch '^[a-z0-9_-]{1,32}$') {
        throw 'provider_qualification_raw_name_invalid'
    }
    $path = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath (Join-Path 'raw' $Name)
    if (-not (Test-Path -LiteralPath $path)) {
        return
    }
    function Remove-PQSafeTree {
        param([Parameter(Mandatory)][string]$TreePath)
        Test-PQNoReparseComponents -Path $TreePath | Out-Null
        foreach ($child in @(Get-ChildItem -LiteralPath $TreePath -Force -ErrorAction Stop)) {
            $childPath = [string]$child.FullName
            Test-PQNoReparseComponents -Path $childPath | Out-Null
            if ($child.PSIsContainer) {
                Remove-PQSafeTree -TreePath $childPath
            } else {
                Remove-Item -LiteralPath $childPath -Force
            }
        }
        Test-PQNoReparseComponents -Path $TreePath | Out-Null
        Remove-Item -LiteralPath $TreePath -Force
    }
    Remove-PQSafeTree -TreePath $path
    if (Test-Path -LiteralPath $path) {
        throw 'provider_qualification_raw_cleanup_failed'
    }
}

function Remove-PQSafeValidationDirectory {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$AllowedRoot
    )

    $root = [System.IO.Path]::GetFullPath($AllowedRoot).TrimEnd('\') + '\'
    $target = [System.IO.Path]::GetFullPath($Path)
    if (-not $target.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase) -or
        $target.Equals($root.TrimEnd('\'), [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_validation_path_invalid'
    }
    if (-not (Test-Path -LiteralPath $target)) {
        return
    }

    function Remove-PQSafeValidationTree {
        param([Parameter(Mandatory)][string]$TreePath)
        Test-PQNoReparseComponents -Path $TreePath | Out-Null
        foreach ($child in @(Get-ChildItem -LiteralPath $TreePath -Force -ErrorAction Stop)) {
            $childPath = [string]$child.FullName
            if (-not $childPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw 'provider_qualification_validation_path_invalid'
            }
            Test-PQNoReparseComponents -Path $childPath | Out-Null
            if ($child.PSIsContainer) {
                Remove-PQSafeValidationTree -TreePath $childPath
            } else {
                Remove-Item -LiteralPath $childPath -Force
            }
        }
        Test-PQNoReparseComponents -Path $TreePath | Out-Null
        Remove-Item -LiteralPath $TreePath -Force
    }

    Remove-PQSafeValidationTree -TreePath $target
    if (Test-Path -LiteralPath $target) {
        throw 'provider_qualification_validation_cleanup_failed'
    }
}

function Stop-PQRunAtWorker {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$Code,
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][string]$Reason
    )

    $context = Read-PQRunContext -ManifestPath $ManifestPath
    if (@('completed', 'failed', 'blocked', 'rehearsal_completed') -contains [string]$context.state.state) {
        return $context.state
    }
    $error = Get-PQSanitizedError -Code $Code -Stage $Stage -Reason $Reason
    $terminalState = if ($Code -match '^(REAL_PROVIDER_|PROVIDER_RECOVERED_)') { 'failed' } else { 'blocked' }
    $stopped = Move-PQRunState -State $context.state -StatePath $context.state_path -NewState $terminalState -Stage $Stage -ErrorObject $error
    Write-PQRunMarker -RunRoot $context.run_root -Name 'BLOCKED.txt' -Content ('blocked:' + [string]$context.manifest.run_id + ':' + $Code) | Out-Null
    return $stopped
}

function Get-PQWorkerFailureCode {
    param([Parameter(Mandatory)][string]$Message)

    if ($Message -match '^(BLOCKED_[A-Z0-9_]+|REAL_PROVIDER_[A-Z0-9_]+|PROVIDER_RECOVERED_[A-Z0-9_]+)$') {
        return $Message
    }
    switch ($Message) {
        'provider_qualification_desktop_reappeared' { return 'BLOCKED_DESKTOP_NOT_QUIESCENT' }
        'provider_qualification_desktop_not_seen_before_wait' { return 'BLOCKED_DESKTOP_NOT_QUIESCENT' }
        'provider_qualification_cache_path_mismatch' { return 'BLOCKED_PROVIDER_CACHE_PATH_UNSAFE' }
        'provider_qualification_reparse_path_rejected' { return 'BLOCKED_PROVIDER_CACHE_PATH_UNSAFE' }
        'provider_qualification_cache_checkpoint_invalid' { return 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS' }
        'provider_qualification_smoke_checkpoint_invalid' { return 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS' }
        'provider_qualification_acceptance_checkpoint_invalid' { return 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS' }
        'provider_qualification_media_checkpoint_invalid' { return 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS' }
        default { return 'WORKER_CONTRACT_FAILED' }
    }
}

function Assert-PQLiveWorkerGates {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [switch]$RequireDesktopAbsent
    )

    $context = Read-PQRunContext -ManifestPath $ManifestPath
    Assert-PQActiveLockBinding -Context $context -Canary:$false | Out-Null
    Assert-PQNoOrphanTemporaryFiles -RunRoot $context.run_root
    Assert-PQProtectedBoundary -Expected $context.manifest.boundary | Out-Null
    Assert-PQSourceFreeze -ExpectedSha256 ([string]$context.manifest.source_freeze_sha256) -IncludeFixture | Out-Null
    Assert-PQEnvironmentHashes -Expected $context.manifest.environment | Out-Null
    if ([int]$context.state.supervisor_pid -le 0 -or -not (Test-PQProcessAlive -ProcessId ([int]$context.state.supervisor_pid))) {
        throw 'BLOCKED_SUPERVISOR_DIED'
    }
    if ($RequireDesktopAbsent -and @(Get-PQDesktopProcessSnapshot).Count -ne 0) {
        throw 'provider_qualification_desktop_reappeared'
    }
    return $context
}

function Get-PQCacheCheckpointPreparation {
    param([Parameter(Mandatory)]$Context)

    $state = $Context.state
    $original = [string]$state.original_cache_sha256
    if ($original -notmatch '^[0-9a-f]{64}$' -or [string]$state.cache_backup_sha256 -ne $original) {
        throw 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS'
    }
    $backupRoot = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath ('cache-' + $original.Substring(0, 16))
    $backupFile = Resolve-PQRunChild -RunRoot $backupRoot -RelativePath 'models_cache.original.json'
    $quarantineFile = Resolve-PQRunChild -RunRoot $backupRoot -RelativePath 'quarantine\models_cache.json'
    if ((Get-PQSha256 -Path $backupFile) -ne $original) {
        throw 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS'
    }

    $active = Assert-PQExactCachePath -Path $CachePath
    $strategy = [string]$state.cache_strategy
    if ([string]$state.state -eq 'cache_backed_up' -and $strategy -eq 'backup_only') {
        if ((Get-PQSha256 -Path $active) -ne $original) {
            throw 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS'
        }
        return [pscustomobject]@{ state = $state; backup_root = $backupRoot; backup_file = $backupFile; quarantine_file = $null; original_hash = $original; strategy = $strategy }
    }

    if ($strategy -eq 'quarantine_rebuild' -and -not (Test-Path -LiteralPath $active -PathType Leaf) -and
        (Get-PQSha256 -Path $quarantineFile) -eq $original) {
        if ([string]$state.state -eq 'cache_backed_up') {
            $state = Move-PQRunState -State $state -StatePath $Context.state_path -NewState 'cache_quarantined' -Stage 'cache_reconcile' -Patch @{ quarantine_cache_sha256 = $original }
        }
        return [pscustomobject]@{ state = $state; backup_root = $backupRoot; backup_file = $backupFile; quarantine_file = $quarantineFile; original_hash = $original; strategy = $strategy }
    }
    throw 'BLOCKED_CACHE_RECOVERY_AMBIGUOUS'
}

function Invoke-PQDesktopAndCachePreparation {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)]$State
    )

    $context = Assert-PQLiveWorkerGates -ManifestPath $ManifestPath
    $root = $context.run_root
    $statePath = $context.state_path
    $state = $context.state
    if (@('cache_backed_up', 'cache_quarantined') -contains [string]$state.state) {
        return Get-PQCacheCheckpointPreparation -Context $context
    }
    if ([string]$state.state -eq 'worker_armed') {
        if (@(Get-PQDesktopProcessSnapshot).Count -ne 0) {
            $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'waiting_for_desktop_exit' -Stage 'desktop_wait' -Patch @{ desktop_seen_before_quiescence = $true }
        } else {
            throw 'provider_qualification_desktop_not_seen_before_wait'
        }
    }
    if ([string]$state.state -eq 'waiting_for_desktop_exit') {
        $lease = [string]$state.lease_id
        $heartbeatPath = Resolve-PQRunChild -RunRoot $root -RelativePath 'heartbeat.json'
        $deadline = (Get-Date).AddSeconds(1800)
        $absent = 0
        while ((Get-Date) -lt $deadline -and $absent -lt 10) {
            $state = Write-PQWorkerHeartbeat -ManifestPath $ManifestPath -HeartbeatPath $heartbeatPath -LeaseId $lease -Stage 'desktop_wait'
            if (@(Get-PQDesktopProcessSnapshot).Count -eq 0) { $absent++ } else { $absent = 0 }
            if ($absent -lt 10) { Start-Sleep -Seconds 1 }
        }
        if ($absent -lt 10) {
            throw 'BLOCKED_DESKTOP_NOT_QUIESCENT'
        }
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'desktop_quiescent' -Stage 'desktop_quiescence' -Patch @{ desktop_quiescent = $true }
    }
    if ([string]$state.state -eq 'desktop_quiescent') {
        $lease = [string]$state.lease_id
        $heartbeatPath = Resolve-PQRunChild -RunRoot $root -RelativePath 'heartbeat.json'
        $samples = @()
        for ($index = 0; $index -lt 5; $index++) {
            $state = Write-PQWorkerHeartbeat -ManifestPath $ManifestPath -HeartbeatPath $heartbeatPath -LeaseId $lease -Stage 'cache_stability'
            $samples += Get-PQCacheSnapshot -Path $CachePath
            if ($index -lt 4) { Start-Sleep -Seconds 1 }
        }
        $keys = @($samples | ForEach-Object { "$($_.sha256)|$($_.size_bytes)|$($_.last_write_utc)" } | Select-Object -Unique)
        if ($keys.Count -ne 1 -or -not [bool]$samples[0].exists) {
            throw 'BLOCKED_PROVIDER_CACHE_DRIFT'
        }
        $snapshot = $samples[-1]
        $health = Get-PQCacheHealth -Snapshot $snapshot
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'cache_stable' -Stage 'cache_stability' -Patch @{
            original_cache_sha256 = [string]$snapshot.sha256
            active_cache_sha256 = [string]$snapshot.sha256
            cache_strategy = [string]$health.strategy
        }
    }
    if ([string]$state.state -ne 'cache_stable') {
        throw 'provider_qualification_cache_checkpoint_invalid'
    }
    Assert-PQLiveWorkerGates -ManifestPath $ManifestPath -RequireDesktopAbsent | Out-Null
    $original = [string]$state.original_cache_sha256
    $backupRoot = Resolve-PQRunChild -RunRoot $root -RelativePath ('cache-' + $original.Substring(0, 16))
    $requiresQuarantine = ([string]$state.cache_strategy -eq 'quarantine_rebuild')
    $state = Update-PQRunState -State $state -StatePath $statePath -Stage 'cache_backup_intent' -Patch @{
        cache_mutation_started = $requiresQuarantine
        rollback_required = $requiresQuarantine
    }
    $journalPath = Join-Path $backupRoot 'rollback_journal.json'
    try {
        New-Item -ItemType Directory -Path $backupRoot | Out-Null
        Write-PQJsonAtomic -Path $journalPath -Value ([ordered]@{
            run_id = [string]$context.manifest.run_id
            original_cache_sha256 = $original
            strategy = [string]$state.cache_strategy
            created_utc = [DateTime]::UtcNow.ToString('o')
        })
        $result = Invoke-PQCacheBackup -CachePath $CachePath -BackupRoot $backupRoot -OriginalHash $original -Strategy ([string]$state.cache_strategy)
    } catch {
        throw 'BLOCKED_PROVIDER_RECOVERY'
    }
    Assert-PQLiveWorkerGates -ManifestPath $ManifestPath -RequireDesktopAbsent | Out-Null
    $backupArtifact = Get-PQArtifactRecord -Kind 'original_cache_backup' -Path ([string]$result.backup)
    $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'cache_backed_up' -Stage 'cache_backup' -Patch @{
        cache_backup_sha256 = [string]$result.original_hash
        artifacts = @($state.artifacts) + @($backupArtifact)
    }
    if ([string]$result.strategy -eq 'quarantine_rebuild') {
        $quarantineArtifact = Get-PQArtifactRecord -Kind 'original_cache_quarantine' -Path ([string]$result.quarantine)
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'cache_quarantined' -Stage 'cache_quarantine' -Patch @{
            quarantine_cache_sha256 = [string]$result.original_hash
            artifacts = @($state.artifacts) + @($quarantineArtifact)
        }
    }
    return [pscustomobject]@{ state = $state; backup_root = $backupRoot; backup_file = [string]$result.backup; quarantine_file = [string]$result.quarantine; original_hash = $original; strategy = [string]$result.strategy }
}

function Invoke-PQSmoke {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)]$Preparation
    )

    $context = Assert-PQLiveWorkerGates -ManifestPath $ManifestPath -RequireDesktopAbsent
    $statePath = $context.state_path
    $state = $context.state
    Assert-PQLeaseCurrent -State $state
    if (@('cache_backed_up', 'cache_quarantined') -notcontains [string]$state.state) {
        throw 'provider_qualification_smoke_checkpoint_invalid'
    }
    $state = Claim-PQCommand -State $state -StatePath $statePath -Command smoke -NewState 'smoke_started' -Fingerprint (Get-PQCommandFingerprint -Name 'smoke') -TaskId ([string]$Profile.task_id)
    $supervisorLivenessProbe = New-PQWorkerSupervisorLivenessProbe -ManifestPath $ManifestPath -LeaseId ([string]$state.lease_id)
    $raw = New-PQRawDirectory -RunRoot $context.run_root -Name 'smoke'
    $promptPath = Join-Path $raw 'prompt.txt'
    $draftPath = Join-Path $raw 'director_draft.json'
    $stdoutPath = Join-Path $raw 'stdout.txt'
    $stderrPath = Join-Path $raw 'stderr.txt'
    $schemaErrorPath = Join-Path $raw 'schema-error.txt'
    $workDirectory = Join-Path $raw 'work'
    New-Item -ItemType Directory -Path $workDirectory | Out-Null
    $smokeReportPath = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'smoke_report.json'
    $started = Get-Date
    try {
        $prompt = '只输出符合给定 JSON Schema 的 JSON。创建 5 幕中文常青嵌入式 Modbus RTU DirectorDraft；第一幕 hook，最后一幕 summary；不得包含路径、asset_id、渲染参数或外部指令。'
        Write-PQTextAtomic -Path $promptPath -Content $prompt
        $codex = Assert-PQCodexContract -SupervisorLivenessProbe $supervisorLivenessProbe
        $command = Get-Command codex -ErrorAction Stop | Select-Object -First 1
        $commandPath = [string]$command.Source
        if ([string]::IsNullOrWhiteSpace($commandPath)) { $commandPath = [string]$command.Path }
        if ([string]::IsNullOrWhiteSpace($commandPath)) { $commandPath = [string]$command.Definition }
        $draftSchema = Join-Path $RepoRoot 'schemas\video\director_draft.schema.json'
        $arguments = @('exec', '--ephemeral', '--sandbox', 'read-only', '--skip-git-repo-check', '--ignore-user-config', '--color', 'never', '--output-schema', $draftSchema, '--output-last-message', $draftPath, '-C', $workDirectory, '-')
        $exitCode = Invoke-PQBoundedProcess -FilePath $PowerShellExecutable `
            -Arguments (@('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $commandPath) + $arguments) `
            -WorkingDirectory $workDirectory -StdOutPath $stdoutPath -StdErrPath $stderrPath `
            -InputText $prompt -TimeoutSeconds 180 -SupervisorLivenessProbe $supervisorLivenessProbe
        Assert-PQLeaseCurrent -State (Read-PQJson -Path $statePath)
        $elapsed = [math]::Round(((Get-Date) - $started).TotalSeconds, 3)
        $schemaValid = ($exitCode -eq 0 -and (Test-PQJsonAgainstSchema -JsonPath $draftPath -SchemaPath $draftSchema -ErrorPath $schemaErrorPath))
        $sceneCount = 0
        if ($schemaValid) {
            $draft = Read-PQJson -Path $draftPath
            $sceneCount = @($draft.scenes).Count
            $schemaValid = ($sceneCount -ge 5 -and $sceneCount -le 9)
        }
        $cacheAfter = Get-PQCacheSnapshot -Path $CachePath
        $cacheHealthy = $false
        try { $cacheHealthy = ((Get-PQCacheHealth -Snapshot $cacheAfter).status -eq 'healthy') } catch { $cacheHealthy = $false }
        $draftArtifact = if (Test-Path -LiteralPath $draftPath -PathType Leaf) { Get-PQArtifactRecord -Kind 'smoke_draft' -Path $draftPath } else { $null }
        Write-PQJsonAtomic -Path $smokeReportPath -Value ([ordered]@{
            run_id = [string]$context.manifest.run_id
            exit_code = [int]$exitCode
            elapsed_seconds = $elapsed
            draft_sha256 = if ($null -eq $draftArtifact) { $null } else { $draftArtifact.sha256 }
            draft_size_bytes = if ($null -eq $draftArtifact) { 0 } else { $draftArtifact.size_bytes }
            scene_count = $sceneCount
            schema_valid = [bool]$schemaValid
            cache_before_sha256 = [string]$Preparation.original_hash
            cache_after_sha256 = [string]$cacheAfter.sha256
            cache_model_count = [int]$cacheAfter.model_count
            cache_missing_base_instructions_count = [int]$cacheAfter.missing_base_instructions_count
        })
        if (-not $schemaValid -or -not $cacheHealthy) {
            $error = Get-PQSanitizedError -Code 'REAL_PROVIDER_BLOCKED_SMOKE' -Stage 'smoke' -Reason 'command_or_cache_health'
            $state = Complete-PQCommand -State $state -StatePath $statePath -Command smoke -NewState 'failed' -Outcome 'failed' -ErrorObject $error
            if ([string]$Preparation.strategy -eq 'quarantine_rebuild' -or [string]$cacheAfter.sha256 -ne [string]$Preparation.original_hash) {
                $evidence = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'cache-evidence'
                if (-not (Test-Path -LiteralPath $evidence -PathType Container)) { New-Item -ItemType Directory -Path $evidence | Out-Null }
                Restore-PQOriginalCache -CachePath $CachePath -BackupFile ([string]$Preparation.backup_file) -QuarantineFile ([string]$Preparation.quarantine_file) -OriginalHash ([string]$Preparation.original_hash) -EvidenceRoot $evidence | Out-Null
            }
            return $state
        }
        Remove-PQRawDirectory -RunRoot $context.run_root -Name 'smoke'
        $state = Update-PQRunState -State $state -StatePath $statePath -Stage 'smoke_cleanup' -Patch @{
            raw_cleanup_verified = $true
            active_cache_sha256 = [string]$cacheAfter.sha256
            artifacts = @($state.artifacts) + @(Get-PQArtifactRecord -Kind 'smoke_report' -Path $smokeReportPath)
        }
        return Complete-PQCommand -State $state -StatePath $statePath -Command smoke -NewState 'smoke_passed' -Outcome 'succeeded'
    } finally {
        if (Test-Path -LiteralPath $raw) {
            Remove-PQRawDirectory -RunRoot $context.run_root -Name 'smoke'
        }
    }
}

function Get-PQQualificationFixture {
    $fixtureRoot = Join-Path $RepoRoot ([string]$Profile.fixture_directory)
    $topicPath = Join-Path $fixtureRoot 'topic.txt'
    $briefPath = Join-Path $fixtureRoot 'factual_brief.json'
    if (-not (Test-Path -LiteralPath $topicPath -PathType Leaf) -or -not (Test-Path -LiteralPath $briefPath -PathType Leaf)) {
        throw 'provider_qualification_fixture_missing'
    }
    $topic = (Get-Content -LiteralPath $topicPath -Raw -Encoding UTF8).Normalize([System.Text.NormalizationForm]::FormKC).Trim()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($topic)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    $digest = ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
    if (-not [string]::IsNullOrWhiteSpace([string]$Profile.expected_topic_digest) -and
        $digest -ne [string]$Profile.expected_topic_digest) {
        throw 'provider_qualification_fixture_digest_invalid'
    }
    $jobId = 'director_' + $digest.Substring(0, 16)
    $workDir = Join-Path $RepoRoot ('dist\director\' + $jobId)
    $distRoot = Join-Path $RepoRoot 'dist\director'
    Test-PQNoReparseComponents -Path $distRoot | Out-Null
    Test-PQNoReparseComponents -Path $workDir | Out-Null
    return [pscustomobject]@{
        topic_path = $topicPath
        factual_brief_path = $briefPath
        topic_digest = $digest
        job_id = $jobId
        work_dir = $workDir
        fixture_directory = [string]$Profile.fixture_directory
        topic_relative = ([string]$Profile.fixture_directory + '/topic.txt')
        factual_brief_relative = ([string]$Profile.fixture_directory + '/factual_brief.json')
        output_name = [string]$Profile.output_name
    }
}

function Assert-PQFreshQualificationJob {
    $fixture = Get-PQQualificationFixture
    if (Test-Path -LiteralPath $fixture.work_dir) {
        Test-PQNoReparseComponents -Path $fixture.work_dir | Out-Null
        throw 'BLOCKED_FRESH_JOB_REQUIRED'
    }
    return $fixture
}

function Get-PQJsonDocument {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Assert-PQDirectorArtifactContract {
    param([Parameter(Mandatory)]$Fixture, [switch]$ReadOnly)

    $root = [string]$Fixture.work_dir
    Test-PQNoReparseComponents -Path $root | Out-Null
    $pairs = @(
        @('script.json', 'schemas\video\director_script.schema.json'),
        @('storyboard.json', 'schemas\video\storyboard.schema.json'),
        @('asset_selection.json', 'schemas\video\asset_selection_report.schema.json'),
        @('director_report.json', 'schemas\video\director_run_report.schema.json'),
        @('video_job_state.json', 'schemas\video\video_job_state.schema.json'),
        @('timeline.json', 'schemas\video\timeline.schema.json'),
        @('director_quality_report.json', 'schemas\video\director_quality_report.schema.json')
    )
    $validationRaw = Join-Path $root '.qualification-schema-check'
    if ($ReadOnly) {
        if (Test-Path -LiteralPath $validationRaw) { throw 'provider_qualification_validation_directory_exists' }
    } else {
        if (Test-Path -LiteralPath $validationRaw) { throw 'provider_qualification_validation_directory_exists' }
        New-Item -ItemType Directory -Path $validationRaw | Out-Null
    }
    try {
        foreach ($pair in $pairs) {
            $artifact = Join-Path $root $pair[0]
            $schema = Join-Path $RepoRoot $pair[1]
            if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
                throw 'provider_qualification_artifact_missing'
            }
            Test-PQNoReparseComponents -Path $artifact | Out-Null
            Test-PQNoReparseComponents -Path $schema | Out-Null
            $valid = $false
            if ($ReadOnly) {
                $validationCode = 'import json,sys,jsonschema; jsonschema.Draft202012Validator(json.load(open(sys.argv[2],encoding="utf-8-sig")),format_checker=jsonschema.FormatChecker()).validate(json.load(open(sys.argv[1],encoding="utf-8-sig")))'
                $null = & $PythonExecutable -c $validationCode $artifact $schema 2>$null
                $valid = ($LASTEXITCODE -eq 0)
            } else {
                $valid = Test-PQJsonAgainstSchema -JsonPath $artifact -SchemaPath $schema -ErrorPath (Join-Path $validationRaw ($pair[0] + '.err'))
            }
            if (-not $valid) {
                throw 'provider_qualification_artifact_schema_invalid'
            }
        }
        $script = Get-PQJsonDocument -Path (Join-Path $root 'script.json')
        $storyboard = Get-PQJsonDocument -Path (Join-Path $root 'storyboard.json')
        $selection = Get-PQJsonDocument -Path (Join-Path $root 'asset_selection.json')
        $directorReport = Get-PQJsonDocument -Path (Join-Path $root 'director_report.json')
        $state = Get-PQJsonDocument -Path (Join-Path $root 'video_job_state.json')
        $timeline = Get-PQJsonDocument -Path (Join-Path $root 'timeline.json')
        $quality = Get-PQJsonDocument -Path (Join-Path $root 'director_quality_report.json')
        if ([string]$directorReport.provider -ne 'codex-cli' -or [int]$directorReport.attempts -lt 1 -or [int]$directorReport.attempts -gt 3 -or $null -ne $directorReport.error) { throw 'provider_qualification_director_report_invalid' }
        if ([int]$quality.score -lt 85 -or [string]$quality.status -ne 'completed' -or [string]$quality.factual_review_status -ne 'verified') { throw 'provider_qualification_quality_report_invalid' }
        if ([string]$state.state -ne 'completed' -or [string]$state.factual_review_status -ne 'verified') { throw 'provider_qualification_job_state_invalid' }
        $scenes = @($storyboard.scenes)
        if ($scenes.Count -lt 5 -or $scenes.Count -gt 9 -or [string]$script.beats[0].purpose -ne 'hook' -or [string]$script.beats[$script.beats.Count - 1].purpose -ne 'summary') { throw 'provider_qualification_storyboard_semantics_invalid' }
        $assetIds = @($selection.selections | ForEach-Object { [string]$_.asset_id } | Select-Object -Unique)
        if ($assetIds.Count -lt 4 -or @($selection.selections | Where-Object { [string]$_.asset_id -notmatch '^pink_pig\.' -or [string]$_.rights_basis -notmatch 'repository-owned registry asset' }).Count -ne 0) { throw 'provider_qualification_asset_selection_invalid' }
        $scriptJson = ConvertTo-Json -InputObject $script -Depth 20
        if ($scriptJson -match '(?i)asset_id' -or $scriptJson -match '[A-Za-z]:[\\/]') { throw 'provider_qualification_script_leakage' }
        $timelineScenes = @($timeline.scenes)
        if ($timelineScenes.Count -ne $scenes.Count -or [string]$timeline.composition.composition_id -ne 'knowledge_illustration' -or
            [int]$timeline.composition.subtitle_style.font_size -lt 52 -or [int]$timeline.composition.subtitle_style.font_size -gt 60 -or
            [int]$timeline.composition.regions.content_area.y -ne 240 -or [int]$timeline.composition.regions.content_area.height -ne 800 -or
            [int]$timeline.composition.regions.subtitle_area.y -ne 1120 -or [int]$timeline.composition.regions.subtitle_area.height -ne 460 -or
            @($timelineScenes | Where-Object { [string]$_.layout_mode -ne 'knowledge_illustration' -or [string]$_.subtitle_layout -ne 'knowledge_illustration' }).Count -ne 0) {
            throw 'provider_qualification_timeline_composition_invalid'
        }
        return [pscustomobject]@{ scene_count = $scenes.Count; asset_count = $assetIds.Count; score = [int]$quality.score; timeline = $timeline }
    } finally {
        if (-not $ReadOnly -and (Test-Path -LiteralPath $validationRaw)) {
            Remove-PQSafeValidationDirectory -Path $validationRaw -AllowedRoot $root
        }
    }
}

function Invoke-PQAcceptance {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)]$State
    )

    $context = Assert-PQLiveWorkerGates -ManifestPath $ManifestPath -RequireDesktopAbsent
    $statePath = $context.state_path
    $state = $context.state
    Assert-PQLeaseCurrent -State $state
    if ([string]$state.state -ne 'smoke_passed') {
        throw 'provider_qualification_acceptance_checkpoint_invalid'
    }
    $fixture = Get-PQQualificationFixture
    $null = Assert-PQFreshQualificationJob
    $state = Claim-PQCommand -State $state -StatePath $statePath -Command acceptance -NewState 'acceptance_started' -Fingerprint (Get-PQCommandFingerprint -Name 'acceptance') -TaskId ([string]$Profile.task_id)
    $supervisorLivenessProbe = New-PQWorkerSupervisorLivenessProbe -ManifestPath $ManifestPath -LeaseId ([string]$state.lease_id)
    $raw = New-PQRawDirectory -RunRoot $context.run_root -Name 'acceptance'
    $stdoutPath = Join-Path $raw 'stdout.txt'
    $stderrPath = Join-Path $raw 'stderr.txt'
    $reportPath = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'acceptance_report.json'
    $started = Get-Date
    try {
        $exitCode = Invoke-PQBoundedProcess -FilePath $PythonExecutable `
            -Arguments @('generate_video.py', '--topic-file', $fixture.topic_relative, '--factual-brief', $fixture.factual_brief_relative, '--director-provider', 'codex-cli', '--output-name', $fixture.output_name) `
            -WorkingDirectory $RepoRoot -StdOutPath $stdoutPath -StdErrPath $stderrPath `
            -TimeoutSeconds 1800 -SupervisorLivenessProbe $supervisorLivenessProbe
        Assert-PQLeaseCurrent -State (Read-PQJson -Path $statePath)
        $elapsed = [math]::Round(((Get-Date) - $started).TotalSeconds, 3)
        $outputPath = Join-Path $fixture.work_dir $fixture.output_name
        $artifactAvailable = ($exitCode -eq 0 -and (Test-Path -LiteralPath $outputPath -PathType Leaf))
        Write-PQJsonAtomic -Path $reportPath -Value ([ordered]@{
            run_id = [string]$context.manifest.run_id
            exit_code = [int]$exitCode
            elapsed_seconds = $elapsed
            job_id = [string]$fixture.job_id
            output_present = [bool]$artifactAvailable
            output_sha256 = if ($artifactAvailable) { Get-PQSha256 -Path $outputPath } else { $null }
            output_size_bytes = if ($artifactAvailable) { [int64](Get-Item -LiteralPath $outputPath).Length } else { 0 }
        })
        if (-not $artifactAvailable) {
            $error = Get-PQSanitizedError -Code 'PROVIDER_RECOVERED_ACCEPTANCE_FAILED' -Stage 'acceptance' -Reason 'command_failed'
            return Complete-PQCommand -State $state -StatePath $statePath -Command acceptance -NewState 'failed' -Outcome 'failed' -ErrorObject $error
        }
        Remove-PQRawDirectory -RunRoot $context.run_root -Name 'acceptance'
        $state = Update-PQRunState -State $state -StatePath $statePath -Stage 'acceptance_cleanup' -Patch @{
            raw_cleanup_verified = $true
            artifacts = @($state.artifacts) + @(Get-PQArtifactRecord -Kind 'acceptance_report' -Path $reportPath)
        }
        return Complete-PQCommand -State $state -StatePath $statePath -Command acceptance -NewState 'acceptance_passed' -Outcome 'succeeded'
    } finally {
        if (Test-Path -LiteralPath $raw) {
            Remove-PQRawDirectory -RunRoot $context.run_root -Name 'acceptance'
        }
    }
}

function Invoke-PQRegressionSuite {
    param(
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][scriptblock]$SupervisorLivenessProbe
    )

    $raw = New-PQRawDirectory -RunRoot $RunRoot -Name 'regression'
    $reportPath = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath 'regression_report.json'
    $cases = @(
        [ordered]@{ name = 'director'; arguments = @('-m', 'pytest', 'tests/director', '-q'); minimum_passed = 47; exact_passed = $null; require_skipped = $null },
        [ordered]@{ name = 'video'; arguments = @('-m', 'pytest', 'tests/video', '-q'); minimum_passed = $null; exact_passed = 273; require_skipped = $null },
        [ordered]@{ name = 'video_factory'; arguments = @('-m', 'pytest', 'video_factory/tests', '-q'); minimum_passed = $null; exact_passed = 5; require_skipped = $null },
        [ordered]@{ name = 'legacy'; arguments = @('-m', 'pytest', 'tests/test_p1_candidate_cli.py', 'tests/test_p1_candidate_pipeline.py', 'tests/test_p1_candidate_media.py', 'tests/test_p1_candidate_render.py', 'tests/test_p1_candidate_delivery.py', 'tests/test_p1_candidate_inventory.py', 'tests/test_p1_candidate_state.py', 'tests/test_p1_final_audit.py', '-q'); minimum_passed = 56; exact_passed = $null; require_skipped = 1 }
    )
    $results = @()
    $allPassed = $true
    try {
        foreach ($case in $cases) {
            $stdoutPath = Join-Path $raw ([string]$case.name + '.stdout.txt')
            $stderrPath = Join-Path $raw ([string]$case.name + '.stderr.txt')
            $exitCode = Invoke-PQBoundedProcess -FilePath $PythonExecutable `
                -Arguments ([string[]]$case.arguments) -WorkingDirectory $RepoRoot `
                -StdOutPath $stdoutPath -StdErrPath $stderrPath -TimeoutSeconds 900 `
                -SupervisorLivenessProbe $SupervisorLivenessProbe
            Assert-PQLeaseCurrent -State (Read-PQJson -Path (Resolve-PQRunChild -RunRoot $RunRoot -RelativePath 'state.json'))
            $text = ((Get-Content -LiteralPath $stdoutPath -Raw -Encoding UTF8) + "`n" + (Get-Content -LiteralPath $stderrPath -Raw -Encoding UTF8))
            $passed = if ($text -match '([0-9]+) passed') { [int]$Matches[1] } else { 0 }
            $skipped = if ($text -match '([0-9]+) skipped') { [int]$Matches[1] } else { 0 }
            $casePassed = ($exitCode -eq 0)
            if ($null -ne $case.minimum_passed -and $passed -lt [int]$case.minimum_passed) { $casePassed = $false }
            if ($null -ne $case.exact_passed -and $passed -ne [int]$case.exact_passed) { $casePassed = $false }
            if ($null -ne $case.require_skipped -and $skipped -ne [int]$case.require_skipped) { $casePassed = $false }
            if (-not $casePassed) { $allPassed = $false }
            $results += [ordered]@{ name = [string]$case.name; exit_code = [int]$exitCode; passed = $passed; skipped = $skipped; passed_contract = [bool]$casePassed }
        }
        Write-PQJsonAtomic -Path $reportPath -Value ([ordered]@{ run_id = (Split-Path -Leaf $RunRoot); suites = $results; all_passed = [bool]$allPassed })
        if (-not $allPassed) {
            throw 'REAL_PROVIDER_MEDIA_OR_REGRESSION_FAILED'
        }
        return Get-PQArtifactRecord -Kind 'regression_report' -Path $reportPath
    } finally {
        if (Test-Path -LiteralPath $raw) {
            Remove-PQRawDirectory -RunRoot $RunRoot -Name 'regression'
        }
    }
}

function Invoke-PQMediaVerification {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)]$State
    )

    $context = Assert-PQLiveWorkerGates -ManifestPath $ManifestPath -RequireDesktopAbsent
    $mediaTools = Assert-PQMediaTools
    $statePath = $context.state_path
    $state = $context.state
    $supervisorLivenessProbe = New-PQWorkerSupervisorLivenessProbe -ManifestPath $ManifestPath -LeaseId ([string]$state.lease_id)
    Assert-PQLeaseCurrent -State $state
    if ([string]$state.state -ne 'acceptance_passed') {
        throw 'provider_qualification_media_checkpoint_invalid'
    }
    $fixture = Get-PQQualificationFixture
    $semantic = Assert-PQDirectorArtifactContract -Fixture $fixture
    $outputPath = Join-Path $fixture.work_dir $fixture.output_name
    $renderReportPath = Join-Path $fixture.work_dir 'render_report.json'
    $subtitlePath = Join-Path $fixture.work_dir 'subtitle.srt'
    $styleTokensPath = Join-Path $fixture.work_dir 'style_tokens.json'
    $runReportPath = Join-Path $fixture.work_dir 'run_report.json'
    foreach ($artifactPath in @($outputPath, $renderReportPath, $subtitlePath, $styleTokensPath, $runReportPath)) {
        if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) { throw 'provider_qualification_media_artifact_missing' }
        Test-PQNoReparseComponents -Path $artifactPath | Out-Null
    }
    $raw = New-PQRawDirectory -RunRoot $context.run_root -Name 'media'
    $probePath = Join-Path $raw 'ffprobe.json'
    $decodeStdoutPath = Join-Path $raw 'decode.out'
    $probeErrorPath = Join-Path $raw 'ffprobe.err'
    $decodeErrorPath = Join-Path $raw 'decode.err'
    $volumePath = Join-Path $raw 'volume.txt'
    $frameDirectory = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'frames'
    $summaryPath = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'media_validation.json'
    if (-not (Test-Path -LiteralPath $frameDirectory -PathType Container)) { New-Item -ItemType Directory -Path $frameDirectory | Out-Null }
    try {
        $decodeExit = Invoke-PQBoundedProcess -FilePath $mediaTools.ffmpeg `
            -Arguments @('-v', 'error', '-i', $outputPath, '-f', 'null', '-') `
            -WorkingDirectory $fixture.work_dir -StdOutPath $decodeStdoutPath -StdErrPath $decodeErrorPath -TimeoutSeconds 600 `
            -SupervisorLivenessProbe $supervisorLivenessProbe
        $probeExit = Invoke-PQBoundedProcess -FilePath $mediaTools.ffprobe `
            -Arguments @('-v', 'error', '-show_streams', '-show_format', '-of', 'json', $outputPath) `
            -WorkingDirectory $fixture.work_dir -StdOutPath $probePath -StdErrPath $probeErrorPath -TimeoutSeconds 300 `
            -SupervisorLivenessProbe $supervisorLivenessProbe
        $volumeExit = Invoke-PQBoundedProcess -FilePath $mediaTools.ffmpeg `
            -Arguments @('-i', $outputPath, '-af', 'volumedetect', '-f', 'null', 'NUL') `
            -WorkingDirectory $fixture.work_dir -StdOutPath (Join-Path $raw 'volume.out') -StdErrPath $volumePath -TimeoutSeconds 600 `
            -SupervisorLivenessProbe $supervisorLivenessProbe
        Assert-PQLeaseCurrent -State (Read-PQJson -Path $statePath)
        if ($decodeExit -ne 0 -or $probeExit -ne 0 -or $volumeExit -ne 0) { throw 'provider_qualification_media_command_failed' }
        $probe = Get-PQJsonDocument -Path $probePath
        $video = @($probe.streams | Where-Object { [string]$_.codec_type -eq 'video' }) | Select-Object -First 1
        $audio = @($probe.streams | Where-Object { [string]$_.codec_type -eq 'audio' }) | Select-Object -First 1
        $duration = [double]$probe.format.duration
        $fpsValue = [string]$video.avg_frame_rate
        $fps = if ($fpsValue -match '^([0-9]+)\/([0-9]+)$' -and [int]$Matches[2] -ne 0) { [double]$Matches[1] / [double]$Matches[2] } else { [double]$fpsValue }
        $volumeText = Get-Content -LiteralPath $volumePath -Raw -Encoding UTF8
        $maxVolume = if ($volumeText -match 'max_volume:\s*([-0-9.]+) dB') { [double]$Matches[1] } else { -999.0 }
        $render = Get-PQJsonDocument -Path $renderReportPath
        $subtitleText = Get-Content -LiteralPath $subtitlePath -Raw -Encoding UTF8
        $cueBlocks = @($subtitleText.Trim() -split '(?:\r?\n){2,}')
        $twoLine = $true
        foreach ($block in $cueBlocks) {
            $parts = @($block -split '\r?\n')
            if ($parts.Count -gt 2 -and @($parts[2..($parts.Count - 1)]).Count -gt 2) { $twoLine = $false }
        }
        $styleTokens = Get-PQJsonDocument -Path $styleTokensPath
        $subtitleRegion = $render.subtitle_region
        $runReport = Get-PQJsonDocument -Path $runReportPath
        $ttsSegments = @(Get-ChildItem -LiteralPath $fixture.work_dir -Filter 'seg_*.mp3' -File -ErrorAction Stop)
        foreach ($segment in $ttsSegments) { Test-PQNoReparseComponents -Path ([string]$segment.FullName) | Out-Null }
        $expectedAssets = @($semantic.timeline.scenes | ForEach-Object { [string]$_.asset_id })
        $actualAssets = @($render.asset_ids | ForEach-Object { [string]$_ })
        $assetsMatch = ($expectedAssets.Count -eq $actualAssets.Count)
        if ($assetsMatch) {
            for ($assetIndex = 0; $assetIndex -lt $expectedAssets.Count; $assetIndex++) {
                if ($expectedAssets[$assetIndex] -ne $actualAssets[$assetIndex]) { $assetsMatch = $false; break }
            }
        }
        $mediaValid = (
            [int]$video.width -eq 1080 -and [int]$video.height -eq 1920 -and
            [math]::Abs($fps - 30.0) -lt 0.01 -and [string]$video.codec_name -eq 'h264' -and
            [string]$audio.codec_name -eq 'aac' -and $duration -ge 25.0 -and $duration -le 60.0 -and $maxVolume -gt -50.0 -and
            [int]$render.resolution.width -eq 1080 -and [int]$render.resolution.height -eq 1920 -and
            [math]::Abs([double]$render.fps - 30.0) -lt 0.01 -and [string]$render.codec -eq 'h264' -and
            [math]::Abs([double]$render.duration - $duration) -lt 0.2 -and
            [bool]$render.audio.present -and [bool]$render.subtitle.present -and
            [int]$render.subtitle.cue_count -eq $cueBlocks.Count -and
            [int]$subtitleRegion.x -eq 90 -and [int]$subtitleRegion.y -eq 1120 -and [int]$subtitleRegion.width -eq 900 -and [int]$subtitleRegion.height -eq 460 -and
            $twoLine -and [string]$render.layout_mode -eq 'knowledge_illustration' -and
            [string]$styleTokens.composition_id -eq 'knowledge_illustration' -and [string]$styleTokens.mascot_mode -eq 'required' -and
            [string]$render.style_profile.status -eq 'pass' -and [string]$render.style_profile.character_id -eq 'pink_pig' -and
            [string]$render.style_profile.mascot_mode -eq 'required' -and $assetsMatch -and
            $ttsSegments.Count -eq [int]$semantic.scene_count -and [int]$runReport.audio_plan.segments_count -eq [int]$semantic.scene_count
        )
        if (-not $mediaValid) { throw 'provider_qualification_media_contract_invalid' }
        $sceneCount = [int]$semantic.scene_count
        for ($index = 1; $index -le $sceneCount; $index++) {
            $offset = [math]::Round((($index - 0.5) * $duration / $sceneCount), 3)
            $frame = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath (Join-Path 'frames' ('scene_' + $index.ToString('00') + '.jpg'))
            $frameStdout = Join-Path $raw ('frame_' + $index.ToString('00') + '.out')
            $frameStderr = Join-Path $raw ('frame_' + $index.ToString('00') + '.err')
            $frameExit = Invoke-PQBoundedProcess -FilePath $mediaTools.ffmpeg `
                -Arguments @('-v', 'error', '-ss', [string]$offset, '-i', $outputPath, '-frames:v', '1', '-q:v', '2', $frame) `
                -WorkingDirectory $fixture.work_dir -StdOutPath $frameStdout -StdErrPath $frameStderr -TimeoutSeconds 300 `
                -SupervisorLivenessProbe $supervisorLivenessProbe
            Assert-PQLeaseCurrent -State (Read-PQJson -Path $statePath)
            if ($frameExit -ne 0 -or -not (Test-Path -LiteralPath $frame -PathType Leaf)) { throw 'provider_qualification_frame_extract_failed' }
            Test-PQNoReparseComponents -Path $frame | Out-Null
            $state = Update-PQRunState -State $state -StatePath $statePath -Stage 'frame_extract' -Patch @{ artifacts = @($state.artifacts) + @(Get-PQArtifactRecord -Kind ('frame_' + $index) -Path $frame) }
        }
        Write-PQJsonAtomic -Path $summaryPath -Value ([ordered]@{
            run_id = [string]$context.manifest.run_id
            output_sha256 = Get-PQSha256 -Path $outputPath
            duration_seconds = [math]::Round($duration, 3)
            resolution = [ordered]@{ width = [int]$video.width; height = [int]$video.height }
            fps = $fps
            codec = [string]$video.codec_name
            audio_codec = [string]$audio.codec_name
            max_volume_db = $maxVolume
            scene_count = $sceneCount
            asset_count = [int]$semantic.asset_count
            subtitle_max_two_lines = $twoLine
            subtitle_region = [ordered]@{ y = [int]$subtitleRegion.y; height = [int]$subtitleRegion.height }
            tts_segments = $ttsSegments.Count
        })
        $regressionArtifact = Invoke-PQRegressionSuite -RunRoot $context.run_root -SupervisorLivenessProbe $supervisorLivenessProbe
        $state = Update-PQRunState -State $state -StatePath $statePath -Stage 'media_verified' -Patch @{ artifacts = @($state.artifacts) + @(Get-PQArtifactRecord -Kind 'media_validation' -Path $summaryPath) + @($regressionArtifact) }
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'verification_passed' -Stage 'verification'
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'complete_pending_review' -Stage 'verification'
        Write-PQRunMarker -RunRoot $context.run_root -Name 'READY_TO_REOPEN.txt' -Content ('ready_to_reopen:' + [string]$context.manifest.run_id) | Out-Null
        return $state
    } finally {
        if (Test-Path -LiteralPath $raw) {
            Remove-PQRawDirectory -RunRoot $context.run_root -Name 'media'
        }
    }
}

function Assert-PQVerifyReadOnlyContract {
    param([Parameter(Mandatory)]$Context)

    $manifest = $Context.manifest
    $state = $Context.state
    if ([string]$manifest.schema_version -ne '1.1') {
        return [ordered]@{ status = 'legacy_read_only'; state = [string]$state.state }
    }
    Assert-PQProtectedBoundary -Expected $manifest.boundary | Out-Null
    if ($null -ne $manifest.environment) {
        Assert-PQEnvironmentHashes -Expected $manifest.environment | Out-Null
    }
    Assert-PQNoOrphanTemporaryFiles -RunRoot $Context.run_root
    foreach ($tokenLeaf in @('supervisor.token', 'worker.token')) {
        $tokenPath = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath $tokenLeaf
        if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
            throw 'provider_qualification_launch_token_retained'
        }
    }
    $isRehearsal = ([string]$manifest.kind -eq 'rehearsal')
    $freeze = Read-PQJson -Path (Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'source_freeze.json')
    Assert-PQSourceFreezeDocument -Freeze $freeze -IncludeFixture:(-not $isRehearsal) | Out-Null
    if ([string]$Profile.profile -eq '005V' -and
        ((-not ($manifest.PSObject.Properties.Name -contains 'immutable_005t_evidence_sha256')) -or
         [string]$manifest.immutable_005t_evidence_sha256 -ne [string]$freeze.immutable_005t_evidence.sha256)) {
        throw 'provider_qualification_005t_immutable_evidence_binding_invalid'
    }

    $active = Read-PQActiveLock -ExternalRoot ([string]$Profile.external_root)
    if ($null -ne $active) {
        Assert-PQActiveLockBinding -Context $Context -Canary:$isRehearsal | Out-Null
    } elseif (@('completed', 'failed', 'blocked', 'rehearsal_completed') -contains [string]$state.state) {
        $terminal = Join-Path ([string]$Profile.external_root) ('.qualification.terminal.' + [string]$state.run_id + '.lock')
        if (-not (Test-Path -LiteralPath $terminal -PathType Leaf)) {
            throw 'provider_qualification_terminal_ledger_missing'
        }
        Test-PQNoReparseComponents -Path $terminal | Out-Null
        $terminalDocument = Read-PQJson -Path $terminal
        $terminalItem = Get-Item -LiteralPath $terminal -Force
        $manifestPath = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'run_manifest.json'
        if ([string]$terminalDocument.task_id -ne [string]$Profile.task_id -or
            [string]$terminalDocument.qualification_profile -ne [string]$Profile.profile -or
            [string]$terminalDocument.run_id -ne [string]$state.run_id -or
            [string]$terminalDocument.manifest_sha256 -ne (Get-PQSha256 -Path $manifestPath) -or
            [string]$terminalDocument.source_freeze_sha256 -ne [string]$Context.manifest.source_freeze_sha256 -or
            [bool]$terminalDocument.canary -ne [bool]$isRehearsal -or
            (-not $isRehearsal -and [string]$terminalDocument.prelaunch_audit_sha256 -ne (Get-PQSha256 -Path (Join-Path $RepoRoot ([string]$Profile.prelaunch_audit_path)))) -or
            (-not ($terminalItem.Attributes -band [System.IO.FileAttributes]::ReadOnly)) -or
            (-not $isRehearsal -and [string]$terminalDocument.prelaunch_reviewer_result_sha256 -ne [string]$Context.manifest.prelaunch_reviewer_result_sha256)) {
            throw 'provider_qualification_terminal_ledger_binding_invalid'
        }
    } else {
        throw 'provider_qualification_active_lock_missing'
    }

    foreach ($command in @('smoke', 'acceptance')) {
        $ledger = $state.$command
        if ([string]$ledger.status -eq 'not_started') {
            if ([int]$ledger.attempt_count -ne 0 -or $null -ne $ledger.command_fingerprint) {
                throw 'provider_qualification_command_ledger_invalid'
            }
        } else {
            if ([int]$ledger.attempt_count -ne 1 -or
                [string]$ledger.command_fingerprint -ne (Get-PQCommandFingerprint -Name $command -TaskId ([string]$manifest.task_id))) {
                throw 'provider_qualification_command_fingerprint_mismatch'
            }
        }
    }
    $artifactByKind = @{}
    foreach ($artifact in @($state.artifacts)) {
        if (-not [string]::IsNullOrWhiteSpace([string]$artifact.kind)) {
            $artifactByKind[[string]$artifact.kind] = $artifact
        }
    }
    if ([string]$state.smoke.status -eq 'succeeded') {
        $smokeReportPath = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'smoke_report.json'
        if (-not (Test-Path -LiteralPath $smokeReportPath -PathType Leaf)) { throw 'provider_qualification_smoke_report_missing' }
        $smokeReport = Read-PQJson -Path $smokeReportPath
        if ([string]$smokeReport.run_id -ne [string]$manifest.run_id -or [int]$smokeReport.exit_code -ne 0 -or
            -not [bool]$smokeReport.schema_valid -or [int]$smokeReport.scene_count -lt 5 -or [int]$smokeReport.scene_count -gt 9 -or
            [int]$smokeReport.cache_missing_base_instructions_count -ne 0 -or
            [string]$smokeReport.draft_sha256 -notmatch '^[0-9a-f]{64}$' -or [int64]$smokeReport.draft_size_bytes -le 0) {
            throw 'provider_qualification_smoke_report_binding_invalid'
        }
        if (-not $artifactByKind.ContainsKey('smoke_report') -or
            [string]$artifactByKind['smoke_report'].sha256 -ne (Get-PQSha256 -Path $smokeReportPath) -or
            [int64]$artifactByKind['smoke_report'].size_bytes -ne [int64](Get-Item -LiteralPath $smokeReportPath).Length) {
            throw 'provider_qualification_smoke_report_artifact_mismatch'
        }
    }
    if ([string]$state.acceptance.status -eq 'succeeded') {
        $acceptanceReportPath = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'acceptance_report.json'
        if (-not (Test-Path -LiteralPath $acceptanceReportPath -PathType Leaf)) { throw 'provider_qualification_acceptance_report_missing' }
        $acceptanceReport = Read-PQJson -Path $acceptanceReportPath
        $fixtureForReport = Get-PQQualificationFixture
        $outputPathForReport = Join-Path $fixtureForReport.work_dir $fixtureForReport.output_name
        if ([string]$acceptanceReport.run_id -ne [string]$manifest.run_id -or
            [string]$acceptanceReport.job_id -ne [string]$fixtureForReport.job_id -or
            [int]$acceptanceReport.exit_code -ne 0 -or -not [bool]$acceptanceReport.output_present -or
            [string]$acceptanceReport.output_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [int64]$acceptanceReport.output_size_bytes -le 0 -or
            -not (Test-Path -LiteralPath $outputPathForReport -PathType Leaf)) {
            throw 'provider_qualification_acceptance_report_binding_invalid'
        }
        Test-PQNoReparseComponents -Path $outputPathForReport | Out-Null
        if ([string]$acceptanceReport.output_sha256 -ne (Get-PQSha256 -Path $outputPathForReport) -or
            [int64]$acceptanceReport.output_size_bytes -ne [int64](Get-Item -LiteralPath $outputPathForReport).Length) {
            throw 'provider_qualification_acceptance_output_hash_mismatch'
        }
        if (-not $artifactByKind.ContainsKey('acceptance_report') -or
            [string]$artifactByKind['acceptance_report'].sha256 -ne (Get-PQSha256 -Path $acceptanceReportPath) -or
            [int64]$artifactByKind['acceptance_report'].size_bytes -ne [int64](Get-Item -LiteralPath $acceptanceReportPath).Length) {
            throw 'provider_qualification_acceptance_report_artifact_mismatch'
        }
    }
    if ([string]$state.state -in @('complete_pending_review', 'completed')) {
        if ([string]$state.smoke.status -ne 'succeeded' -or [string]$state.acceptance.status -ne 'succeeded' -or
            [string]$state.prelaunch_review_result_sha256 -ne [string]$manifest.prelaunch_reviewer_result_sha256) {
            throw 'provider_qualification_completion_contract_invalid'
        }
        $fixture = Get-PQQualificationFixture
        Assert-PQDirectorArtifactContract -Fixture $fixture -ReadOnly | Out-Null
        $mediaSummary = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'media_validation.json'
        if (-not (Test-Path -LiteralPath $mediaSummary -PathType Leaf)) {
            throw 'provider_qualification_media_summary_missing'
        }
        $media = Read-PQJson -Path $mediaSummary
        $fixtureOutput = Get-PQQualificationFixture
        $currentOutputPath = Join-Path $fixtureOutput.work_dir $fixtureOutput.output_name
        if (-not (Test-Path -LiteralPath $currentOutputPath -PathType Leaf)) {
            throw 'provider_qualification_media_output_missing'
        }
        Test-PQNoReparseComponents -Path $currentOutputPath | Out-Null
        $currentOutputSha256 = Get-PQSha256 -Path $currentOutputPath
        if ([string]$media.output_sha256 -notmatch '^[0-9a-f]{64}$' -or
            [string]$media.output_sha256 -ne $currentOutputSha256) {
            throw 'provider_qualification_media_output_hash_mismatch'
        }
        if ([double]$media.duration_seconds -lt 25.0 -or [double]$media.duration_seconds -gt 60.0 -or
            [int]$media.resolution.width -ne 1080 -or [int]$media.resolution.height -ne 1920 -or
            [math]::Abs([double]$media.fps - 30.0) -gt 0.01 -or [double]$media.max_volume_db -le -50.0) {
            throw 'provider_qualification_media_contract_invalid'
        }
    }
    if ([string]$state.state -eq 'completed') {
        $reviewMarker = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'FINAL_REVIEW_APPROVED.txt'
        $reviewResult = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'FINAL_REVIEW_RESULT.json'
        if (-not (Test-Path -LiteralPath $reviewResult -PathType Leaf) -or -not (Test-Path -LiteralPath $reviewMarker -PathType Leaf)) {
            throw 'provider_qualification_final_review_result_missing'
        }
        $reviewDocument = Read-PQJson -Path $reviewResult
        if ([string]$Profile.profile -eq '005V') {
            Assert-PQFinalReviewSchema -Review $reviewDocument
            Assert-PQFinalReviewBindings -Review $reviewDocument -Manifest $manifest -RunRoot $Context.run_root | Out-Null
        }
        $reviewHash = Get-PQSha256 -Path $reviewResult
        if ([string]$reviewDocument.task_id -ne [string]$manifest.task_id -or
            [string]$reviewDocument.run_id -ne [string]$manifest.run_id -or
            [string]$reviewDocument.verdict -ne 'APPROVED' -or
            [string]$reviewDocument.source_freeze_sha256 -ne [string]$manifest.source_freeze_sha256 -or
            [string]$reviewDocument.prelaunch_reviewer_result_sha256 -ne [string]$manifest.prelaunch_reviewer_result_sha256 -or
            $null -eq $reviewDocument.boundary -or
            [string]$reviewDocument.boundary.branch -ne [string]$manifest.boundary.branch -or
            [string]$reviewDocument.boundary.head -ne [string]$manifest.boundary.head -or
            [bool]$reviewDocument.boundary.index_empty -ne [bool]$manifest.boundary.index_empty -or
            [string]$state.final_review_result_sha256 -ne $reviewHash -or
            -not (Test-PQRunBoundMarker -MarkerPath $reviewMarker -RunId ([string]$manifest.run_id) -Prefix 'final_review_approved' -Suffix $reviewHash)) {
            throw 'provider_qualification_final_review_not_bound'
        }
    }
    if ([string]$state.state -eq 'rehearsal_completed') {
        $canaryMarker = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'CANARY_PASSED.txt'
        $closeMarker = Resolve-PQRunChild -RunRoot $Context.run_root -RelativePath 'CLOSE_CODEX_DESKTOP_NOW.txt'
        if (-not (Test-PQRunBoundMarker -MarkerPath $canaryMarker -RunId ([string]$manifest.run_id) -Prefix 'canary_passed' -Suffix (([int]$state.worker_generation).ToString() + ':' + [string]$state.lease_id + ':' + ([int]$state.worker_pid).ToString())) -or
            -not (Test-PQRunBoundMarker -MarkerPath $closeMarker -RunId ([string]$manifest.run_id) -Prefix 'close_desktop_now' -Suffix (([int]$state.worker_generation).ToString() + ':' + [string]$state.lease_id + ':' + ([int]$state.worker_pid).ToString() + ':' + ([int]$state.supervisor_pid).ToString())) -or
            [int]$state.heartbeat_sequence -lt 3 -or -not [bool]$state.desktop_seen_before_quiescence -or -not [bool]$state.desktop_quiescent) {
            throw 'provider_qualification_rehearsal_evidence_invalid'
        }
    }
    $maxGeneration = [int]$Profile.max_worker_generations
    if ([int]$state.worker_generation -gt $maxGeneration -or [int]$state.worker_launch_count -gt $maxGeneration) {
        throw 'provider_qualification_worker_generation_invalid'
    }
    return [ordered]@{ status = 'passed'; state = [string]$state.state; run_id = [string]$manifest.run_id }
}

function Invoke-PQSupervisor {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [string]$SupervisorToken = '',
        [string]$SupervisorTokenFile = $null,
        [switch]$Canary
    )
    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $manifest = $context.manifest
    $root = $context.run_root
    $statePath = $context.state_path
    $state = $context.state
    Assert-PQNoOrphanTemporaryFiles -RunRoot $root
    $sourceFreeze = Read-PQJson -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'source_freeze.json')
    Assert-PQLauncherPath -Freeze $sourceFreeze | Out-Null
    if (-not [string]::IsNullOrWhiteSpace($SupervisorTokenFile)) {
        $SupervisorToken = Read-PQLaunchTokenFile -ManifestPath $ManifestPath -TokenFile $SupervisorTokenFile -ExpectedLeaf 'supervisor.token'
    }
    if (-not (Test-PQLaunchToken -Token $SupervisorToken -ExpectedHash ([string]$manifest.supervisor_token_sha256))) {
        throw 'provider_qualification_supervisor_token_invalid'
    }
    Assert-PQProtectedBoundary -Expected $manifest.boundary | Out-Null
    Assert-PQSourceFreeze -ExpectedSha256 ([string]$manifest.source_freeze_sha256) -IncludeFixture:(-not $Canary) | Out-Null
    $manifestHash = Get-PQSha256 -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'run_manifest.json')
    $sourceFreezeHash = [string]$manifest.source_freeze_sha256
    $prelaunchAuditHash = if ($Canary) { $null } else { Get-PQSha256 -Path (Join-Path $RepoRoot ([string]$Profile.prelaunch_audit_path)) }
    $prelaunchReviewerHash = if ($Canary) { $null } else { [string]$manifest.prelaunch_reviewer_result_sha256 }
    if ([string]$manifest.kind -ne $(if ($Canary) { 'rehearsal' } else { 'production' })) {
        throw 'provider_qualification_manifest_kind_mismatch'
    }
    Claim-PQActiveLockSupervisor -ExternalRoot ([string]$Profile.external_root) -Profile $Profile -RunId ([string]$manifest.run_id) -SupervisorPid $PID -SupervisorToken $SupervisorToken -ManifestSha256 $manifestHash -SourceFreezeSha256 $sourceFreezeHash -PrelaunchAuditSha256 $prelaunchAuditHash -PrelaunchReviewerResultSha256 $prelaunchReviewerHash | Out-Null
    if ([int]$state.supervisor_pid -eq 0) {
        $state = Update-PQRunState -State $state -StatePath $statePath -Patch @{ supervisor_pid = $PID } -Stage 'supervisor'
    }
    if ([int]$state.supervisor_pid -ne $PID) {
        throw 'provider_qualification_supervisor_pid_mismatch'
    }
    $script:PQInvocationAuthenticated = $true
    if ([string]$state.state -eq 'source_frozen') {
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'supervisor_started' -Stage 'supervisor'
    }
    if ([string]$manifest.kind -ne $(if ($Canary) { 'rehearsal' } else { 'production' })) {
        throw 'provider_qualification_manifest_kind_mismatch'
    }
    $generation = [int]$state.worker_generation + 1
    if ($generation -gt [int]$Profile.max_worker_generations) {
        $error = Get-PQSanitizedError -Code 'BLOCKED_WORKER_RESTART_LIMIT' -Stage 'supervisor' -Reason 'generation_limit'
        Move-PQRunState -State $state -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
        return
    }
    $lease = [guid]::NewGuid().ToString('N')
    $workerToken = New-PQLaunchToken
    $workerTokenHash = Get-PQTokenHash -Token $workerToken
    # The lease must outlive the longest bounded child command.  The Worker
    # still heartbeats between commands; this margin prevents a legitimate
    # 30-minute acceptance from expiring while its child is running.
    $leaseExpires = [DateTime]::UtcNow.AddMinutes($script:PQWorkerLeaseMinutes).ToString('o')
    $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'worker_started' -Stage 'worker_launch' -Patch @{
        worker_generation = $generation
        worker_launch_count = $generation
        lease_id = $lease
        lease_expires_utc = $leaseExpires
        worker_pid = 0
        worker_token_sha256 = $workerTokenHash
    }
    $workerTokenFile = Resolve-PQRunChild -RunRoot $root -RelativePath 'worker.token'
    # worker_started is a durable reservation.  The production-used startup
    # seam owns the complete initial handshake, including the exact durable
    # marker leaves.  Its callbacks keep the live behavior explicit while
    # letting TestDrive-only tests exercise the same sequence.
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-QualificationProfile', [string]$Profile.profile, '-Mode', 'Worker', '-RunManifest', $ManifestPath, '-LaunchTokenFile', $workerTokenFile)
    if ($Canary) { $arguments += '-Rehearsal' }
    $startup = Invoke-PQSupervisorWorkerStartup -State $state -StatePath $statePath -TokenFile $workerTokenFile -Token $workerToken `
        -RunRoot $root -RunId ([string]$manifest.run_id) -SupervisorPid $PID `
        -WriteToken { param($path, $content) Write-PQTextAtomic -Path $path -Content $content } `
        -StartProcess { Start-PQProcess -Arguments $arguments -WorkingDirectory $RepoRoot } `
        -WritePidFile { param($pid) Write-PQTextAtomic -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'worker.pid') -Content ([string]$pid) } `
        -PromoteReady { param($current, $path, $pid) Move-PQRunState -State $current -StatePath $path -NewState 'supervisor_ready' -Stage 'supervisor' -Patch @{ worker_pid = $pid } } `
        -RemoveToken { param($path) if (Test-Path -LiteralPath $path -PathType Leaf) { Test-PQNoReparseComponents -Path $path | Out-Null; Remove-Item -LiteralPath $path -Force } } `
        -RemovePidFile { param($pid) $pidPath = Resolve-PQRunChild -RunRoot $root -RelativePath 'worker.pid'; if (Test-Path -LiteralPath $pidPath -PathType Leaf) { Test-PQNoReparseComponents -Path $pidPath | Out-Null; Remove-Item -LiteralPath $pidPath -Force } } `
        -WriteMarker { param($runRoot, $name, $content) Write-PQRunMarker -RunRoot $runRoot -Name $name -Content $content } `
        -WaitForWorkerReady {
            param($current, $worker, $runRoot, $runId, $workerGeneration, $workerLease)
            $ready = Resolve-PQRunChild -RunRoot $runRoot -RelativePath 'WORKER_READY.txt'
            $deadline = (Get-Date).AddSeconds(60)
            while ((Get-Date) -lt $deadline -and -not (Test-PQRunBoundMarker -MarkerPath $ready -RunId $runId -Prefix 'worker_ready' -Suffix ($workerGeneration.ToString() + ':' + $workerLease + ':' + $worker.Id))) {
                if (-not (Test-PQProcessAlive -ProcessId $worker.Id)) {
                    return [pscustomobject]@{ ready = $false; code = 'BLOCKED_DETACHED_WORKER_DIED'; reason = 'worker_died_before_ready' }
                }
                Start-Sleep -Milliseconds 250
            }
            if (-not (Test-PQRunBoundMarker -MarkerPath $ready -RunId $runId -Prefix 'worker_ready' -Suffix ($workerGeneration.ToString() + ':' + $workerLease + ':' + $worker.Id))) {
                $code = if (-not (Test-PQProcessAlive -ProcessId $worker.Id)) { 'BLOCKED_DETACHED_WORKER_DIED' } else { 'BLOCKED_WORKER_NOT_ARMED' }
                $reason = if ($code -eq 'BLOCKED_DETACHED_WORKER_DIED') { 'worker_died_before_ready' } else { 'handshake_missing' }
                return [pscustomobject]@{ ready = $false; code = $code; reason = $reason }
            }
            return [pscustomobject]@{ ready = $true; code = $null; reason = $null }
        } `
        -ArmWorker { param($current, $path) Move-PQRunState -State $current -StatePath $path -NewState 'worker_armed' -Stage 'worker_armed' } `
        -BlockState { param($current, $path, $error, $stage) Move-PQRunState -State $current -StatePath $path -NewState 'blocked' -Stage $stage -ErrorObject $error }
    if (-not [bool]$startup.succeeded) {
        if (-not [bool]$startup.blocked_persisted) { throw 'provider_qualification_failure_state_persist_failed' }
        return
    }
    $state = $startup.state
    $worker = $startup.worker
    $workerPid = [int]$startup.worker_pid
    if ($Canary) {
        Write-PQRunMarker -RunRoot $root -Name 'CANARY_ARMED_TO_CLOSE_DESKTOP.txt' -Content ('canary_armed:' + [string]$manifest.run_id + ':' + $generation + ':' + $lease + ':' + $worker.Id + ':' + $PID) | Out-Null
    }
    Write-PQRunMarker -RunRoot $root -Name 'REOPEN_NOT_BEFORE_UTC.txt' -Content ('reopen_not_before:' + [string]$manifest.run_id + ':' + [DateTime]::UtcNow.AddMinutes(30).ToString('o')) | Out-Null
    $workerDeadline = (Get-Date).AddMinutes($script:PQWorkerWallClockMinutes)
    while ($true) {
        while (Test-PQProcessAlive -ProcessId $worker.Id) {
            if ((Get-Date) -ge $workerDeadline) {
                $latest = Read-PQJson -Path $statePath
                $error = Get-PQSanitizedError -Code 'BLOCKED_WORKER_LEASE_EXPIRED' -Stage 'supervisor' -Reason 'worker_wall_clock_timeout'
                Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
                return
            }
            Start-Sleep -Seconds 1
        }
        $latest = Read-PQJson -Path $statePath
        $disposition = Get-PQWorkerRecoveryDisposition -State $latest -MaxGenerations ([int]$Profile.max_worker_generations)
        if ($disposition -in @('terminal', 'handoff_pending')) {
            return
        }
        if ($disposition -eq 'command_outcome_unknown') {
            $error = Get-PQSanitizedError -Code 'BLOCKED_PROVIDER_OUTCOME_UNKNOWN' -Stage 'supervisor' -Reason 'command_claimed'
            Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
            return
        }
        if ($disposition -eq 'cache_reconciliation_required') {
            $error = Get-PQSanitizedError -Code 'BLOCKED_PROVIDER_RECOVERY' -Stage 'supervisor' -Reason 'cache_mutation_checkpoint'
            Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
            return
        }
        if ($disposition -eq 'generation_limit') {
            $error = Get-PQSanitizedError -Code 'BLOCKED_WORKER_RESTART_LIMIT' -Stage 'supervisor' -Reason 'generation_limit'
            Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
            return
        }
        if ($disposition -ne 'restart_safe' -or (Test-PQProcessAlive -ProcessId ([int]$latest.worker_pid))) {
            $error = Get-PQSanitizedError -Code 'BLOCKED_DETACHED_WORKER_DIED' -Stage 'supervisor' -Reason 'checkpoint_unsafe'
            Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
            return
        }
        Wait-PQLeaseExpiry -State $latest
        Assert-PQProtectedBoundary -Expected $manifest.boundary | Out-Null
        Assert-PQSourceFreeze -ExpectedSha256 ([string]$manifest.source_freeze_sha256) -IncludeFixture:(-not $Canary) | Out-Null
        $nextGeneration = [int]$latest.worker_generation + 1
        $nextLease = [guid]::NewGuid().ToString('N')
        $nextToken = New-PQLaunchToken
        $nextTokenHash = Get-PQTokenHash -Token $nextToken
        $latest = Update-PQRunState -State $latest -StatePath $statePath -Stage 'worker_recovery' -Patch @{
            worker_generation = $nextGeneration
            worker_launch_count = $nextGeneration
            worker_pid = 0
            worker_token_sha256 = $nextTokenHash
            lease_id = $nextLease
            lease_expires_utc = [DateTime]::UtcNow.AddMinutes($script:PQWorkerLeaseMinutes).ToString('o')
        }
        $recoveryTokenFile = Resolve-PQRunChild -RunRoot $root -RelativePath 'worker.token'
        Write-PQTextAtomic -Path $recoveryTokenFile -Content $nextToken
        $recoveryArguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-QualificationProfile', [string]$Profile.profile, '-Mode', 'Worker', '-RunManifest', $ManifestPath, '-LaunchTokenFile', $recoveryTokenFile)
        if ($Canary) { $recoveryArguments += '-Rehearsal' }
        $worker = Start-PQProcess -Arguments $recoveryArguments -WorkingDirectory $RepoRoot
        $workerDeadline = (Get-Date).AddMinutes($script:PQWorkerWallClockMinutes)
        $latest = Update-PQRunState -State $latest -StatePath $statePath -Stage 'worker_recovery' -Patch @{ worker_pid = [int]$worker.Id }
        Write-PQTextAtomic -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'worker.pid') -Content ([string]$worker.Id)
        $recoveryReady = Resolve-PQRunChild -RunRoot $root -RelativePath 'WORKER_READY.txt'
        $recoveryDeadline = (Get-Date).AddSeconds(60)
        while ((Get-Date) -lt $recoveryDeadline -and -not (Test-PQRunBoundMarker -MarkerPath $recoveryReady -RunId ([string]$manifest.run_id) -Prefix 'worker_ready' -Suffix ($nextGeneration.ToString() + ':' + $nextLease + ':' + $worker.Id))) {
            if (-not (Test-PQProcessAlive -ProcessId $worker.Id)) {
                $error = Get-PQSanitizedError -Code 'BLOCKED_DETACHED_WORKER_DIED' -Stage 'supervisor' -Reason 'worker_died_before_ready'
                Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
                return
            }
            Start-Sleep -Milliseconds 250
        }
        if (-not (Test-PQRunBoundMarker -MarkerPath $recoveryReady -RunId ([string]$manifest.run_id) -Prefix 'worker_ready' -Suffix ($nextGeneration.ToString() + ':' + $nextLease + ':' + $worker.Id))) {
            $code = if (-not (Test-PQProcessAlive -ProcessId $worker.Id)) { 'BLOCKED_DETACHED_WORKER_DIED' } else { 'BLOCKED_WORKER_NOT_ARMED' }
            $reason = if ($code -eq 'BLOCKED_DETACHED_WORKER_DIED') { 'worker_died_before_ready' } else { 'recovery_handshake_missing' }
            $error = Get-PQSanitizedError -Code $code -Stage 'supervisor' -Reason $reason
            Move-PQRunState -State $latest -StatePath $statePath -NewState 'blocked' -Stage 'supervisor' -ErrorObject $error | Out-Null
            return
        }
        Write-PQRunMarker -RunRoot $root -Name 'LIVE_WORKER_ARMED.txt' -Content ('worker_armed:' + [string]$manifest.run_id + ':' + $nextGeneration + ':' + $nextLease + ':' + $worker.Id + ':' + $PID) | Out-Null
        if ($Canary) {
            Write-PQRunMarker -RunRoot $root -Name 'CANARY_ARMED_TO_CLOSE_DESKTOP.txt' -Content ('canary_armed:' + [string]$manifest.run_id + ':' + $nextGeneration + ':' + $nextLease + ':' + $worker.Id + ':' + $PID) | Out-Null
        }
    }
}

function Invoke-PQWorker {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [string]$WorkerToken = '',
        [string]$WorkerTokenFile = $null,
        [switch]$Canary
    )
    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $manifest = $context.manifest
    $root = $context.run_root
    $statePath = $context.state_path
    $state = $context.state
    Assert-PQNoOrphanTemporaryFiles -RunRoot $root
    $sourceFreeze = Read-PQJson -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'source_freeze.json')
    Assert-PQLauncherPath -Freeze $sourceFreeze | Out-Null
    if (-not [string]::IsNullOrWhiteSpace($WorkerTokenFile)) {
        $WorkerToken = Read-PQLaunchTokenFile -ManifestPath $ManifestPath -TokenFile $WorkerTokenFile -ExpectedLeaf 'worker.token'
    }
    if ([string]$manifest.kind -ne $(if ($Canary) { 'rehearsal' } else { 'production' })) {
        throw 'provider_qualification_manifest_kind_mismatch'
    }
    Assert-PQProtectedBoundary -Expected $manifest.boundary | Out-Null
    Assert-PQSourceFreeze -ExpectedSha256 ([string]$manifest.source_freeze_sha256) -IncludeFixture:(-not $Canary) | Out-Null
    $generation = [int]$state.worker_generation
    $lease = [string]$state.lease_id
    if ($generation -lt 1 -or [string]::IsNullOrWhiteSpace($lease) -or
        -not (Test-PQLaunchToken -Token $WorkerToken -ExpectedHash ([string]$state.worker_token_sha256))) {
        throw 'provider_qualification_worker_lease_missing'
    }
    $workerPidDeadline = (Get-Date).AddSeconds(15)
    # A persisted PID is necessary but not sufficient: the Supervisor must
    # finish its own durable ready transition before the Worker can attest to
    # readiness.  This prevents a launch-side persistence failure from racing
    # ahead into a misleading WORKER_READY marker.
    while (([int]$state.worker_pid -eq 0 -or [string]$state.state -ne 'supervisor_ready') -and (Get-Date) -lt $workerPidDeadline) {
        if (@('completed', 'failed', 'blocked') -contains [string]$state.state) {
            throw 'provider_qualification_worker_not_ready'
        }
        Start-Sleep -Milliseconds 100
        $state = (Read-PQRunContext -ManifestPath $ManifestPath).state
    }
    if ([string]$state.state -ne 'supervisor_ready' -or [int]$state.worker_pid -ne $PID) {
        throw 'provider_qualification_worker_pid_mismatch'
    }
    $script:PQInvocationAuthenticated = $true
    Publish-PQWorkerReadyMarker -State $state -RunRoot $root -RunId ([string]$manifest.run_id) -WorkerPid $PID `
        -WriteMarker { param($runRoot, $name, $content) Write-PQRunMarker -RunRoot $runRoot -Name $name -Content $content } | Out-Null
    $heartbeatPath = Resolve-PQRunChild -RunRoot $root -RelativePath 'heartbeat.json'
    $armedPath = Resolve-PQRunChild -RunRoot $root -RelativePath 'LIVE_WORKER_ARMED.txt'
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline -and -not (Test-PQRunBoundMarker -MarkerPath $armedPath -RunId ([string]$manifest.run_id) -Prefix 'worker_armed' -Suffix ($generation.ToString() + ':' + $lease + ':' + $PID + ':' + [int]$state.supervisor_pid))) {
        Write-PQHeartbeat -Path $heartbeatPath -State $state -ProcessId $PID -LeaseId $lease | Out-Null
        Start-Sleep -Milliseconds 500
    }
    if (-not (Test-PQRunBoundMarker -MarkerPath $armedPath -RunId ([string]$manifest.run_id) -Prefix 'worker_armed' -Suffix ($generation.ToString() + ':' + $lease + ':' + $PID + ':' + [int]$state.supervisor_pid))) {
        throw 'provider_qualification_worker_not_armed'
    }
    $closePath = Resolve-PQRunChild -RunRoot $root -RelativePath 'CLOSE_CODEX_DESKTOP_NOW.txt'
    $closeDeadline = (Get-Date).AddSeconds(30)
    $closeSuffix = $generation.ToString() + ':' + $lease + ':' + $PID + ':' + [int]$state.supervisor_pid
    while ((Get-Date) -lt $closeDeadline -and -not (Test-PQRunBoundMarker -MarkerPath $closePath -RunId ([string]$manifest.run_id) -Prefix 'close_desktop_now' -Suffix $closeSuffix)) {
        Write-PQHeartbeat -Path $heartbeatPath -State $state -ProcessId $PID -LeaseId $lease | Out-Null
        Start-Sleep -Milliseconds 250
    }
    if (-not (Test-PQRunBoundMarker -MarkerPath $closePath -RunId ([string]$manifest.run_id) -Prefix 'close_desktop_now' -Suffix $closeSuffix)) {
        throw 'provider_qualification_close_desktop_handoff_missing'
    }
    $state = (Read-PQRunContext -ManifestPath $ManifestPath).state
    if (@('worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up', 'cache_quarantined', 'smoke_passed', 'acceptance_passed', 'verification_passed', 'complete_pending_review') -notcontains [string]$state.state) {
        throw 'provider_qualification_worker_state_not_armed'
    }
    if ($Canary) {
        if ([string]$state.state -eq 'worker_armed' -and @(Get-PQDesktopProcessSnapshot).Count -eq 0) {
            $error = Get-PQSanitizedError -Code 'DETACHED_REHEARSAL_FAILED' -Stage 'rehearsal' -Reason 'desktop_not_seen'
            Move-PQRunState -State $state -StatePath $statePath -NewState 'blocked' -Stage 'rehearsal' -ErrorObject $error | Out-Null
            Write-PQRunMarker -RunRoot $root -Name 'CANARY_BLOCKED.txt' -Content ('canary_blocked:' + [string]$manifest.run_id + ':desktop_not_seen') | Out-Null
            return
        }
        if ([string]$state.state -eq 'worker_armed') {
            $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'waiting_for_desktop_exit' -Stage 'rehearsal' -Patch @{ desktop_seen_before_quiescence = $true }
        }
        $quiet = [string]$state.state -eq 'desktop_quiescent'
        if (-not $quiet) {
            $deadline = (Get-Date).AddSeconds(1800)
            $absent = 0
            while ((Get-Date) -lt $deadline -and $absent -lt 10) {
                $state = Write-PQWorkerHeartbeat -ManifestPath $ManifestPath -HeartbeatPath $heartbeatPath -LeaseId $lease -Stage 'rehearsal_wait'
                if (@(Get-PQDesktopProcessSnapshot).Count -eq 0) { $absent++ } else { $absent = 0 }
                if ($absent -lt 10) { Start-Sleep -Seconds 1 }
            }
            $quiet = ($absent -eq 10)
        }
        if (-not $quiet) {
            $error = Get-PQSanitizedError -Code 'DETACHED_REHEARSAL_FAILED' -Stage 'rehearsal' -Reason 'desktop_not_quiescent'
            Move-PQRunState -State $state -StatePath $statePath -NewState 'blocked' -Stage 'rehearsal' -ErrorObject $error | Out-Null
            Write-PQRunMarker -RunRoot $root -Name 'CANARY_BLOCKED.txt' -Content ('canary_blocked:' + [string]$manifest.run_id + ':desktop_not_quiescent') | Out-Null
            return
        }
        if ([string]$state.state -eq 'waiting_for_desktop_exit') {
            $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'desktop_quiescent' -Stage 'rehearsal' -Patch @{ desktop_quiescent = $true }
        }
        for ($index = 0; $index -lt 3; $index++) {
            if (@(Get-PQDesktopProcessSnapshot).Count -ne 0 -or -not (Test-PQProcessAlive -ProcessId ([int]$state.supervisor_pid))) {
                $error = Get-PQSanitizedError -Code 'DETACHED_REHEARSAL_FAILED' -Stage 'rehearsal' -Reason 'desktop_or_supervisor_reappeared'
                Move-PQRunState -State $state -StatePath $statePath -NewState 'blocked' -Stage 'rehearsal' -ErrorObject $error | Out-Null
                Write-PQRunMarker -RunRoot $root -Name 'CANARY_BLOCKED.txt' -Content ('canary_blocked:' + [string]$manifest.run_id + ':desktop_or_supervisor_reappeared') | Out-Null
                return
            }
            $state = Write-PQWorkerHeartbeat -ManifestPath $ManifestPath -HeartbeatPath $heartbeatPath -LeaseId $lease -Stage 'rehearsal'
            Start-Sleep -Seconds 7
        }
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'rehearsal_completed' -Stage 'rehearsal'
        Write-PQRunMarker -RunRoot $root -Name 'CANARY_PASSED.txt' -Content ('canary_passed:' + [string]$manifest.run_id + ':' + $generation + ':' + $lease + ':' + $PID) | Out-Null
        return
    }
    try {
        while ($true) {
            $state = (Read-PQRunContext -ManifestPath $ManifestPath).state
            if (@('completed', 'failed', 'blocked', 'rehearsal_completed') -contains [string]$state.state) {
                return
            }
            if (-not $Canary -and -not (Test-PQProcessAlive -ProcessId ([int]$state.supervisor_pid))) {
                throw 'BLOCKED_SUPERVISOR_DIED'
            }
            if (@('worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up', 'cache_quarantined') -contains [string]$state.state) {
                $preparation = Invoke-PQDesktopAndCachePreparation -ManifestPath $ManifestPath -State $state
                $state = $preparation.state
                if (@('failed', 'blocked') -contains [string]$state.state) { return }
                if (@('cache_backed_up', 'cache_quarantined') -contains [string]$state.state) {
                    $state = Invoke-PQSmoke -ManifestPath $ManifestPath -State $state -Preparation $preparation
                    if (@('failed', 'blocked') -contains [string]$state.state) { return }
                }
                continue
            }
            if ([string]$state.state -eq 'smoke_passed') {
                $state = Invoke-PQAcceptance -ManifestPath $ManifestPath -State $state
                if (@('failed', 'blocked') -contains [string]$state.state) { return }
                continue
            }
            if ([string]$state.state -eq 'acceptance_passed') {
                Invoke-PQMediaVerification -ManifestPath $ManifestPath -State $state | Out-Null
                continue
            }
            if (@('verification_passed', 'complete_pending_review') -contains [string]$state.state) {
                return
            }
            throw 'provider_qualification_worker_checkpoint_unrecognized'
        }
    } catch {
        $rawReason = [string]$_.Exception.Message
        $code = Get-PQWorkerFailureCode -Message $rawReason
        $reason = if ($rawReason -match '^[a-z0-9_]{1,96}$') { $rawReason } else { 'unexpected_error' }
        Stop-PQRunAtWorker -ManifestPath $ManifestPath -Code $code -Stage 'worker' -Reason $reason | Out-Null
    }
}

function Start-PQRehearsal {
    if (-not $Apply) {
        throw 'provider_qualification_rehearsal_requires_apply'
    }
    if (-not [bool]$Profile.allow_rehearsal) {
        throw 'provider_qualification_rehearsal_not_authorized'
    }
    if ([bool]$Profile.start_closed) {
        throw 'provider_qualification_run_closed'
    }
    $null = Get-PQPreflight
    $externalRoot = Assert-PQExternalRoot -Profile $Profile -ExternalRoot ([string]$Profile.external_root)
    New-PQRehearsalLedger -Profile $Profile | Out-Null
    $runId = 'session_rehearsal_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '_' + $PID
    $root = Assert-PQRunRoot -Profile $Profile -RunRoot (Join-Path $externalRoot $runId) -RunId $runId
    if (Test-Path -LiteralPath $root) {
        throw 'provider_qualification_run_exists'
    }
    $boundary = Get-PQProtectedBoundary
    $freeze = Get-PQSourceFreeze
    Assert-PQLauncherPath -Freeze $freeze | Out-Null
    $supervisorToken = New-PQLaunchToken
    $supervisorTokenHash = Get-PQTokenHash -Token $supervisorToken
    New-PQActiveLock -ExternalRoot $externalRoot -Profile $Profile -RunId $runId -SupervisorPid 0 -SupervisorTokenHash $supervisorTokenHash -SourceFreezeSha256 ([string]$freeze.sha256) -Canary | Out-Null
    try {
        New-Item -ItemType Directory -Path $root | Out-Null
        $manifest = New-PQRunManifest -RunId $runId -RunRoot $root -Boundary $boundary -Freeze $freeze -SupervisorTokenHash $supervisorTokenHash -Environment $null
        $manifest.kind = 'rehearsal'
        $manifestPath = Resolve-PQRunChild -RunRoot $root -RelativePath 'run_manifest.json'
        Write-PQJsonAtomic -Path $manifestPath -Value $manifest
        Write-PQJsonAtomic -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'source_freeze.json') -Value $freeze
        Set-PQActiveLockManifestBinding -ExternalRoot $externalRoot -Profile $Profile -RunId $runId -ManifestSha256 (Get-PQSha256 -Path $manifestPath) | Out-Null
        $state = New-PQInitialState -Profile $Profile -RunId $runId
        $state.supervisor_token_sha256 = $supervisorTokenHash
        $statePath = Resolve-PQRunChild -RunRoot $root -RelativePath 'state.json'
        Write-PQJsonAtomic -Path $statePath -Value $state
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'prelaunch_validated' -Stage 'rehearsal'
        $state = Move-PQRunState -State $state -StatePath $statePath -NewState 'source_frozen' -Stage 'rehearsal' -Patch @{ source_freeze_sha256 = [string]$freeze.sha256 }
        $supervisorTokenFile = Resolve-PQRunChild -RunRoot $root -RelativePath 'supervisor.token'
        Write-PQTextAtomic -Path $supervisorTokenFile -Content $supervisorToken
        $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-QualificationProfile', [string]$Profile.profile, '-Mode', 'Supervisor', '-RunManifest', $manifestPath, '-LaunchTokenFile', $supervisorTokenFile, '-Rehearsal')
        $supervisor = Start-PQProcess -Arguments $args -WorkingDirectory $RepoRoot
        Claim-PQActiveLockSupervisor -ExternalRoot $externalRoot -Profile $Profile -RunId $runId -SupervisorPid $supervisor.Id -SupervisorToken $supervisorToken | Out-Null
        Write-PQTextAtomic -Path (Resolve-PQRunChild -RunRoot $root -RelativePath 'supervisor.pid') -Content ([string]$supervisor.Id)
        $handoff = Resolve-PQRunChild -RunRoot $root -RelativePath 'CLOSE_CODEX_DESKTOP_NOW.txt'
        $stateFile = Resolve-PQRunChild -RunRoot $root -RelativePath 'state.json'
        $handoffDeadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $handoffDeadline) {
            if (-not (Test-PQProcessAlive -ProcessId $supervisor.Id)) { throw 'BLOCKED_DETACHED_WORKER_DIED' }
            if (Test-Path -LiteralPath $stateFile -PathType Leaf) {
                $handoffState = Read-PQJson -Path $stateFile
                $handoffSuffix = ([int]$handoffState.worker_generation).ToString() + ':' + [string]$handoffState.lease_id + ':' + ([int]$handoffState.worker_pid).ToString() + ':' + ([int]$handoffState.supervisor_pid).ToString()
                if (Test-PQRunBoundMarker -MarkerPath $handoff -RunId $runId -Prefix 'close_desktop_now' -Suffix $handoffSuffix) { break }
            }
            Start-Sleep -Milliseconds 250
        }
        if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) { throw 'BLOCKED_WORKER_NOT_ARMED' }
        $handoffState = Read-PQJson -Path $stateFile
        $handoffSuffix = ([int]$handoffState.worker_generation).ToString() + ':' + [string]$handoffState.lease_id + ':' + ([int]$handoffState.worker_pid).ToString() + ':' + ([int]$handoffState.supervisor_pid).ToString()
        if (-not (Test-PQRunBoundMarker -MarkerPath $handoff -RunId $runId -Prefix 'close_desktop_now' -Suffix $handoffSuffix)) { throw 'BLOCKED_WORKER_NOT_ARMED' }
        return [ordered]@{ status = 'rehearsal_ready_for_desktop_close'; run_id = $runId; supervisor_pid = $supervisor.Id; state_ref = 'state.json'; handoff_ref = 'CLOSE_CODEX_DESKTOP_NOW.txt' }
    } catch {
        # A launch failure must not leave a reusable capability in the
        # external run root.  Only the two exact token leaves are eligible;
        # no recursive cleanup is attempted here.
        foreach ($tokenLeaf in @('supervisor.token', 'worker.token')) {
            try {
                $tokenPath = Resolve-PQRunChild -RunRoot $root -RelativePath $tokenLeaf
                if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
                    Test-PQNoReparseComponents -Path $tokenPath | Out-Null
                    Remove-Item -LiteralPath $tokenPath -Force
                }
            } catch {
                # Preserve the original structured launch failure; Verify
                # will fail closed if a token remains.
            }
        }
        throw
    }
}

function Invoke-PQVerify {
    param([Parameter(Mandatory)][string]$ManifestPath, [switch]$ApplyFinalize)
    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $state = $context.state
    $contract = Assert-PQVerifyReadOnlyContract -Context $context
    if (-not $ApplyFinalize) {
        $smoke = if ([string]$state.schema_version -eq '1.0') {
            [ordered]@{ status = if ([bool]$state.smoke_attempted) { 'historical_attempted' } else { 'not_started' }; attempt_count = if ([bool]$state.smoke_attempted) { 1 } else { 0 }; command_fingerprint = $null }
        } else { $state.smoke }
        $acceptance = if ([string]$state.schema_version -eq '1.0') {
            [ordered]@{ status = if ([bool]$state.acceptance_attempted) { 'historical_attempted' } else { 'not_started' }; attempt_count = if ([bool]$state.acceptance_attempted) { 1 } else { 0 }; command_fingerprint = $null }
        } else { $state.acceptance }
        return [ordered]@{
            task_id = [string]$context.manifest.task_id
            qualification_profile = [string]$context.manifest.qualification_profile
            run_id = [string]$context.manifest.run_id
            state = [string]$state.state
            revision = [int]$state.revision
            prelaunch_review_result_sha256 = if ($state.PSObject.Properties.Name -contains 'prelaunch_review_result_sha256') { [string]$state.prelaunch_review_result_sha256 } else { $null }
            final_review_result_sha256 = if ($state.PSObject.Properties.Name -contains 'final_review_result_sha256') { [string]$state.final_review_result_sha256 } else { $null }
            smoke = $smoke
             acceptance = $acceptance
             contract = $contract
        }
    }
    if ([string]$Profile.schema_version -ne '1.1' -or [string]$state.state -ne 'complete_pending_review') {
        throw 'provider_qualification_finalize_not_allowed'
    }
    $review = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'FINAL_REVIEW_APPROVED.txt'
    $reviewResult = Resolve-PQRunChild -RunRoot $context.run_root -RelativePath 'FINAL_REVIEW_RESULT.json'
    if (-not (Test-Path -LiteralPath $reviewResult -PathType Leaf)) {
        throw 'provider_qualification_final_review_result_missing'
    }
    $reviewDocument = Read-PQJson -Path $reviewResult
    if ([string]$Profile.profile -eq '005V') {
        Assert-PQFinalReviewSchema -Review $reviewDocument
        Assert-PQFinalReviewBindings -Review $reviewDocument -Manifest $context.manifest -RunRoot $context.run_root | Out-Null
    }
    if ([string]$reviewDocument.task_id -ne [string]$context.manifest.task_id -or
        [string]$reviewDocument.run_id -ne [string]$context.manifest.run_id -or
        [string]$reviewDocument.verdict -ne 'APPROVED' -or
        [string]$reviewDocument.source_freeze_sha256 -ne [string]$context.manifest.source_freeze_sha256 -or
        [string]$reviewDocument.prelaunch_reviewer_result_sha256 -ne [string]$context.manifest.prelaunch_reviewer_result_sha256 -or
        $null -eq $reviewDocument.boundary -or
        [string]$reviewDocument.boundary.branch -ne [string]$context.manifest.boundary.branch -or
        [string]$reviewDocument.boundary.head -ne [string]$context.manifest.boundary.head -or
        [bool]$reviewDocument.boundary.index_empty -ne [bool]$context.manifest.boundary.index_empty) {
        throw 'provider_qualification_final_review_invalid'
    }
    $reviewHash = (Get-PQSha256 -Path $reviewResult)
    if ($reviewHash -notmatch '^[0-9a-f]{64}$' -or -not (Test-PQRunBoundMarker -MarkerPath $review -RunId ([string]$context.manifest.run_id) -Prefix 'final_review_approved' -Suffix $reviewHash)) {
        throw 'provider_qualification_final_review_not_bound'
    }
    $completed = Move-PQRunState -State $state -StatePath $context.state_path -NewState 'completed' -Stage 'finalize' -Patch @{ final_review_result_sha256 = $reviewHash }
    return [ordered]@{ status = 'completed'; run_id = [string]$completed.run_id; revision = [int]$completed.revision }
}

function Invoke-PQStatus {
    param([Parameter(Mandatory)][string]$ManifestPath)

    $context = Read-PQRunContext -ManifestPath $ManifestPath
    $state = $context.state
    $terminalLedger = $null
    if (@('completed', 'failed', 'blocked', 'rehearsal_completed') -contains [string]$state.state -and [string]$Profile.schema_version -eq '1.1') {
        $active = Read-PQActiveLock -ExternalRoot ([string]$Profile.external_root)
        if ($null -ne $active -and [string]$active.run_id -eq [string]$context.manifest.run_id) {
            $supervisorExited = -not (Test-PQProcessAlive -ProcessId ([int]$active.supervisor_pid))
            $workerExited = ([int]$state.worker_pid -eq 0) -or -not (Test-PQProcessAlive -ProcessId ([int]$state.worker_pid))
            if ($supervisorExited -and $workerExited) {
                Assert-PQActiveLockBinding -Context $context -Canary:([string]$context.manifest.kind -eq 'rehearsal') | Out-Null
                $terminalLedger = Convert-PQActiveLockToTerminal -ExternalRoot ([string]$Profile.external_root) -Profile $Profile -State $state -SupervisorExited $true -WorkerExited $true -Canary:([string]$context.manifest.kind -eq 'rehearsal')
            }
        }
    }
    return [ordered]@{
        task_id = [string]$context.manifest.task_id
        qualification_profile = [string]$context.manifest.qualification_profile
        run_id = [string]$context.manifest.run_id
        state = [string]$state.state
        revision = [int]$state.revision
        terminal_ledger_created = ($null -ne $terminalLedger)
    }
}

function Try-PQPersistTerminalFailure {
    param(
        [string]$ManifestPath,
        [string]$Code,
        [string]$Stage,
        [string]$Reason
    )

    if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
        return
    }
    try {
        $context = Read-PQRunContext -ManifestPath $ManifestPath
        if (@('completed', 'failed', 'blocked') -contains [string]$context.state.state) {
            return
        }
        $error = Get-PQSanitizedError -Code $Code -Stage $Stage -Reason $Reason
        $failed = Move-PQRunState -State $context.state -StatePath $context.state_path -NewState 'blocked' -Stage $Stage -ErrorObject $error
        Write-PQRunMarker -RunRoot $context.run_root -Name 'BLOCKED.txt' -Content ('blocked:' + [string]$context.manifest.run_id + ':' + $Code) | Out-Null
    } catch {
        # The original structured CLI envelope remains the only safe output if
        # the run identity itself cannot be trusted or persisted.
    }
}

if ($LoadOnly) {
    return
}

try {
    if ([string]$Profile.profile -in @('005V', '005V3') -and
        $Mode -in @('Preflight', 'Start', 'Rehearse', 'Supervisor', 'Worker', 'Status', 'Verify')) {
        if ($Mode -eq 'Preflight') {
            $changeRequest = Invoke-PQPreflightGate -Gate 'authorization' -Substep 'change_request' -Action {
                $request = Get-PQOperationalChangeRequest -Mode $Mode
                Assert-PQOperationalAuthorization -Profile $Profile -ChangeRequest $request -Mode $Mode | Out-Null
                return $request
            }
            $script:PQPreflightExpectedBoundary = if ([string]$Profile.profile -eq '005V3') { $changeRequest.protected_boundary } else { $null }
            Invoke-PQPreflightGate -Gate 'source_freeze' -Substep 'source_freeze_hash' -Action {
                if ([string]$Profile.profile -eq '005V3') {
                    # The diagnostic namespace is intentionally not allowed to
                    # reuse the consumed 005V2 bridge or the 005V production CR.
                    if ([string]$changeRequest.id -ne 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-DIAGNOSTICS-005V3') {
                        throw 'provider_qualification_change_request_invalid'
                    }
                }
                if ([string]$changeRequest.source_freeze_sha256 -ne [string](Get-PQSourceFreeze -IncludeFixture).sha256) {
                    throw 'provider_qualification_source_freeze_drift'
                }
                return $true
            } | Out-Null
        } else {
            $changeRequest = Get-PQOperationalChangeRequest -Mode $Mode
            Assert-PQOperationalAuthorization -Profile $Profile -ChangeRequest $changeRequest -Mode $Mode | Out-Null
        }
    }
    if ([bool]$Profile.start_closed -and $Mode -in @('Start', 'Supervisor', 'Worker', 'Rehearse')) {
        Write-PQCliFailure -Code 'provider_qualification_run_closed' -Stage 'profile' -Reason 'historical_run_closed'
        return
    }
    switch ($Mode) {
        'Preflight' { Write-PQCliObject -Value (Get-PQPreflight); break }
        'Start' { Write-PQCliObject -Value (Start-PQSupervisor); break }
        'Rehearse' { Write-PQCliObject -Value (Start-PQRehearsal); break }
        'Supervisor' { Invoke-PQSupervisor -ManifestPath $RunManifest -SupervisorTokenFile $LaunchTokenFile -Canary:$Rehearsal; break }
        'Worker' { Invoke-PQWorker -ManifestPath $RunManifest -WorkerTokenFile $LaunchTokenFile -Canary:$Rehearsal; break }
        'Status' { Write-PQCliObject -Value (Invoke-PQStatus -ManifestPath $RunManifest); break }
        'Verify' { Write-PQCliObject -Value (Invoke-PQVerify -ManifestPath $RunManifest -ApplyFinalize:$Finalize); break }
    }
} catch {
    $preflightContext = if ($Mode -eq 'Preflight') { Get-PQPreflightFailureContext -Exception $_.Exception } else { $null }
    if ($null -ne $preflightContext) {
        Write-PQCliFailure -Code 'provider_qualification_preflight_failed' -Stage 'preflight' -Reason ([string]$preflightContext.reason) -Gate ([string]$preflightContext.gate) -Substep ([string]$preflightContext.substep) -FailureExitCode $preflightContext.exit_code
        return
    }
    $reason = $_.Exception.Message
    if ($reason -notmatch '^[a-z0-9_]{1,96}$') {
        $reason = 'unexpected_error'
    }
    if ($Mode -in @('Supervisor', 'Worker') -and $script:PQInvocationAuthenticated) {
        Try-PQPersistTerminalFailure -ManifestPath $RunManifest -Code 'WORKER_CONTRACT_FAILED' -Stage 'qualification' -Reason $reason
    }
    Write-PQCliFailure -Code 'provider_qualification_failed' -Stage 'qualification' -Reason $reason
}
