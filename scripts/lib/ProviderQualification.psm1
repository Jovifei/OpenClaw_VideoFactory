Set-StrictMode -Version Latest

# Shared, profile-driven control primitives for the 005R/005S/005T/005V qualification
# tasks.  This module intentionally contains no Provider invocation.  It
# models and persists authorization, identity, and recovery state only.

$script:PQProfiles = @{
    '005R' = [ordered]@{
        profile = '005R'
        task_id = 'AI-DIRECTOR-PHASE2-DESKTOP-DETACHED-PROVIDER-QUALIFICATION-005R'
        schema_version = '1.0'
        external_root = 'E:\Claude_allow\Download\codex-provider-recovery-005r'
        fixture_directory = 'examples\ai_director_provider_qualification_005r'
        expected_topic_digest = $null
        output_name = 'pink_pig_modbus_ai_provider_005r.mp4'
        prelaunch_audit_path = 'reports\CODEX_PROVIDER_PRELAUNCH_AUDIT_005R.json'
        max_worker_generations = 1
        allow_rehearsal = $false
        start_closed = $true
    }
    '005S' = [ordered]@{
        profile = '005S'
        task_id = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
        schema_version = '1.1'
        external_root = 'E:\Claude_allow\Download\codex-provider-recovery-005s'
        fixture_directory = 'examples\ai_director_provider_qualification_005s'
        expected_topic_digest = '3aff643f8c6a7ab8f55f840bd7e3d8e61b583665e5c824bfa93f92c08db22d49'
        output_name = 'pink_pig_modbus_ai_provider_005s.mp4'
        prelaunch_audit_path = 'reports\CODEX_PROVIDER_PRELAUNCH_AUDIT_005S.json'
        max_worker_generations = 3
        allow_rehearsal = $true
        start_closed = $true
    }
    '005T' = [ordered]@{
        profile = '005T'
        task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
        schema_version = '1.1'
        external_root = 'E:\Claude_allow\Download\codex-provider-recovery-005t'
        fixture_directory = 'examples\ai_director_provider_qualification_005t'
        expected_topic_digest = 'fbe64e97fba1bcaaf2ff7de47d0385febe75f0b339cc5d3f543e4196d7f1fc70'
        output_name = 'pink_pig_modbus_ai_provider_005t.mp4'
        prelaunch_audit_path = 'reports\CODEX_PROVIDER_PRELAUNCH_AUDIT_005T.json'
        max_worker_generations = 1
        allow_rehearsal = $false
        start_closed = $true
    }
    '005V' = [ordered]@{
        profile = '005V'
        task_id = 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V'
        schema_version = '1.1'
        external_root = 'E:\Claude_allow\Download\codex-provider-recovery-005v'
        fixture_directory = 'examples\ai_director_provider_qualification_005v'
        expected_topic_digest = '1224cb6eb1e538f6b33f25664d19c8c22469ddff8b972e81b10404e81fc915d5'
        output_name = 'pink_pig_modbus_ai_provider_005v.mp4'
        prelaunch_audit_path = 'reports\CODEX_PROVIDER_PRELAUNCH_AUDIT_005V.json'
        max_worker_generations = 1
        allow_rehearsal = $false
        start_closed = $false
    }
    '005V3' = [ordered]@{
        profile = '005V3'
        task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-DIAGNOSTICS-005V3'
        schema_version = '1.1'
        external_root = 'E:\Claude_allow\Download\codex-provider-preflight-diagnostics-005v3'
        fixture_directory = 'examples\ai_director_provider_qualification_005v'
        expected_topic_digest = '1224cb6eb1e538f6b33f25664d19c8c22469ddff8b972e81b10404e81fc915d5'
        output_name = 'pink_pig_modbus_ai_provider_005v3.mp4'
        prelaunch_audit_path = 'reports\CODEX_PROVIDER_PRELAUNCH_AUDIT_005V3.json'
        max_worker_generations = 0
        allow_rehearsal = $false
        start_closed = $true
    }
}

$script:PQTerminalStates = @('completed', 'failed', 'blocked', 'rehearsal_completed')
$script:PQCommandStates = @('not_started', 'claimed', 'succeeded', 'failed', 'outcome_unknown')
$script:PQTransitions = @{
    '1.0' = @{
        prepared = @('waiting_for_desktop_exit', 'failed', 'blocked')
        waiting_for_desktop_exit = @('desktop_quiescent', 'failed', 'blocked')
        desktop_quiescent = @('cache_stable', 'failed', 'blocked')
        cache_stable = @('cache_quarantined', 'failed', 'blocked')
        cache_quarantined = @('smoke_started', 'failed', 'blocked')
        smoke_started = @('smoke_passed', 'failed', 'blocked')
        smoke_passed = @('acceptance_started', 'failed', 'blocked')
        acceptance_started = @('acceptance_passed', 'failed', 'blocked')
        acceptance_passed = @('verification_passed', 'failed', 'blocked')
        verification_passed = @('complete_pending_review', 'failed', 'blocked')
        complete_pending_review = @('completed', 'failed', 'blocked')
        completed = @()
        failed = @()
        blocked = @()
    }
    '1.1' = @{
        prepared = @('prelaunch_validated', 'failed', 'blocked')
        prelaunch_validated = @('source_frozen', 'failed', 'blocked')
        source_frozen = @('supervisor_started', 'failed', 'blocked')
        supervisor_started = @('worker_started', 'failed', 'blocked')
        worker_started = @('supervisor_ready', 'failed', 'blocked')
        supervisor_ready = @('worker_armed', 'failed', 'blocked')
        worker_armed = @('waiting_for_desktop_exit', 'failed', 'blocked')
        waiting_for_desktop_exit = @('desktop_quiescent', 'failed', 'blocked')
        desktop_quiescent = @('cache_stable', 'rehearsal_completed', 'failed', 'blocked')
        cache_stable = @('cache_backed_up', 'failed', 'blocked')
        cache_backed_up = @('cache_quarantined', 'smoke_started', 'failed', 'blocked')
        cache_quarantined = @('smoke_started', 'failed', 'blocked')
        smoke_started = @('smoke_passed', 'failed', 'blocked')
        smoke_passed = @('acceptance_started', 'failed', 'blocked')
        acceptance_started = @('acceptance_passed', 'failed', 'blocked')
        acceptance_passed = @('verification_passed', 'failed', 'blocked')
        verification_passed = @('complete_pending_review', 'failed', 'blocked')
        complete_pending_review = @('completed', 'failed', 'blocked')
        completed = @()
        failed = @()
        blocked = @()
        rehearsal_completed = @()
    }
}

function Get-PQProfile {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$QualificationProfile)

    if (-not $script:PQProfiles.ContainsKey($QualificationProfile)) {
        throw 'provider_qualification_profile_unknown'
    }
    return [pscustomobject]$script:PQProfiles[$QualificationProfile]
}

function Assert-PQOperationalAuthorization {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)]$ChangeRequest,
        [Parameter(Mandatory)][ValidateSet('Preflight', 'Start', 'Rehearse', 'Supervisor', 'Worker', 'Status', 'Verify')][string]$Mode
    )

    if ([string]$Profile.profile -eq '005V3') {
        if ($Mode -ne 'Preflight') {
            throw 'provider_qualification_diagnostic_profile_only'
        }
        if ($null -eq $ChangeRequest -or
            [string]$ChangeRequest.id -ne [string]$Profile.task_id -or
            [string]$ChangeRequest.mode -ne 'single_read_only_preflight_diagnostic' -or
            [string]$ChangeRequest.execution_status -ne 'ready_for_diagnostic_preflight' -or
            [int]$ChangeRequest.maximum_preflight_commands -ne 1 -or
            [int]$ChangeRequest.maximum_worker_generations -ne 0 -or
            [int]$ChangeRequest.maximum_smoke_commands -ne 0 -or
            [int]$ChangeRequest.maximum_acceptance_commands -ne 0 -or
            [bool]$ChangeRequest.allow_rehearsal -ne $false -or
            [bool]$ChangeRequest.allows_read_only_preflight_probes -ne $true -or
            [bool]$ChangeRequest.allows_read_only_metadata_probes -ne $true -or
            [bool]$ChangeRequest.allows_read_only_hash_probes -ne $true -or
            [bool]$ChangeRequest.allows_read_only_process_probes -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_cache_mutation -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_config_auth_mutation -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_desktop_control -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_desktop_operation -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_worker_start -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_provider_execution -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_oauth_profile_model_config_changes -ne $true -or
            [bool]$ChangeRequest.does_not_authorize_commit_or_push -ne $true) {
            throw 'provider_qualification_change_request_not_authorized'
        }
        return $true
    }

    $identityOk = ([string]$ChangeRequest.id -eq [string]$Profile.task_id) -or
        ([string]$ChangeRequest.mode -eq 'single_read_only_provider_preflight' -and
         [string]$ChangeRequest.parent_profile_task_id -eq [string]$Profile.task_id)
    if (-not $identityOk -or
        [bool]$ChangeRequest.does_not_authorize_oauth_profile_model_changes -ne $true -or
        [bool]$ChangeRequest.does_not_authorize_commit_or_push -ne $true) {
        throw 'provider_qualification_change_request_invalid'
    }
    if ($Mode -eq 'Rehearse' -or [bool]$ChangeRequest.allow_rehearsal) {
        throw 'provider_qualification_rehearsal_not_authorized'
    }

    $status = [string]$ChangeRequest.execution_status
    switch ($Mode) {
        'Preflight' {
            if ($status -notin @('contract_review_approved_pending_preflight', 'ready_for_worker', 'ready_for_preflight')) {
                throw 'provider_qualification_change_request_not_authorized'
            }
        }
        'Start' {
            if ($status -ne 'ready_for_worker') {
                throw 'provider_qualification_change_request_not_authorized'
            }
        }
        'Supervisor' {
            if ($status -notin @('ready_for_worker', 'provider_running')) {
                throw 'provider_qualification_change_request_not_authorized'
            }
        }
        'Worker' {
            if ($status -notin @('ready_for_worker', 'provider_running')) {
                throw 'provider_qualification_change_request_not_authorized'
            }
        }
        'Status' {
            if ($status -in @('prepared_pending_contract_review', 'baseline_blocked', 'implementation_in_progress')) {
                throw 'provider_qualification_change_request_not_authorized'
            }
        }
        'Verify' {
            if ($status -in @('prepared_pending_contract_review', 'baseline_blocked', 'implementation_in_progress')) {
                throw 'provider_qualification_change_request_not_authorized'
            }
        }
    }
    return $true
}

function Get-PQSanitizedError {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Code,
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][string]$Reason
    )

    $safeStage = if ($Stage -match '^[a-z0-9_]{1,64}$') { $Stage } else { 'qualification' }
    $safeReason = if ($Reason -match '^[a-z0-9_]{1,96}$') { $Reason } else { 'unexpected_error' }
    return [ordered]@{
        code = $Code
        message = 'Provider qualification stopped.'
        context = [ordered]@{ stage = $safeStage; reason = $safeReason }
    }
}

$script:PQPreflightGates = @(
    'authorization', 'source_freeze', 'external_root', 'active_lock',
    'fresh_job', 'fresh_evidence', 'git_boundary', 'codex_cli',
    'media_tools', 'immutable_005t', 'cache_snapshot',
    'environment_hashes', 'desktop_snapshot'
)
$script:PQPreflightSubsteps = @(
    'change_request', 'source_freeze_hash', 'external_root_path',
    'active_lock_probe', 'job_path', 'external_root_entries', 'git_index',
    'git_branch', 'git_head', 'dirty_files', 'path_resolution',
    'version_probe', 'help_probe', 'required_flags', 'tool_path', 'tool_hash',
    'evidence_identity', 'evidence_hash', 'json_parse', 'health',
    'baseline_hash', 'config_hash', 'auth_hash', 'process_probe'
)
$script:PQPreflightReasons = @(
    'change_request_missing', 'change_request_invalid',
    'change_request_not_authorized', 'source_freeze_drift',
    'active_run_exists', 'fresh_job_required', 'fresh_evidence_required',
    'git_index_changed', 'git_branch_changed', 'git_head_changed',
    'dirty_file_changed', 'cli_not_npm', 'cli_version_unsupported',
    'cli_help_unavailable', 'cli_flag_missing', 'media_tool_unavailable',
    'media_tool_changed', 'immutable_005t_invalid', 'immutable_005t_drift',
    'cache_missing', 'cache_invalid', 'cache_unhealthy',
    'environment_baseline_missing', 'config_changed', 'auth_changed',
    'desktop_probe_failed', 'unexpected_error'
)

function Get-PQStablePreflightReason {
    [CmdletBinding()]
    param([AllowNull()][string]$RawReason)

    $value = if ($null -eq $RawReason) { '' } else { $RawReason.ToLowerInvariant() }
    if ($script:PQPreflightReasons -contains $value) { return $value }
    $map = @{
        'provider_qualification_change_request_missing' = 'change_request_missing'
        'provider_qualification_change_request_invalid' = 'change_request_invalid'
        'provider_qualification_change_request_not_authorized' = 'change_request_not_authorized'
        'provider_qualification_source_freeze_drift' = 'source_freeze_drift'
        'provider_qualification_source_freeze_binding_invalid' = 'source_freeze_drift'
        'provider_qualification_source_freeze_missing' = 'source_freeze_drift'
        'provider_qualification_active_run_exists' = 'active_run_exists'
        'provider_qualification_run_exists' = 'active_run_exists'
        'provider_qualification_external_root_mismatch' = 'fresh_evidence_required'
        'provider_qualification_fixture_missing' = 'fresh_job_required'
        'provider_qualification_fixture_digest_invalid' = 'fresh_job_required'
        'blocked_fresh_job_required' = 'fresh_job_required'
        'blocked_fresh_evidence_required' = 'fresh_evidence_required'
        'provider_qualification_git_index_changed' = 'git_index_changed'
        'provider_qualification_git_branch_changed' = 'git_branch_changed'
        'provider_qualification_git_head_changed' = 'git_head_changed'
        'provider_qualification_dirty_file_changed' = 'dirty_file_changed'
        'provider_qualification_cli_not_npm' = 'cli_not_npm'
        'provider_qualification_cli_version_unsupported' = 'cli_version_unsupported'
        'provider_qualification_cli_help_unavailable' = 'cli_help_unavailable'
        'provider_qualification_cli_flag_missing' = 'cli_flag_missing'
        'provider_qualification_media_tool_unavailable' = 'media_tool_unavailable'
        'provider_qualification_media_tool_changed' = 'media_tool_changed'
        'provider_qualification_005t_immutable_evidence_invalid' = 'immutable_005t_invalid'
        'provider_qualification_005t_immutable_evidence_binding_invalid' = 'immutable_005t_invalid'
        'provider_qualification_005t_immutable_evidence_drift' = 'immutable_005t_drift'
        'provider_qualification_005t_immutable_evidence_missing' = 'immutable_005t_invalid'
        'provider_qualification_005v2_immutable_evidence_invalid' = 'immutable_005t_invalid'
        'provider_qualification_005v2_immutable_evidence_binding_invalid' = 'immutable_005t_invalid'
        'provider_qualification_005v2_immutable_evidence_drift' = 'immutable_005t_drift'
        'provider_qualification_cache_missing' = 'cache_missing'
        'blocked_provider_cache_missing' = 'cache_missing'
        'provider_qualification_cache_json_invalid' = 'cache_invalid'
        'provider_qualification_cache_invalid' = 'cache_invalid'
        'provider_qualification_cache_unhealthy' = 'cache_unhealthy'
        'blocked_provider_cache_drift' = 'cache_unhealthy'
        'provider_qualification_environment_baseline_missing' = 'environment_baseline_missing'
        'provider_qualification_config_changed' = 'config_changed'
        'provider_qualification_auth_changed' = 'auth_changed'
        'blocked_desktop_not_quiescent' = 'desktop_probe_failed'
        'blocked_desktop_probe_failed' = 'desktop_probe_failed'
    }
    if ($map.ContainsKey($value)) { return $map[$value] }
    return 'unexpected_error'
}

function New-PQPreflightFailure {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Gate,
        [Parameter(Mandatory)][string]$Substep,
        [Parameter(Mandatory)][string]$Reason,
        [AllowNull()][object]$ExitCode = $null
    )
    if ($script:PQPreflightGates -notcontains $Gate) { $Gate = 'authorization' }
    if ($script:PQPreflightSubsteps -notcontains $Substep) { $Substep = 'change_request' }
    if ($script:PQPreflightReasons -notcontains $Reason) { $Reason = 'unexpected_error' }
    $exception = [System.Exception]::new('Provider preflight stopped.')
    $exception.Data['pq_preflight'] = $true
    $exception.Data['gate'] = $Gate
    $exception.Data['substep'] = $Substep
    $exception.Data['reason'] = $Reason
    $exception.Data['exit_code'] = if ($null -eq $ExitCode) { $null } else { [int]$ExitCode }
    return $exception
}

function Get-PQPreflightFailureContext {
    [CmdletBinding()]
    param([AllowNull()][System.Exception]$Exception)
    if ($null -eq $Exception -or -not $Exception.Data.Contains('pq_preflight') -or
        [bool]$Exception.Data['pq_preflight'] -ne $true) { return $null }
    return [ordered]@{
        stage = 'preflight'
        gate = [string]$Exception.Data['gate']
        substep = [string]$Exception.Data['substep']
        reason = [string]$Exception.Data['reason']
        exit_code = if ($null -eq $Exception.Data['exit_code']) { $null } else { [int]$Exception.Data['exit_code'] }
    }
}

function Get-PQSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Write-PQJsonAtomic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Value
    )

    $parent = Split-Path -Parent $Path
    if ([string]::IsNullOrWhiteSpace($parent)) {
        throw 'provider_qualification_atomic_parent_missing'
    }
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Test-PQNoReparseComponents -Path $parent | Out-Null
    $temporary = Join-Path $parent ('.' + [System.IO.Path]::GetFileName($Path) + '.tmp.' + [guid]::NewGuid().ToString('N'))
    $replaceBackup = $null
    try {
        $json = $Value | ConvertTo-Json -Depth 20
        $encoding = New-Object System.Text.UTF8Encoding($false)
        $stream = New-Object System.IO.FileStream($temporary, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None, 4096, [System.IO.FileOptions]::WriteThrough)
        try {
            $writer = New-Object System.IO.StreamWriter($stream, $encoding)
            try {
                $writer.Write($json)
                $writer.Flush()
                $stream.Flush($true)
            } finally {
                $writer.Dispose()
            }
        } finally {
            $stream.Dispose()
        }
        Test-PQNoReparseComponents -Path $parent | Out-Null
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            Test-PQNoReparseComponents -Path $Path | Out-Null
            $replaceBackup = $temporary + '.replace-backup'
            [System.IO.File]::Replace($temporary, $Path, $replaceBackup, $true)
            if (Test-Path -LiteralPath $replaceBackup -PathType Leaf) {
                Remove-Item -LiteralPath $replaceBackup -Force
            }
        } else {
            [System.IO.File]::Move($temporary, $Path)
        }
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
        if ($null -ne $replaceBackup -and (Test-Path -LiteralPath $replaceBackup -PathType Leaf)) {
            Remove-Item -LiteralPath $replaceBackup -Force
        }
    }
}

function Write-PQTextAtomic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
    )

    $parent = Split-Path -Parent $Path
    if ([string]::IsNullOrWhiteSpace($parent) -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw 'provider_qualification_atomic_parent_missing'
    }
    Test-PQNoReparseComponents -Path $parent | Out-Null
    $temporary = Join-Path $parent ('.' + [System.IO.Path]::GetFileName($Path) + '.tmp.' + [guid]::NewGuid().ToString('N'))
    $replaceBackup = $null
    try {
        $encoding = New-Object System.Text.UTF8Encoding($false)
        $stream = New-Object System.IO.FileStream($temporary, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None, 4096, [System.IO.FileOptions]::WriteThrough)
        try {
            $writer = New-Object System.IO.StreamWriter($stream, $encoding)
            try {
                $writer.Write($Content)
                $writer.Flush()
                $stream.Flush($true)
            } finally {
                $writer.Dispose()
            }
        } finally {
            $stream.Dispose()
        }
        Test-PQNoReparseComponents -Path $parent | Out-Null
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            Test-PQNoReparseComponents -Path $Path | Out-Null
            $replaceBackup = $temporary + '.replace-backup'
            [System.IO.File]::Replace($temporary, $Path, $replaceBackup, $true)
            if (Test-Path -LiteralPath $replaceBackup -PathType Leaf) {
                Remove-Item -LiteralPath $replaceBackup -Force
            }
        } else {
            [System.IO.File]::Move($temporary, $Path)
        }
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
        if ($null -ne $replaceBackup -and (Test-Path -LiteralPath $replaceBackup -PathType Leaf)) {
            Remove-Item -LiteralPath $replaceBackup -Force
        }
    }
}

function Assert-PQNoOrphanTemporaryFiles {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$RunRoot)

    $root = [System.IO.Path]::GetFullPath($RunRoot).TrimEnd([char]92, [char]47) + [string][char]92
    Test-PQNoReparseComponents -Path $root | Out-Null
    $orphans = @(Get-ChildItem -LiteralPath $root -Force -Recurse -File -ErrorAction Stop | Where-Object { $_.Name -match '^\..+\.tmp\.[0-9a-f]{32}(\.replace-backup)?$' -or $_.Name -match '\.replace-backup$' })
    if ($orphans.Count -ne 0) {
        throw 'provider_qualification_orphan_temporary_file'
    }

    # Raw Provider material is deliberately short-lived.  A Worker is never
    # allowed to inherit it: doing so would either mix evidence between
    # generations or risk retaining prompt/model output after a crash.
    $rawRoot = Join-Path $root 'raw'
    if (Test-Path -LiteralPath $rawRoot -PathType Container) {
        Test-PQNoReparseComponents -Path $rawRoot | Out-Null
        $rawFiles = @(Get-ChildItem -LiteralPath $rawRoot -Force -Recurse -File -ErrorAction Stop)
        if ($rawFiles.Count -ne 0) {
            throw 'provider_qualification_raw_output_retained'
        }
    }
}

function Get-PQStateMutexName {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$StatePath)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes([System.IO.Path]::GetFullPath($StatePath).ToLowerInvariant())
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    $suffix = ([System.BitConverter]::ToString($hash)).Replace('-', '').Substring(0, 24)
    return 'Local\OpenClawVideoFactoryProviderQualification_' + $suffix
}

function Invoke-PQStateLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][scriptblock]$Action
    )

    $mutex = New-Object System.Threading.Mutex($false, (Get-PQStateMutexName -StatePath $StatePath))
    $entered = $false
    try {
        $entered = $mutex.WaitOne([TimeSpan]::FromSeconds(15))
        if (-not $entered) {
            throw 'provider_qualification_state_lock_timeout'
        }
        return (& $Action)
    } finally {
        if ($entered) {
            $mutex.ReleaseMutex()
        }
        $mutex.Dispose()
    }
}

function Read-PQJson {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'provider_qualification_json_missing'
    }
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Get-PQCurrentStateForMutation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$ExpectedState,
        [Parameter(Mandatory)][string]$StatePath
    )

    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        return $ExpectedState
    }
    $actual = Read-PQJson -Path $StatePath
    if ([int]$actual.revision -ne [int]$ExpectedState.revision -or
        [string]$actual.state -ne [string]$ExpectedState.state -or
        [string]$actual.run_id -ne [string]$ExpectedState.run_id) {
        throw 'provider_qualification_state_conflict'
    }
    return $actual
}

function Copy-PQObject {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Value)

    return ($Value | ConvertTo-Json -Depth 20 | ConvertFrom-Json)
}

function New-PQLaunchToken {
    [CmdletBinding()]
    param()

    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

function Get-PQTokenHash {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Token)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Token)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
}

function Test-PQLaunchToken {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][string]$ExpectedHash
    )

    if ($ExpectedHash -notmatch '^[0-9a-f]{64}$') {
        return $false
    }
    return ((Get-PQTokenHash -Token $Token) -eq $ExpectedHash)
}

function Get-PQCommandFingerprint {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][ValidateSet('smoke','acceptance')][string]$Name,
        [string]$TaskId = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
    )

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($TaskId + ':' + $Name + ':v1')
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
}

function Test-PQNoReparseComponents {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    $cursor = [System.IO.Path]::GetFullPath($Path)
    while (-not [string]::IsNullOrWhiteSpace($cursor)) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'provider_qualification_reparse_path_rejected'
            }
        }
        $parent = Split-Path -Parent $cursor
        if ($parent -eq $cursor -or [string]::IsNullOrWhiteSpace($parent)) {
            break
        }
        $cursor = $parent
    }
    return $true
}

function Resolve-PQRunChild {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][string]$RelativePath
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath -match '(^|[\\/])\.\.([\\/]|$)' -or
        [string]::IsNullOrWhiteSpace($RelativePath)) {
        throw 'provider_qualification_path_escape'
    }
    $root = [System.IO.Path]::GetFullPath($RunRoot).TrimEnd('\', '/') + '\'
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $root $RelativePath))
    if (-not $candidate.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_path_escape'
    }
    Test-PQNoReparseComponents -Path $candidate | Out-Null
    return $candidate
}

function Assert-PQRunRoot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][string]$RunId
    )

    if ([string]::IsNullOrWhiteSpace($RunId) -or $RunId -notmatch '^session_[A-Za-z0-9_.-]+$') {
        throw 'provider_qualification_run_id_invalid'
    }
    $expected = [System.IO.Path]::GetFullPath((Join-Path ([string]$Profile.external_root) $RunId))
    $actual = [System.IO.Path]::GetFullPath($RunRoot)
    if (-not $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_run_root_mismatch'
    }
    Test-PQNoReparseComponents -Path $actual | Out-Null
    return $actual
}

function Assert-PQExternalRoot {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$ExternalRoot
    )

    $expected = [System.IO.Path]::GetFullPath([string]$Profile.external_root).TrimEnd([char]92, [char]47)
    $actual = [System.IO.Path]::GetFullPath($ExternalRoot).TrimEnd([char]92, [char]47)
    if (-not $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_external_root_mismatch'
    }
    Test-PQNoReparseComponents -Path $actual | Out-Null
    return $actual
}

function Test-PQProcessAlive {
    [CmdletBinding()]
    param([Parameter(Mandatory)][int]$ProcessId)

    return ($null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue))
}

function ConvertTo-PQProcessArgument {
    [CmdletBinding()]
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Value)

    if ($Value -notmatch '[\s"]') { return $Value }
    # Windows CommandLineToArgvW quoting: double trailing backslashes before
    # the closing quote and escape embedded quotes.
    $quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\\"')
    $quoted = [regex]::Replace($quoted, '(\\+)$', '$1$1')
    return '"' + $quoted + '"'
}

function Initialize-PQJobTreeNative {
    [CmdletBinding()]
    param()

    if ($null -ne ('PQJobTree.Native' -as [type])) { return }
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

function Assert-PQSupervisorLivenessProbe {
    [CmdletBinding()]
    param([scriptblock]$SupervisorLivenessProbe = $null)

    if ($null -ne $SupervisorLivenessProbe -and -not [bool](& $SupervisorLivenessProbe)) {
        throw 'BLOCKED_SUPERVISOR_DIED'
    }
    return $true
}

function Invoke-PQBoundedProcess {
    [CmdletBinding()]
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

    Initialize-PQJobTreeNative
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = [string]::Join(' ', @($Arguments | ForEach-Object { ConvertTo-PQProcessArgument -Value ([string]$_) }))
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $job = [PQJobTree.Native]::CreateKillOnCloseJob()
    try {
        if (-not $process.Start()) { throw 'provider_qualification_command_start_failed' }
        try {
            [PQJobTree.Native]::Assign($job, $process.Handle)
        } catch {
            # Assignment failure means the process is not protected by the
            # kill-on-close Job Object.  Kill this direct child before
            # disposing handles so it cannot outlive the bounded invocation.
            try {
                if (-not $process.HasExited) {
                    $process.Kill()
                    $process.WaitForExit(5000)
                }
            } catch { }
            throw
        }
        $outTask = $process.StandardOutput.ReadToEndAsync()
        $errTask = $process.StandardError.ReadToEndAsync()
        if ($null -ne $InputText) {
            $process.StandardInput.Write($InputText)
        }
        $process.StandardInput.Close()
        $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
        while (-not $process.HasExited) {
            Assert-PQSupervisorLivenessProbe -SupervisorLivenessProbe $SupervisorLivenessProbe | Out-Null
            $remainingMilliseconds = [int][math]::Ceiling(($deadline - [DateTime]::UtcNow).TotalMilliseconds)
            if ($remainingMilliseconds -le 0) {
                throw 'provider_qualification_command_timeout'
            }
            $waitMilliseconds = [math]::Min($LivenessPollMilliseconds, $remainingMilliseconds)
            $process.WaitForExit($waitMilliseconds) | Out-Null
        }
        Assert-PQSupervisorLivenessProbe -SupervisorLivenessProbe $SupervisorLivenessProbe | Out-Null
        [System.Threading.Tasks.Task]::WaitAll(@($outTask, $errTask), 10000) | Out-Null
        Test-PQNoReparseComponents -Path $StdOutPath | Out-Null
        Test-PQNoReparseComponents -Path $StdErrPath | Out-Null
        [System.IO.File]::WriteAllText($StdOutPath, [string]$outTask.Result, (New-Object System.Text.UTF8Encoding($false)))
        [System.IO.File]::WriteAllText($StdErrPath, [string]$errTask.Result, (New-Object System.Text.UTF8Encoding($false)))
        return [int]$process.ExitCode
    } catch {
        # Every liveness fault, timeout, or stream failure terminates the full
        # assigned tree before the error reaches the Worker state machine.
        [PQJobTree.Native]::EndTree($job, 125)
        try { if (-not $process.HasExited) { $process.WaitForExit(5000) } } catch { }
        throw
    } finally {
        [PQJobTree.Native]::Close($job)
        $process.Dispose()
    }
}

function Assert-PQManifestPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$ManifestPath
    )

    if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
        throw 'provider_qualification_manifest_path_missing'
    }
    $full = [System.IO.Path]::GetFullPath($ManifestPath)
    $leaf = [System.IO.Path]::GetFileName($full)
    $parent = Split-Path -Parent $full
    $runId = Split-Path -Leaf $parent
    if ($leaf -ne 'run_manifest.json') {
        throw 'provider_qualification_manifest_path_mismatch'
    }
    $root = Assert-PQRunRoot -Profile $Profile -RunRoot $parent -RunId $runId
    $expected = Resolve-PQRunChild -RunRoot $root -RelativePath 'run_manifest.json'
    if (-not $full.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_manifest_path_mismatch'
    }
    return [pscustomobject]@{ manifest_path = $expected; run_root = $root; run_id = $runId }
}

function New-PQInitialState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$RunId
    )

    if ([string]$Profile.schema_version -eq '1.0') {
        return [pscustomobject][ordered]@{
            schema_version = '1.0'
            task_id = [string]$Profile.task_id
            run_id = $RunId
            revision = 1
            state = 'prepared'
            stage = 'preflight'
            desktop_quiescent = $false
            original_cache_sha256 = $null
            active_cache_sha256 = $null
            smoke_attempted = $false
            acceptance_attempted = $false
            artifacts = @()
            error = $null
        }
    }

    return [pscustomobject][ordered]@{
        schema_version = '1.1'
        task_id = [string]$Profile.task_id
        qualification_profile = [string]$Profile.profile
        run_id = $RunId
        revision = 1
        state = 'prepared'
        stage = 'preflight'
        desktop_quiescent = $false
        desktop_seen_before_quiescence = $false
        worker_generation = 0
        worker_launch_count = 0
        supervisor_pid = 0
        worker_pid = 0
        supervisor_token_sha256 = $null
        worker_token_sha256 = $null
        lease_id = $null
        lease_expires_utc = $null
        heartbeat_sequence = 0
        last_checkpoint = 'prepared'
        cache_mutation_started = $false
        rollback_required = $false
        cache_strategy = 'none'
        original_cache_sha256 = $null
        active_cache_sha256 = $null
        source_freeze_sha256 = $null
        cache_backup_sha256 = $null
        quarantine_cache_sha256 = $null
         raw_cleanup_verified = $false
         review_result_sha256 = $null
         prelaunch_review_result_sha256 = $null
         final_review_result_sha256 = $null
         smoke = [ordered]@{ status = 'not_started'; attempt_count = 0; command_fingerprint = $null }
        acceptance = [ordered]@{ status = 'not_started'; attempt_count = 0; command_fingerprint = $null }
        artifacts = @()
        error = $null
    }
}

function Assert-PQStateIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$RunId
    )

    if ([string]$State.task_id -ne [string]$Profile.task_id -or
        [string]$State.run_id -ne $RunId -or
        [string]$State.schema_version -ne [string]$Profile.schema_version) {
        throw 'provider_qualification_state_identity_mismatch'
    }
    if ([string]$Profile.schema_version -eq '1.1' -and [string]$State.qualification_profile -ne [string]$Profile.profile) {
        throw 'provider_qualification_state_profile_mismatch'
    }
}

function Get-PQStateSchemaTestMember {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$InputObject,
        [Parameter(Mandatory)][string]$Name
    )

    if ($InputObject -is [System.Collections.IDictionary]) {
        if (-not $InputObject.Contains($Name)) {
            throw 'provider_qualification_state_schema_invalid'
        }
        return $InputObject[$Name]
    }

    $property = $InputObject.PSObject.Properties[$Name]
    if ($null -eq $property) {
        throw 'provider_qualification_state_schema_invalid'
    }
    return $property.Value
}

function Assert-PQStateSchemaTestInteger {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Value,
        [Parameter(Mandatory)][int64]$Minimum,
        [int64]$Maximum = [int64]::MaxValue
    )

    if ($Value -isnot [byte] -and $Value -isnot [sbyte] -and $Value -isnot [int16] -and
        $Value -isnot [uint16] -and $Value -isnot [int32] -and $Value -isnot [uint32] -and
        $Value -isnot [int64] -and $Value -isnot [uint64]) {
        throw 'provider_qualification_state_schema_invalid'
    }
    $number = [int64]$Value
    if ($number -lt $Minimum -or $number -gt $Maximum) {
        throw 'provider_qualification_state_schema_invalid'
    }
    return $number
}

function Assert-PQStateSchemaTestHash {
    [CmdletBinding()]
    param(
        [AllowNull()]$Value,
        [switch]$Required
    )

    if ($null -eq $Value) {
        if ($Required) { throw 'provider_qualification_state_schema_invalid' }
        return
    }
    if ($Value -isnot [string] -or $Value -notmatch '^[0-9a-f]{64}$') {
        throw 'provider_qualification_state_schema_invalid'
    }
}

function Assert-PQStateSchemaTestCommandLedger {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Ledger)

    $status = [string](Get-PQStateSchemaTestMember -InputObject $Ledger -Name 'status')
    $attemptCount = Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $Ledger -Name 'attempt_count') -Minimum 0 -Maximum 1
    $fingerprint = Get-PQStateSchemaTestMember -InputObject $Ledger -Name 'command_fingerprint'
    if ($script:PQCommandStates -notcontains $status) {
        throw 'provider_qualification_state_schema_invalid'
    }
    if ($status -eq 'not_started') {
        if ($attemptCount -ne 0 -or $null -ne $fingerprint) {
            throw 'provider_qualification_state_schema_invalid'
        }
        return
    }
    if ($attemptCount -ne 1) {
        throw 'provider_qualification_state_schema_invalid'
    }
    Assert-PQStateSchemaTestHash -Value $fingerprint -Required
}

function Assert-PQStateSchemaTestContract {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$State)

    # This deliberately mirrors the state invariants exercised by 005U/U1/V,
    # without loading a schema file or invoking Python.  It is not a production
    # replacement for the JSON Schema gate.
    $required = @(
        'schema_version', 'task_id', 'qualification_profile', 'run_id', 'revision',
        'state', 'stage', 'desktop_quiescent', 'desktop_seen_before_quiescence',
        'worker_generation', 'worker_launch_count', 'supervisor_pid', 'worker_pid',
        'supervisor_token_sha256', 'worker_token_sha256', 'lease_id', 'lease_expires_utc', 'heartbeat_sequence', 'last_checkpoint',
        'cache_mutation_started', 'rollback_required', 'cache_strategy',
        'original_cache_sha256', 'active_cache_sha256', 'source_freeze_sha256',
        'cache_backup_sha256', 'quarantine_cache_sha256', 'raw_cleanup_verified', 'review_result_sha256',
        'prelaunch_review_result_sha256', 'final_review_result_sha256',
        'smoke', 'acceptance', 'artifacts', 'error'
    )
    foreach ($name in $required) {
        $null = Get-PQStateSchemaTestMember -InputObject $State -Name $name
    }

    if ([string](Get-PQStateSchemaTestMember -InputObject $State -Name 'schema_version') -ne '1.1') {
        throw 'provider_qualification_state_schema_invalid'
    }
    $profile = [string](Get-PQStateSchemaTestMember -InputObject $State -Name 'qualification_profile')
    $taskId = [string](Get-PQStateSchemaTestMember -InputObject $State -Name 'task_id')
    $profileTasks = @{
        '005S' = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
        '005T' = 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
        '005V' = 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V'
    }
    if (-not $profileTasks.ContainsKey($profile) -or $profileTasks[$profile] -ne $taskId) {
        throw 'provider_qualification_state_schema_invalid'
    }
    $runId = Get-PQStateSchemaTestMember -InputObject $State -Name 'run_id'
    if ($runId -isnot [string] -or $runId -notmatch '^session_[A-Za-z0-9_.-]+$') {
        throw 'provider_qualification_state_schema_invalid'
    }
    Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'revision') -Minimum 1 | Out-Null

    $states = @(
        'prepared', 'prelaunch_validated', 'source_frozen', 'supervisor_started', 'worker_started', 'supervisor_ready', 'worker_armed',
        'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up', 'cache_quarantined', 'smoke_started',
        'smoke_passed', 'acceptance_started', 'acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed',
        'rehearsal_completed', 'failed', 'blocked'
    )
    $currentState = [string](Get-PQStateSchemaTestMember -InputObject $State -Name 'state')
    if ($states -notcontains $currentState) {
        throw 'provider_qualification_state_schema_invalid'
    }
    $stage = Get-PQStateSchemaTestMember -InputObject $State -Name 'stage'
    $checkpoint = Get-PQStateSchemaTestMember -InputObject $State -Name 'last_checkpoint'
    if ($stage -isnot [string] -or $stage -notmatch '^[a-z0-9_]{1,64}$' -or
        $checkpoint -isnot [string] -or $checkpoint -notmatch '^[a-z_]{1,64}$') {
        throw 'provider_qualification_state_schema_invalid'
    }

    foreach ($name in @('desktop_quiescent', 'desktop_seen_before_quiescence', 'cache_mutation_started', 'rollback_required', 'raw_cleanup_verified')) {
        if ((Get-PQStateSchemaTestMember -InputObject $State -Name $name) -isnot [bool]) {
            throw 'provider_qualification_state_schema_invalid'
        }
    }
    $workerGeneration = Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'worker_generation') -Minimum 0 -Maximum 3
    $workerLaunchCount = Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'worker_launch_count') -Minimum 0 -Maximum 3
    $supervisorPid = Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'supervisor_pid') -Minimum 0
    $workerPid = Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'worker_pid') -Minimum 0
    Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'heartbeat_sequence') -Minimum 0 | Out-Null
    if (($profile -eq '005T' -or $profile -eq '005V') -and ($workerGeneration -gt 1 -or $workerLaunchCount -gt 1)) {
        throw 'provider_qualification_state_schema_invalid'
    }
    if (@('none', 'backup_only', 'quarantine_rebuild') -notcontains [string](Get-PQStateSchemaTestMember -InputObject $State -Name 'cache_strategy')) {
        throw 'provider_qualification_state_schema_invalid'
    }
    foreach ($name in @('original_cache_sha256', 'active_cache_sha256', 'source_freeze_sha256', 'cache_backup_sha256', 'quarantine_cache_sha256', 'review_result_sha256', 'prelaunch_review_result_sha256', 'final_review_result_sha256', 'supervisor_token_sha256', 'worker_token_sha256')) {
        Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name $name)
    }

    $leaseId = Get-PQStateSchemaTestMember -InputObject $State -Name 'lease_id'
    $leaseExpiry = Get-PQStateSchemaTestMember -InputObject $State -Name 'lease_expires_utc'
    if ($null -ne $leaseId -and ($leaseId -isnot [string] -or $leaseId -notmatch '^[a-f0-9]{32}$')) {
        throw 'provider_qualification_state_schema_invalid'
    }
    if ($null -ne $leaseExpiry -and ($leaseExpiry -isnot [string] -or $leaseExpiry -notmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?Z$')) {
        throw 'provider_qualification_state_schema_invalid'
    }
    Assert-PQStateSchemaTestCommandLedger -Ledger (Get-PQStateSchemaTestMember -InputObject $State -Name 'smoke')
    Assert-PQStateSchemaTestCommandLedger -Ledger (Get-PQStateSchemaTestMember -InputObject $State -Name 'acceptance')

    $artifacts = @(Get-PQStateSchemaTestMember -InputObject $State -Name 'artifacts')
    if ($artifacts -is [string] -or $artifacts -isnot [System.Collections.IEnumerable]) {
        throw 'provider_qualification_state_schema_invalid'
    }
    foreach ($artifact in @($artifacts)) {
        $kind = Get-PQStateSchemaTestMember -InputObject $artifact -Name 'kind'
        if ($kind -isnot [string] -or $kind.Length -lt 1 -or $kind.Length -gt 96) {
            throw 'provider_qualification_state_schema_invalid'
        }
        Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $artifact -Name 'sha256') -Required
        Assert-PQStateSchemaTestInteger -Value (Get-PQStateSchemaTestMember -InputObject $artifact -Name 'size_bytes') -Minimum 0 | Out-Null
    }

    $error = Get-PQStateSchemaTestMember -InputObject $State -Name 'error'
    if (@('failed', 'blocked') -contains $currentState) {
        if ($null -eq $error) { throw 'provider_qualification_state_schema_invalid' }
        foreach ($name in @('code', 'message', 'context')) { $null = Get-PQStateSchemaTestMember -InputObject $error -Name $name }
        $context = Get-PQStateSchemaTestMember -InputObject $error -Name 'context'
        foreach ($name in @('stage', 'reason')) { $null = Get-PQStateSchemaTestMember -InputObject $context -Name $name }
    } elseif ($null -ne $error) {
        throw 'provider_qualification_state_schema_invalid'
    }

    $sourceFrozenStates = @('source_frozen', 'supervisor_started', 'worker_started', 'supervisor_ready', 'worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up', 'cache_quarantined', 'smoke_started', 'smoke_passed', 'acceptance_started', 'acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed')
    if ($sourceFrozenStates -contains $currentState) {
        Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'source_freeze_sha256') -Required
    }
    if ($currentState -eq 'supervisor_started') {
        if ($supervisorPid -lt 1) { throw 'provider_qualification_state_schema_invalid' }
        Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'supervisor_token_sha256') -Required
    }
    if ($currentState -eq 'worker_started') {
        if ($workerGeneration -lt 1 -or $workerLaunchCount -lt 1 -or $workerGeneration -ne $workerLaunchCount -or $supervisorPid -lt 1 -or $workerPid -ne 0) {
            throw 'provider_qualification_state_schema_invalid'
        }
        foreach ($name in @('supervisor_token_sha256', 'worker_token_sha256')) {
            Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name $name) -Required
        }
        if ($null -eq $leaseId -or $null -eq $leaseExpiry) { throw 'provider_qualification_state_schema_invalid' }
    }
    $workerReadyStates = @('supervisor_ready', 'worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up', 'cache_quarantined', 'smoke_started', 'smoke_passed', 'acceptance_started', 'acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed')
    if ($workerReadyStates -contains $currentState) {
        if ($workerGeneration -lt 1 -or $workerLaunchCount -lt 1 -or $supervisorPid -lt 1 -or $workerPid -lt 1) {
            throw 'provider_qualification_state_schema_invalid'
        }
        foreach ($name in @('supervisor_token_sha256', 'worker_token_sha256')) {
            Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name $name) -Required
        }
        if ($null -eq $leaseId -or $null -eq $leaseExpiry) { throw 'provider_qualification_state_schema_invalid' }
    }
    if (@('smoke_started', 'smoke_passed', 'acceptance_started', 'acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed') -contains $currentState -and
        [int](Get-PQStateSchemaTestMember -InputObject (Get-PQStateSchemaTestMember -InputObject $State -Name 'smoke') -Name 'attempt_count') -ne 1) {
        throw 'provider_qualification_state_schema_invalid'
    }
    if (@('smoke_passed', 'acceptance_started', 'acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed') -contains $currentState -and
        [string](Get-PQStateSchemaTestMember -InputObject (Get-PQStateSchemaTestMember -InputObject $State -Name 'smoke') -Name 'status') -ne 'succeeded') {
        throw 'provider_qualification_state_schema_invalid'
    }
    if (@('acceptance_started', 'acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed') -contains $currentState -and
        [int](Get-PQStateSchemaTestMember -InputObject (Get-PQStateSchemaTestMember -InputObject $State -Name 'acceptance') -Name 'attempt_count') -ne 1) {
        throw 'provider_qualification_state_schema_invalid'
    }
    if (@('acceptance_passed', 'verification_passed', 'complete_pending_review', 'completed') -contains $currentState -and
        [string](Get-PQStateSchemaTestMember -InputObject (Get-PQStateSchemaTestMember -InputObject $State -Name 'acceptance') -Name 'status') -ne 'succeeded') {
        throw 'provider_qualification_state_schema_invalid'
    }
    if (@('complete_pending_review', 'completed') -contains $currentState) {
        Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'prelaunch_review_result_sha256') -Required
    }
    if ($currentState -eq 'completed') {
        Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name 'final_review_result_sha256') -Required
    }
    if ($currentState -eq 'rehearsal_completed') {
        if (-not [bool](Get-PQStateSchemaTestMember -InputObject $State -Name 'desktop_quiescent') -or
            -not [bool](Get-PQStateSchemaTestMember -InputObject $State -Name 'desktop_seen_before_quiescence') -or
            [int](Get-PQStateSchemaTestMember -InputObject $State -Name 'heartbeat_sequence') -lt 3 -or
            $workerGeneration -lt 1 -or $workerLaunchCount -lt 1 -or $supervisorPid -lt 1 -or $workerPid -lt 1) {
            throw 'provider_qualification_state_schema_invalid'
        }
        foreach ($name in @('source_freeze_sha256', 'supervisor_token_sha256', 'worker_token_sha256')) {
            Assert-PQStateSchemaTestHash -Value (Get-PQStateSchemaTestMember -InputObject $State -Name $name) -Required
        }
        if ($null -eq $leaseId -or $null -eq $leaseExpiry) { throw 'provider_qualification_state_schema_invalid' }
    }
    return $true
}

function Assert-PQStateSchema {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$State)

    # This validates the *in-memory* candidate before an atomic state write.
    # Nothing from the document is emitted: a failed validator is deliberately
    # collapsed to a stable control-plane error.  Test suites mock this private
    # call in Pester; production has no runtime switch that can replace it.
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $schemaPath = Join-Path $repoRoot 'schemas\ops\provider_qualification_run.schema.json'
    $python = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $schemaPath -PathType Leaf) -or -not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw 'provider_qualification_state_schema_validator_unavailable'
    }

    $payload = $State | ConvertTo-Json -Depth 20 -Compress
    # Windows PowerShell 5.1 may prepend a UTF-8 BOM when piping a string to
    # a native process. Decode the validator stdin as utf-8-sig so the schema
    # gate validates the document rather than failing before JSON parsing.
    $code = 'import json,sys,jsonschema; schema=json.load(open(sys.argv[1],encoding=''utf-8-sig'')); document=json.loads(sys.stdin.buffer.read().decode(''utf-8-sig'')); jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(document)'
    $priorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $null = $payload | & $python -c $code $schemaPath 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw 'provider_qualification_state_schema_invalid'
        }
    } finally {
        $ErrorActionPreference = $priorPreference
    }
}

function Assert-PQFinalReviewSchema {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Review)

    # 005V finalization accepts only a schema-valid, hash-bound reviewer
    # record. Validation stays local and emits no reviewer content.
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $schemaPath = Join-Path $repoRoot 'schemas\ops\provider_qualification_final_review.schema.json'
    $python = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $schemaPath -PathType Leaf) -or -not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw 'provider_qualification_final_review_schema_validator_unavailable'
    }

    $payload = $Review | ConvertTo-Json -Depth 20 -Compress
    $code = 'import json,sys,jsonschema; schema=json.load(open(sys.argv[1],encoding=''utf-8-sig'')); document=json.loads(sys.stdin.buffer.read().decode(''utf-8-sig'')); jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(document)'
    $priorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $null = $payload | & $python -c $code $schemaPath 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw 'provider_qualification_final_review_schema_invalid'
        }
    } finally {
        $ErrorActionPreference = $priorPreference
    }
}

function Get-PQCanonicalBoundarySha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Boundary)

    # Keep the boundary digest independent of JSON parser/property-order
    # differences.  This is the only representation final review evidence may
    # use when it does not point to the separately bound evidence file.
    $required = @('branch', 'head', 'index_empty', 'protected_dirty_sha256')
    $boundaryNames = if ($Boundary -is [System.Collections.IDictionary]) {
        @($Boundary.Keys | ForEach-Object { [string]$_ })
    } elseif ($null -ne $Boundary) {
        @($Boundary.PSObject.Properties.Name)
    } else {
        @()
    }
    if ($null -eq $Boundary -or $boundaryNames.Count -ne $required.Count) {
        throw 'provider_qualification_final_review_boundary_invalid'
    }
    foreach ($name in $required) {
        if ($boundaryNames -notcontains $name) {
            throw 'provider_qualification_final_review_boundary_invalid'
        }
    }
    $branch = if ($Boundary -is [System.Collections.IDictionary]) { [string]$Boundary['branch'] } else { [string]$Boundary.PSObject.Properties['branch'].Value }
    $head = if ($Boundary -is [System.Collections.IDictionary]) { [string]$Boundary['head'] } else { [string]$Boundary.PSObject.Properties['head'].Value }
    $indexEmpty = if ($Boundary -is [System.Collections.IDictionary]) { $Boundary['index_empty'] } else { $Boundary.PSObject.Properties['index_empty'].Value }
    $dirty = if ($Boundary -is [System.Collections.IDictionary]) { $Boundary['protected_dirty_sha256'] } else { $Boundary.PSObject.Properties['protected_dirty_sha256'].Value }
    if ([string]::IsNullOrWhiteSpace($branch) -or
        [string]::IsNullOrWhiteSpace($head) -or
        $indexEmpty -isnot [bool]) {
        throw 'provider_qualification_final_review_boundary_invalid'
    }

    $dirtyRequired = @(
        'PROJECT_STATUS.yaml',
        'reports/P0_ACCEPTANCE_MATRIX_V2.yaml',
        'scripts/analysis_request.py',
        'scripts/analyzer_mcp.py',
        'scripts/mcp_ingest_attachment.py',
        'scripts/media_action_ticket.py'
    )
    $dirtyNames = if ($dirty -is [System.Collections.IDictionary]) {
        @($dirty.Keys | ForEach-Object { [string]$_ })
    } elseif ($null -ne $dirty) {
        @($dirty.PSObject.Properties.Name)
    } else {
        @()
    }
    if ($dirtyNames.Count -ne $dirtyRequired.Count) {
        throw 'provider_qualification_final_review_boundary_invalid'
    }
    $canonicalDirty = [ordered]@{}
    foreach ($name in ($dirtyRequired | Sort-Object)) {
        if ($dirtyNames -notcontains $name) {
            throw 'provider_qualification_final_review_boundary_invalid'
        }
        $value = if ($dirty -is [System.Collections.IDictionary]) { [string]$dirty[$name] } else { [string]$dirty.PSObject.Properties[$name].Value }
        if ($value -notmatch '^[0-9a-f]{64}$') {
            throw 'provider_qualification_final_review_boundary_invalid'
        }
        $canonicalDirty[$name] = $value
    }

    $canonicalBoundary = [ordered]@{
        branch = $branch
        head = $head
        index_empty = [bool]$indexEmpty
        protected_dirty_sha256 = $canonicalDirty
    }
    $canonical = $canonicalBoundary | ConvertTo-Json -Depth 4 -Compress
    $digestBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($canonical))
    return ([System.BitConverter]::ToString($digestBytes)).Replace('-', '').ToLowerInvariant()
}

function Assert-PQFinalReviewBindings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Review,
        [Parameter(Mandatory)]$Manifest,
        [Parameter(Mandatory)][string]$RunRoot
    )

    # This function intentionally returns only binding metadata and throws
    # short codes.  Independent-review and boundary-evidence contents are
    # never emitted through the qualification CLI or its state files.
    $reviewReportLeaf = 'INDEPENDENT_FINAL_REVIEW_REPORT.json'
    $boundaryEvidenceLeaf = 'FINAL_REVIEW_BOUNDARY_EVIDENCE.json'
    $manifestBoundaryHash = Get-PQCanonicalBoundarySha256 -Boundary $Manifest.boundary
    $reviewBoundaryHash = [string]$Review.protected_boundary_sha256
    $hasBoundaryEvidence = $Review.PSObject.Properties.Name -contains 'protected_boundary_evidence_file'

    # The reviewer record carries its own full boundary snapshot.  Bind it to
    # the manifest before accepting either the canonical digest or a separate
    # boundary-evidence file, so a syntactically valid but substituted protected
    # dirty-file hash cannot finalize the run.
    if ($null -eq $Review.boundary -or
        (Get-PQCanonicalBoundarySha256 -Boundary $Review.boundary) -ne $manifestBoundaryHash) {
        throw 'provider_qualification_final_review_boundary_not_bound'
    }

    if ($hasBoundaryEvidence) {
        if ([string]$Review.protected_boundary_evidence_file -ne $boundaryEvidenceLeaf) {
            throw 'provider_qualification_final_review_boundary_evidence_invalid'
        }
        $boundaryEvidencePath = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath $boundaryEvidenceLeaf
        if (-not (Test-Path -LiteralPath $boundaryEvidencePath -PathType Leaf)) {
            throw 'provider_qualification_final_review_boundary_evidence_missing'
        }
        Test-PQNoReparseComponents -Path $boundaryEvidencePath | Out-Null
        if ($reviewBoundaryHash -ne (Get-PQSha256 -Path $boundaryEvidencePath)) {
            throw 'provider_qualification_final_review_protected_boundary_not_bound'
        }
        try {
            $boundaryEvidence = Read-PQJson -Path $boundaryEvidencePath
        } catch {
            throw 'provider_qualification_final_review_boundary_evidence_invalid'
        }
        if ([string]$boundaryEvidence.task_id -ne [string]$Manifest.task_id -or
            [string]$boundaryEvidence.profile -ne [string]$Manifest.qualification_profile -or
            [string]$boundaryEvidence.run_id -ne [string]$Manifest.run_id -or
            $null -eq $boundaryEvidence.boundary -or
            (Get-PQCanonicalBoundarySha256 -Boundary $boundaryEvidence.boundary) -ne $manifestBoundaryHash) {
            throw 'provider_qualification_final_review_boundary_evidence_invalid'
        }
        $boundaryBinding = 'evidence_file'
    } else {
        if ($reviewBoundaryHash -ne $manifestBoundaryHash) {
            throw 'provider_qualification_final_review_protected_boundary_not_bound'
        }
        $boundaryBinding = 'manifest_canonical'
    }

    if ([string]$Review.review_report_file -ne $reviewReportLeaf) {
        throw 'provider_qualification_final_review_report_invalid'
    }
    $reviewReportPath = Resolve-PQRunChild -RunRoot $RunRoot -RelativePath $reviewReportLeaf
    if (-not (Test-Path -LiteralPath $reviewReportPath -PathType Leaf)) {
        throw 'provider_qualification_final_review_report_missing'
    }
    Test-PQNoReparseComponents -Path $reviewReportPath | Out-Null
    if ([string]$Review.review_report_sha256 -ne (Get-PQSha256 -Path $reviewReportPath)) {
        throw 'provider_qualification_final_review_report_not_bound'
    }
    try {
        $reviewReport = Read-PQJson -Path $reviewReportPath
    } catch {
        throw 'provider_qualification_final_review_report_invalid'
    }
    if ([string]$reviewReport.task_id -ne [string]$Manifest.task_id -or
        [string]$reviewReport.profile -ne [string]$Manifest.qualification_profile -or
        [string]$reviewReport.run_id -ne [string]$Manifest.run_id) {
        throw 'provider_qualification_final_review_report_not_bound'
    }

    return [ordered]@{
        protected_boundary_binding = $boundaryBinding
        independent_review_report_bound = $true
    }
}

function Assert-PQTransition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$NewState
    )

    $version = [string]$State.schema_version
    if (-not $script:PQTransitions.ContainsKey($version)) {
        throw 'provider_qualification_schema_version_unknown'
    }
    $current = [string]$State.state
    if ($script:PQTerminalStates -contains $current) {
        throw 'provider_qualification_terminal_state_immutable'
    }
    if (-not $script:PQTransitions[$version].ContainsKey($current) -or
        -not ($script:PQTransitions[$version][$current] -contains $NewState)) {
        throw 'provider_qualification_state_transition_invalid'
    }
}

function Assert-PQMonotonicPatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][hashtable]$Patch
    )

    if ([string]$State.schema_version -eq '1.0') {
        foreach ($key in $Patch.Keys) {
            if (@('desktop_quiescent', 'original_cache_sha256', 'active_cache_sha256', 'smoke_attempted', 'acceptance_attempted', 'artifacts') -notcontains $key) {
                throw 'provider_qualification_patch_field_rejected'
            }
        }
        foreach ($field in @('smoke_attempted', 'acceptance_attempted', 'desktop_quiescent')) {
            if ($Patch.ContainsKey($field) -and [bool]$State.$field -and -not [bool]$Patch[$field]) {
                throw 'provider_qualification_boolean_cannot_reset'
            }
        }
        return
    }

    $allowed = @(
        'desktop_quiescent', 'desktop_seen_before_quiescence', 'worker_generation', 'worker_launch_count',
        'supervisor_pid', 'worker_pid', 'supervisor_token_sha256', 'worker_token_sha256', 'lease_id',
        'lease_expires_utc', 'heartbeat_sequence', 'cache_mutation_started', 'rollback_required',
        'cache_strategy', 'original_cache_sha256', 'active_cache_sha256', 'source_freeze_sha256',
         'cache_backup_sha256', 'quarantine_cache_sha256', 'raw_cleanup_verified', 'review_result_sha256',
         'prelaunch_review_result_sha256', 'final_review_result_sha256',
        'smoke', 'acceptance', 'artifacts'
    )
    foreach ($key in $Patch.Keys) {
        if ($allowed -notcontains $key) {
            throw 'provider_qualification_patch_field_rejected'
        }
    }
    foreach ($field in @('source_freeze_sha256', 'supervisor_token_sha256', 'original_cache_sha256', 'cache_backup_sha256', 'review_result_sha256', 'prelaunch_review_result_sha256', 'final_review_result_sha256')) {
        if ($Patch.ContainsKey($field) -and
            -not [string]::IsNullOrWhiteSpace([string]$State.$field) -and
            [string]$Patch[$field] -ne [string]$State.$field) {
            throw 'provider_qualification_write_once_changed'
        }
    }
    foreach ($field in @('worker_generation', 'worker_launch_count', 'heartbeat_sequence')) {
        if ($Patch.ContainsKey($field) -and [int]$Patch[$field] -lt [int]$State.$field) {
            throw 'provider_qualification_monotonic_field_regressed'
        }
    }
    if ($Patch.ContainsKey('worker_generation') -or $Patch.ContainsKey('worker_launch_count')) {
        $nextGeneration = if ($Patch.ContainsKey('worker_generation')) { [int]$Patch.worker_generation } else { [int]$State.worker_generation }
        $nextLaunchCount = if ($Patch.ContainsKey('worker_launch_count')) { [int]$Patch.worker_launch_count } else { [int]$State.worker_launch_count }
        $stateProfile = Get-PQProfile -QualificationProfile ([string]$State.qualification_profile)
        if ([string]$stateProfile.task_id -ne [string]$State.task_id) {
            throw 'provider_qualification_state_identity_mismatch'
        }
        $maxGeneration = [int]$stateProfile.max_worker_generations
        if ($nextGeneration -ne $nextLaunchCount -or $nextGeneration -gt $maxGeneration) {
            throw 'provider_qualification_worker_generation_invalid'
        }
        if ($nextGeneration -gt ([int]$State.worker_generation + 1)) {
            throw 'provider_qualification_worker_generation_skipped'
        }
    }
    foreach ($field in @('lease_id', 'worker_token_sha256')) {
        if ($Patch.ContainsKey($field) -and -not [string]::IsNullOrWhiteSpace([string]$State.$field) -and
            [string]$Patch[$field] -ne [string]$State.$field -and
            (-not $Patch.ContainsKey('worker_generation') -or [int]$Patch.worker_generation -ne [int]$State.worker_generation + 1)) {
            throw 'provider_qualification_lease_replacement_rejected'
        }
    }
    if ($Patch.ContainsKey('lease_expires_utc')) {
        if ([string]::IsNullOrWhiteSpace([string]$Patch.lease_expires_utc)) {
            throw 'provider_qualification_lease_invalid'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$State.lease_expires_utc)) {
            try {
                $oldExpiry = [DateTime]::Parse([string]$State.lease_expires_utc).ToUniversalTime()
                $newExpiry = [DateTime]::Parse([string]$Patch.lease_expires_utc).ToUniversalTime()
                if ($newExpiry -lt $oldExpiry) { throw 'provider_qualification_lease_regressed' }
            } catch {
                if ($_.Exception.Message -eq 'provider_qualification_lease_regressed') { throw }
                throw 'provider_qualification_lease_invalid'
            }
        }
    }
    if ($Patch.ContainsKey('supervisor_pid') -and [int]$State.supervisor_pid -ne 0 -and [int]$Patch.supervisor_pid -ne [int]$State.supervisor_pid) {
        throw 'provider_qualification_supervisor_pid_replacement_rejected'
    }
    if ($Patch.ContainsKey('worker_pid') -and [int]$State.worker_pid -ne 0 -and [int]$Patch.worker_pid -ne [int]$State.worker_pid -and
        (-not $Patch.ContainsKey('worker_generation') -or [int]$Patch.worker_generation -ne [int]$State.worker_generation + 1)) {
        throw 'provider_qualification_worker_pid_replacement_rejected'
    }
    foreach ($field in @('cache_mutation_started', 'rollback_required', 'desktop_quiescent', 'desktop_seen_before_quiescence', 'raw_cleanup_verified')) {
        if ($Patch.ContainsKey($field) -and [bool]$State.$field -and -not [bool]$Patch[$field]) {
            throw 'provider_qualification_boolean_cannot_reset'
        }
    }
    if ($Patch.ContainsKey('cache_strategy') -and [string]$State.cache_strategy -ne 'none' -and
        [string]$Patch.cache_strategy -ne [string]$State.cache_strategy) {
        throw 'provider_qualification_cache_strategy_write_once'
    }
    foreach ($ledgerName in @('smoke', 'acceptance')) {
        if ($Patch.ContainsKey($ledgerName)) {
            $old = $State.$ledgerName
            $next = $Patch[$ledgerName]
            if ([int]$next.attempt_count -lt [int]$old.attempt_count -or [int]$next.attempt_count -gt 1) {
                throw 'provider_qualification_command_attempt_invalid'
            }
            if ([string]$old.status -ne 'not_started' -and [string]$next.status -eq 'not_started') {
                throw 'provider_qualification_command_cannot_reset'
            }
            if ([string]$old.status -ne 'not_started' -and
                [string]$next.command_fingerprint -ne [string]$old.command_fingerprint) {
                throw 'provider_qualification_command_fingerprint_changed'
            }
            if ([int]$old.attempt_count -eq 1 -and [int]$next.attempt_count -ne 1) {
                throw 'provider_qualification_command_cannot_reset'
            }
            $allowedLedgerTransitions = @{
                not_started = @('not_started', 'claimed')
                claimed = @('claimed', 'succeeded', 'failed', 'outcome_unknown')
                succeeded = @('succeeded')
                failed = @('failed')
                outcome_unknown = @('outcome_unknown')
            }
            if (-not $allowedLedgerTransitions.ContainsKey([string]$old.status) -or
                -not ($allowedLedgerTransitions[[string]$old.status] -contains [string]$next.status)) {
                throw 'provider_qualification_command_state_transition_invalid'
            }
            if ([string]$next.status -ne 'not_started' -and [string]$next.command_fingerprint -notmatch '^[0-9a-f]{64}$') {
                throw 'provider_qualification_command_fingerprint_invalid'
            }
        }
    }
}

function Move-PQRunState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][string]$NewState,
        [Parameter(Mandatory)][string]$Stage,
        [hashtable]$Patch = @{},
        [object]$ErrorObject = $null
    )

    return Invoke-PQStateLock -StatePath $StatePath -Action {
        $current = Get-PQCurrentStateForMutation -ExpectedState $State -StatePath $StatePath
        Assert-PQTransition -State $current -NewState $NewState
        Assert-PQMonotonicPatch -State $current -Patch $Patch
        if (($NewState -eq 'failed' -or $NewState -eq 'blocked') -and $null -eq $ErrorObject) {
            throw 'provider_qualification_terminal_error_required'
        }
        if (($NewState -ne 'failed' -and $NewState -ne 'blocked') -and $null -ne $ErrorObject) {
            throw 'provider_qualification_nonterminal_error_rejected'
        }

        $next = [ordered]@{}
        foreach ($property in $current.PSObject.Properties) {
            $next[$property.Name] = $property.Value
        }
        foreach ($key in $Patch.Keys) {
            $next[$key] = $Patch[$key]
        }
        $next.state = $NewState
        $next.stage = $Stage
        $next.revision = [int]$current.revision + 1
        if ($next.Contains('last_checkpoint')) {
            $next.last_checkpoint = $NewState
        }
        if ($null -ne $ErrorObject) {
            $next.error = $ErrorObject
        } else {
            $next.error = $null
        }
        Assert-PQStateSchema -State ([pscustomobject]$next)
        Write-PQJsonAtomic -Path $StatePath -Value $next
        return [pscustomobject]$next
    }
}

function Update-PQRunState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [hashtable]$Patch = @{},
        [string]$Stage = $null
    )

    return Invoke-PQStateLock -StatePath $StatePath -Action {
        $current = Get-PQCurrentStateForMutation -ExpectedState $State -StatePath $StatePath
        if ($script:PQTerminalStates -contains [string]$current.state) {
            throw 'provider_qualification_terminal_state_immutable'
        }
        Assert-PQMonotonicPatch -State $current -Patch $Patch
        $next = [ordered]@{}
        foreach ($property in $current.PSObject.Properties) {
            $next[$property.Name] = $property.Value
        }
        foreach ($key in $Patch.Keys) {
            $next[$key] = $Patch[$key]
        }
        if (-not [string]::IsNullOrWhiteSpace($Stage)) {
            $next.stage = $Stage
        }
        $next.revision = [int]$current.revision + 1
        Assert-PQStateSchema -State ([pscustomobject]$next)
        Write-PQJsonAtomic -Path $StatePath -Value $next
        return [pscustomobject]$next
    }
}

function Invoke-PQWorkerLaunchTransaction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][string]$TokenFile,
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][scriptblock]$WriteToken,
        [Parameter(Mandatory)][scriptblock]$StartProcess,
        [Parameter(Mandatory)][scriptblock]$WritePidFile,
        [Parameter(Mandatory)][scriptblock]$PromoteReady,
        [Parameter(Mandatory)][scriptblock]$RemoveToken,
        [Parameter(Mandatory)][scriptblock]$RemovePidFile
    )

    # Shared launch transaction. Production supplies real callbacks; tests use
    # TestDrive callbacks. This keeps pre-ready failures executable without
    # starting a Worker or touching Provider environment files.
    $current = $State
    $worker = $null
    $workerPid = 0
    $failureReason = 'worker_token_write_failed'
    try {
        & $WriteToken $TokenFile $Token
        $failureReason = 'worker_start_failed'
        $worker = & $StartProcess
        if ($null -eq $worker) { $failureReason = 'worker_pid_invalid'; throw 'provider_qualification_worker_pid_invalid' }
        try { $workerPid = [int]$worker.Id } catch { $failureReason = 'worker_pid_invalid'; throw 'provider_qualification_worker_pid_invalid' }
        if ($workerPid -lt 1) { $failureReason = 'worker_pid_invalid'; throw 'provider_qualification_worker_pid_invalid' }
        $failureReason = 'worker_pid_file_write_failed'
        & $WritePidFile $workerPid
        $failureReason = 'supervisor_ready_persist_failed'
        # worker_started is a reservation and is schema-bound to PID zero.
        # Publish a positive PID only in the atomic promotion to
        # supervisor_ready, never as a separate invalid intermediate write.
        $current = & $PromoteReady $current $StatePath $workerPid
        return [pscustomobject]@{ succeeded = $true; state = $current; worker = $worker; worker_pid = $workerPid; failure_reason = $null }
    } catch {
        try { & $RemoveToken $TokenFile } catch { $failureReason = 'worker_token_cleanup_failed' }
        try { & $RemovePidFile $workerPid } catch { $failureReason = 'worker_pid_cleanup_failed' }
        return [pscustomobject]@{ succeeded = $false; state = $current; worker = $worker; worker_pid = $workerPid; failure_reason = $failureReason }
    }
}

function Publish-PQWorkerReadyMarker {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][int]$WorkerPid,
        [Parameter(Mandatory)][scriptblock]$WriteMarker
    )

    # This is deliberately a small, production-used ownership proof.  A
    # Worker cannot attest ready until the Supervisor has durably persisted its
    # PID and moved the state to supervisor_ready.
    if ([string]$State.state -ne 'supervisor_ready' -or $WorkerPid -lt 1 -or [int]$State.worker_pid -ne $WorkerPid) {
        throw 'provider_qualification_worker_pid_mismatch'
    }
    $generation = [int]$State.worker_generation
    $lease = [string]$State.lease_id
    if ($generation -lt 1 -or $lease -notmatch '^[0-9a-f]{32}$') {
        throw 'provider_qualification_worker_lease_missing'
    }
    $content = 'worker_ready:' + $RunId + ':' + $generation + ':' + $lease + ':' + $WorkerPid
    & $WriteMarker $RunRoot 'WORKER_READY.txt' $content | Out-Null
    return [pscustomobject]@{
        name = 'WORKER_READY.txt'
        content = $content
        worker_pid = $WorkerPid
    }
}

function Invoke-PQSupervisorWorkerStartup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][string]$TokenFile,
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][string]$RunRoot,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][int]$SupervisorPid,
        [Parameter(Mandatory)][scriptblock]$WriteToken,
        [Parameter(Mandatory)][scriptblock]$StartProcess,
        [Parameter(Mandatory)][scriptblock]$WritePidFile,
        [Parameter(Mandatory)][scriptblock]$PromoteReady,
        [Parameter(Mandatory)][scriptblock]$RemoveToken,
        [Parameter(Mandatory)][scriptblock]$RemovePidFile,
        [Parameter(Mandatory)][scriptblock]$WriteMarker,
        [Parameter(Mandatory)][scriptblock]$WaitForWorkerReady,
        [Parameter(Mandatory)][scriptblock]$ArmWorker,
        [Parameter(Mandatory)][scriptblock]$BlockState
    )

    # The pre-ready transaction and the four durable handoff markers form one
    # injectable production seam.  Tests invoke this exact function with
    # TestDrive callbacks; Invoke-PQSupervisor supplies the live callbacks.
    $transaction = Invoke-PQWorkerLaunchTransaction -State $State -StatePath $StatePath -TokenFile $TokenFile -Token $Token `
        -WriteToken $WriteToken -StartProcess $StartProcess -WritePidFile $WritePidFile `
        -PromoteReady $PromoteReady -RemoveToken $RemoveToken -RemovePidFile $RemovePidFile
    if (-not [bool]$transaction.succeeded) {
        $current = $transaction.state
        $reason = [string]$transaction.failure_reason
        $persisted = $false
        try {
            if (@('completed', 'failed', 'blocked') -notcontains [string]$current.state) {
                $error = Get-PQSanitizedError -Code 'WORKER_CONTRACT_FAILED' -Stage 'worker_launch' -Reason $reason
                $current = & $BlockState $current $StatePath $error 'worker_launch'
            }
            $persisted = ([string]$current.state -eq 'blocked')
        } catch {
            $persisted = $false
        }
        if (-not $persisted) { $reason = 'blocked_state_persist_failed' }
        return [pscustomobject]@{
            succeeded = $false
            state = $current
            worker = $transaction.worker
            worker_pid = [int]$transaction.worker_pid
            failure_reason = $reason
            blocked_persisted = $persisted
        }
    }

    $current = $transaction.state
    $worker = $transaction.worker
    $workerPid = [int]$transaction.worker_pid
    $generation = [int]$current.worker_generation
    $lease = [string]$current.lease_id
    $failureCode = 'WORKER_CONTRACT_FAILED'
    $failureReason = 'supervisor_ready_marker_write_failed'
    $failureStage = 'supervisor'
    try {
        & $WriteMarker $RunRoot 'SUPERVISOR_READY.txt' ('supervisor_ready:' + $RunId) | Out-Null

        $failureReason = 'worker_ready_wait_failed'
        $ready = & $WaitForWorkerReady $current $worker $RunRoot $RunId $generation $lease
        if ($null -eq $ready -or -not [bool]$ready.ready) {
            $candidateCode = if ($null -eq $ready) { '' } else { [string]$ready.code }
            $candidateReason = if ($null -eq $ready) { '' } else { [string]$ready.reason }
            if ($candidateCode -in @('BLOCKED_DETACHED_WORKER_DIED', 'BLOCKED_WORKER_NOT_ARMED')) {
                $failureCode = $candidateCode
            } else {
                $failureCode = 'BLOCKED_WORKER_NOT_ARMED'
            }
            if ($candidateReason -match '^[a-z0-9_]{1,96}$') {
                $failureReason = $candidateReason
            } else {
                $failureReason = 'handshake_missing'
            }
            throw 'provider_qualification_worker_ready_not_confirmed'
        }

        $failureCode = 'WORKER_CONTRACT_FAILED'
        $failureReason = 'worker_armed_persist_failed'
        $failureStage = 'worker_armed'
        $current = & $ArmWorker $current $StatePath

        $failureReason = 'live_worker_armed_marker_write_failed'
        $failureStage = 'supervisor'
        & $WriteMarker $RunRoot 'LIVE_WORKER_ARMED.txt' ('worker_armed:' + $RunId + ':' + $generation + ':' + $lease + ':' + $workerPid + ':' + $SupervisorPid) | Out-Null

        $failureReason = 'close_desktop_marker_write_failed'
        & $WriteMarker $RunRoot 'CLOSE_CODEX_DESKTOP_NOW.txt' ('close_desktop_now:' + $RunId + ':' + $generation + ':' + $lease + ':' + $workerPid + ':' + $SupervisorPid) | Out-Null

        return [pscustomobject]@{
            succeeded = $true
            state = $current
            worker = $worker
            worker_pid = $workerPid
            failure_reason = $null
            blocked_persisted = $false
        }
    } catch {
        try { & $RemoveToken $TokenFile } catch { $failureReason = 'worker_token_cleanup_failed' }
        $persisted = $false
        try {
            if (@('completed', 'failed', 'blocked') -notcontains [string]$current.state) {
                $error = Get-PQSanitizedError -Code $failureCode -Stage $failureStage -Reason $failureReason
                $current = & $BlockState $current $StatePath $error $failureStage
            }
            $persisted = ([string]$current.state -eq 'blocked')
        } catch {
            $persisted = $false
        }
        if (-not $persisted) { $failureReason = 'blocked_state_persist_failed' }
        return [pscustomobject]@{
            succeeded = $false
            state = $current
            worker = $worker
            worker_pid = $workerPid
            failure_reason = $failureReason
            blocked_persisted = $persisted
        }
    }
}

function Claim-PQCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][ValidateSet('smoke', 'acceptance')][string]$Command,
        [Parameter(Mandatory)][string]$NewState,
        [Parameter(Mandatory)][string]$Fingerprint,
        [string]$TaskId = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
    )

    $ledger = $State.$Command
    if ([string]$TaskId -ne [string]$State.task_id) {
        throw 'provider_qualification_command_task_identity_mismatch'
    }
    if ([string]$ledger.status -ne 'not_started' -or [int]$ledger.attempt_count -ne 0) {
        throw ('provider_qualification_' + $Command + '_already_claimed')
    }
    if ($Fingerprint -ne (Get-PQCommandFingerprint -Name $Command -TaskId $TaskId)) {
        throw 'provider_qualification_command_fingerprint_mismatch'
    }
    $patch = @{}
    $patch[$Command] = [ordered]@{ status = 'claimed'; attempt_count = 1; command_fingerprint = $Fingerprint }
    return Move-PQRunState -State $State -StatePath $StatePath -NewState $NewState -Stage $Command -Patch $patch
}

function Complete-PQCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][ValidateSet('smoke', 'acceptance')][string]$Command,
        [Parameter(Mandatory)][string]$NewState,
        [Parameter(Mandatory)][ValidateSet('succeeded', 'failed', 'outcome_unknown')][string]$Outcome,
        [object]$ErrorObject = $null
    )

    $ledger = $State.$Command
    if ([string]$ledger.status -ne 'claimed' -or [int]$ledger.attempt_count -ne 1) {
        throw ('provider_qualification_' + $Command + '_not_claimed')
    }
    if ([string]$ledger.command_fingerprint -ne (Get-PQCommandFingerprint -Name $Command -TaskId ([string]$State.task_id))) {
        throw 'provider_qualification_command_fingerprint_mismatch'
    }
    $patch = @{}
    $patch[$Command] = [ordered]@{ status = $Outcome; attempt_count = 1; command_fingerprint = [string]$ledger.command_fingerprint }
    if (($NewState -eq 'failed' -or $NewState -eq 'blocked') -and $null -eq $ErrorObject) {
        throw 'provider_qualification_terminal_error_required'
    }
    return Move-PQRunState -State $State -StatePath $StatePath -NewState $NewState -Stage $Command -Patch $patch -ErrorObject $ErrorObject
}

function Write-PQHeartbeat {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][int]$ProcessId,
        [string]$LeaseId = $null
    )

    if ($null -ne $State.supervisor_pid -and [int]$State.supervisor_pid -gt 0 -and
        -not (Test-PQProcessAlive -ProcessId ([int]$State.supervisor_pid))) {
        throw 'BLOCKED_SUPERVISOR_DIED'
    }

    $sequence = if ($null -eq $State.heartbeat_sequence) { 0 } else { [int]$State.heartbeat_sequence }
    $value = [ordered]@{
        schema_version = [string]$State.schema_version
        run_id = [string]$State.run_id
        state = [string]$State.state
        stage = [string]$State.stage
        worker_generation = if ($null -eq $State.worker_generation) { 0 } else { [int]$State.worker_generation }
        lease_id = $LeaseId
        process_id = $ProcessId
        heartbeat_sequence = $sequence
        utc = [DateTime]::UtcNow.ToString('o')
    }
    Write-PQJsonAtomic -Path $Path -Value $value
    return $value
}

function New-PQActiveLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ExternalRoot,
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][int]$SupervisorPid,
        [Parameter(Mandatory)][string]$SupervisorTokenHash,
        [string]$ManifestSha256 = $null,
        [string]$SourceFreezeSha256 = $null,
        [string]$PrelaunchAuditSha256 = $null,
        [string]$PrelaunchReviewerResultSha256 = $null,
        [switch]$Canary
    )

    $ExternalRoot = Assert-PQExternalRoot -Profile $Profile -ExternalRoot $ExternalRoot
    if (-not (Test-Path -LiteralPath $ExternalRoot -PathType Container)) {
        New-Item -ItemType Directory -Path $ExternalRoot -Force | Out-Null
    }
    $lockPath = Join-Path $ExternalRoot '.qualification.active.lock'
    $payload = [ordered]@{
        task_id = [string]$Profile.task_id
        qualification_profile = [string]$Profile.profile
        run_id = $RunId
        supervisor_pid = $SupervisorPid
        supervisor_token_sha256 = $SupervisorTokenHash
        manifest_sha256 = $ManifestSha256
        source_freeze_sha256 = $SourceFreezeSha256
        prelaunch_audit_sha256 = $PrelaunchAuditSha256
        prelaunch_reviewer_result_sha256 = $PrelaunchReviewerResultSha256
        canary = [bool]$Canary
        created_utc = [DateTime]::UtcNow.ToString('o')
    } | ConvertTo-Json -Depth 4
    try {
        $stream = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    } catch {
        throw 'provider_qualification_active_run_exists'
    }
    $writer = $null
    try {
        $writer = New-Object System.IO.StreamWriter($stream, [System.Text.Encoding]::UTF8)
        $writer.Write($payload)
        $writer.Flush()
        $stream.Flush($true)
    } finally {
        if ($null -ne $writer) { $writer.Dispose() } elseif ($null -ne $stream) { $stream.Dispose() }
    }
    return $lockPath
}

function Set-PQActiveLockManifestBinding {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ExternalRoot,
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][string]$ManifestSha256
    )

    if ($ManifestSha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'provider_qualification_manifest_hash_invalid'
    }
    $ExternalRoot = Assert-PQExternalRoot -Profile $Profile -ExternalRoot $ExternalRoot
    $path = Join-Path $ExternalRoot '.qualification.active.lock'
    return Invoke-PQStateLock -StatePath $path -Action {
        $lock = Read-PQActiveLock -ExternalRoot $ExternalRoot
        if ($null -eq $lock -or [string]$lock.task_id -ne [string]$Profile.task_id -or
            [string]$lock.qualification_profile -ne [string]$Profile.profile -or
            [string]$lock.run_id -ne $RunId) {
            throw 'provider_qualification_active_lock_identity_mismatch'
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$lock.manifest_sha256) -and
            [string]$lock.manifest_sha256 -ne $ManifestSha256) {
            throw 'provider_qualification_manifest_hash_changed'
        }
        $next = [ordered]@{}
        foreach ($property in $lock.PSObject.Properties) { $next[$property.Name] = $property.Value }
        $next.manifest_sha256 = $ManifestSha256
        Write-PQJsonAtomic -Path $path -Value $next
        return $path
    }
}

function Read-PQActiveLock {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$ExternalRoot)

    $path = Join-Path $ExternalRoot '.qualification.active.lock'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return $null
    }
    Test-PQNoReparseComponents -Path $path | Out-Null
    return Read-PQJson -Path $path
}

function Claim-PQActiveLockSupervisor {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ExternalRoot,
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][int]$SupervisorPid,
        [Parameter(Mandatory)][string]$SupervisorToken,
        [string]$ManifestSha256 = $null,
        [string]$SourceFreezeSha256 = $null,
        [string]$PrelaunchAuditSha256 = $null,
        [string]$PrelaunchReviewerResultSha256 = $null
    )

    $ExternalRoot = Assert-PQExternalRoot -Profile $Profile -ExternalRoot $ExternalRoot
    $path = Join-Path $ExternalRoot '.qualification.active.lock'
    return Invoke-PQStateLock -StatePath $path -Action {
        $lock = Read-PQActiveLock -ExternalRoot $ExternalRoot
        if ($null -eq $lock -or [string]$lock.task_id -ne [string]$Profile.task_id -or
            [string]$lock.qualification_profile -ne [string]$Profile.profile -or
            [string]$lock.run_id -ne $RunId -or
            -not (Test-PQLaunchToken -Token $SupervisorToken -ExpectedHash ([string]$lock.supervisor_token_sha256))) {
            throw 'provider_qualification_active_lock_identity_mismatch'
        }
        foreach ($binding in @(
            @{ name = 'manifest_sha256'; expected = $ManifestSha256 },
            @{ name = 'source_freeze_sha256'; expected = $SourceFreezeSha256 },
            @{ name = 'prelaunch_audit_sha256'; expected = $PrelaunchAuditSha256 },
            @{ name = 'prelaunch_reviewer_result_sha256'; expected = $PrelaunchReviewerResultSha256 }
        )) {
            if (-not [string]::IsNullOrWhiteSpace([string]$binding.expected) -and
                [string]$lock.($binding.name) -ne [string]$binding.expected) {
                throw 'provider_qualification_active_lock_binding_mismatch'
            }
        }
        $owner = [int]$lock.supervisor_pid
        if ($owner -ne 0 -and $owner -ne $SupervisorPid) {
            if (Test-PQProcessAlive -ProcessId $owner) {
                throw 'provider_qualification_supervisor_already_active'
            }
            throw 'provider_qualification_stale_supervisor_lock'
        }
        $next = [ordered]@{}
        foreach ($property in $lock.PSObject.Properties) { $next[$property.Name] = $property.Value }
        $next.supervisor_pid = $SupervisorPid
        Write-PQJsonAtomic -Path $path -Value $next
        return $path
    }
}

function Convert-PQActiveLockToTerminal {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ExternalRoot,
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][bool]$SupervisorExited,
        [Parameter(Mandatory)][bool]$WorkerExited,
        [Parameter(Mandatory)]$Profile,
        [switch]$Canary
    )

    if (-not ($script:PQTerminalStates -contains [string]$State.state) -or -not $SupervisorExited -or -not $WorkerExited) {
        throw 'provider_qualification_active_lock_not_terminal'
    }
    $ExternalRoot = Assert-PQExternalRoot -Profile $Profile -ExternalRoot $ExternalRoot
    $active = Join-Path $ExternalRoot '.qualification.active.lock'
    if (-not (Test-Path -LiteralPath $active -PathType Leaf)) {
        throw 'provider_qualification_active_lock_missing'
    }
    Test-PQNoReparseComponents -Path $active | Out-Null
    return Invoke-PQStateLock -StatePath $active -Action {
        $lock = Read-PQActiveLock -ExternalRoot $ExternalRoot
        if ($null -eq $lock -or [string]$lock.task_id -ne [string]$Profile.task_id -or
            [string]$lock.qualification_profile -ne [string]$Profile.profile -or
            [string]$lock.run_id -ne [string]$State.run_id -or
            [bool]$lock.canary -ne [bool]$Canary) {
            throw 'provider_qualification_active_lock_identity_mismatch'
        }
        $terminal = Join-Path $ExternalRoot ('.qualification.terminal.' + [string]$State.run_id + '.lock')
        if (Test-Path -LiteralPath $terminal) {
            throw 'provider_qualification_terminal_ledger_exists'
        }
        # Re-check both leaves while holding the state mutex immediately
        # before the move.  A reparse replacement must fail closed rather than
        # redirecting qualification evidence outside the external root.
        Test-PQNoReparseComponents -Path $active | Out-Null
        $terminalParent = Split-Path -Parent $terminal
        Test-PQNoReparseComponents -Path $terminalParent | Out-Null
        [System.IO.File]::Move($active, $terminal)
        $item = Get-Item -LiteralPath $terminal -Force
        $item.Attributes = $item.Attributes -bor [System.IO.FileAttributes]::ReadOnly
        return $terminal
    }
}

function Test-PQRunBoundMarker {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$MarkerPath,
        [Parameter(Mandatory)][string]$RunId,
        [Parameter(Mandatory)][string]$Prefix,
        [string]$Suffix = $null
    )

    if (-not (Test-Path -LiteralPath $MarkerPath -PathType Leaf)) {
        return $false
    }
    $expected = $Prefix + ':' + $RunId
    if (-not [string]::IsNullOrWhiteSpace($Suffix)) {
        $expected += ':' + $Suffix
    }
    $actual = (Get-Content -LiteralPath $MarkerPath -Raw -Encoding UTF8).Trim()
    return ($actual -eq $expected)
}

function Assert-PQManifestIdentity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Manifest,
        [Parameter(Mandatory)]$Profile,
        [Parameter(Mandatory)][string]$ManifestPath
    )

    if ([string]$Manifest.task_id -ne [string]$Profile.task_id -or
        [string]$Manifest.qualification_profile -ne [string]$Profile.profile -or
        [string]::IsNullOrWhiteSpace([string]$Manifest.run_id)) {
        throw 'provider_qualification_manifest_identity_mismatch'
    }
    $root = Assert-PQRunRoot -Profile $Profile -RunRoot ([string]$Manifest.run_root) -RunId ([string]$Manifest.run_id)
    $expectedManifest = Resolve-PQRunChild -RunRoot $root -RelativePath 'run_manifest.json'
    if (-not ([System.IO.Path]::GetFullPath($ManifestPath).Equals($expectedManifest, [System.StringComparison]::OrdinalIgnoreCase))) {
        throw 'provider_qualification_manifest_path_mismatch'
    }
    return $root
}

function Get-PQCacheSnapshot {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return [pscustomobject]@{ exists = $false; sha256 = $null; size_bytes = 0; last_write_utc = $null; json_valid = $false; model_count = 0; missing_base_instructions_count = 0 }
    }
    Test-PQNoReparseComponents -Path $Path | Out-Null
    $item = Get-Item -LiteralPath $Path
    $jsonValid = $false
    $count = 0
    $missing = 0
    try {
        $document = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        $models = @($document.models)
        $jsonValid = $true
        $count = $models.Count
        $missing = @($models | Where-Object { -not $_.PSObject.Properties.Name.Contains('base_instructions') }).Count
    } catch {
        $jsonValid = $false
    }
    return [pscustomobject]@{
        exists = $true
        sha256 = Get-PQSha256 -Path $Path
        size_bytes = [int64]$item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        json_valid = $jsonValid
        model_count = $count
        missing_base_instructions_count = $missing
    }
}

function Assert-PQExactCachePath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    $expected = 'C:\Users\Admin\.codex\models_cache.json'
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolved.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_qualification_cache_path_mismatch'
    }
    Test-PQNoReparseComponents -Path $resolved | Out-Null
    return $resolved
}

function Get-PQCacheHealth {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Snapshot)

    if (-not [bool]$Snapshot.exists) {
        throw 'BLOCKED_PROVIDER_CACHE_MISSING'
    }
    if ([bool]$Snapshot.json_valid -and [int]$Snapshot.model_count -gt 0 -and [int]$Snapshot.missing_base_instructions_count -eq 0) {
        return [pscustomobject]@{ status = 'healthy'; strategy = 'backup_only' }
    }
    return [pscustomobject]@{ status = 'degraded'; strategy = 'quarantine_rebuild' }
}

function Invoke-PQCacheBackup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$CachePath,
        [Parameter(Mandatory)][string]$BackupRoot,
        [Parameter(Mandatory)][string]$OriginalHash,
        [Parameter(Mandatory)][ValidateSet('backup_only', 'quarantine_rebuild')][string]$Strategy
    )

    $cache = Assert-PQExactCachePath -Path $CachePath
    if (-not (Test-Path -LiteralPath $cache -PathType Leaf)) {
        throw 'BLOCKED_PROVIDER_CACHE_MISSING'
    }
    if ((Get-PQSha256 -Path $cache) -ne $OriginalHash) {
        throw 'BLOCKED_PROVIDER_CACHE_DRIFT'
    }
    Test-PQNoReparseComponents -Path $BackupRoot | Out-Null
    if (Test-Path -LiteralPath $BackupRoot) {
        $entries = @(Get-ChildItem -LiteralPath $BackupRoot -Force -ErrorAction Stop)
        if ($entries.Count -ne 1 -or $entries[0].Name -ne 'rollback_journal.json' -or [bool]$entries[0].PSIsContainer) {
            throw 'provider_qualification_backup_root_exists'
        }
    } else {
        New-Item -ItemType Directory -Path $BackupRoot | Out-Null
    }
    $backup = Join-Path $BackupRoot 'models_cache.original.json'
    Copy-Item -LiteralPath $cache -Destination $backup
    if ((Get-PQSha256 -Path $backup) -ne $OriginalHash) {
        throw 'provider_qualification_backup_hash_mismatch'
    }
    $result = [ordered]@{ backup = $backup; quarantine = $null; original_hash = $OriginalHash; strategy = $Strategy }
    if ($Strategy -eq 'backup_only') {
        return [pscustomobject]$result
    }

    $quarantineDirectory = Join-Path $BackupRoot 'quarantine'
    $quarantine = Join-Path $quarantineDirectory 'models_cache.json'
    New-Item -ItemType Directory -Path $quarantineDirectory | Out-Null
    try {
        if ((Get-PQSha256 -Path $cache) -ne $OriginalHash) {
            throw 'BLOCKED_PROVIDER_CACHE_DRIFT'
        }
        Move-Item -LiteralPath $cache -Destination $quarantine
        if ((Get-PQSha256 -Path $quarantine) -ne $OriginalHash -or (Test-Path -LiteralPath $cache -PathType Leaf)) {
            throw 'provider_qualification_quarantine_hash_mismatch'
        }
    } catch {
        if (Test-Path -LiteralPath $quarantine -PathType Leaf) {
            if (-not (Test-Path -LiteralPath $cache -PathType Leaf)) {
                Move-Item -LiteralPath $quarantine -Destination $cache
            }
        } elseif (-not (Test-Path -LiteralPath $cache -PathType Leaf) -and (Test-Path -LiteralPath $backup -PathType Leaf)) {
            Copy-Item -LiteralPath $backup -Destination $cache
        }
        if ((Get-PQSha256 -Path $cache) -ne $OriginalHash) {
            throw 'provider_qualification_rollback_hash_mismatch'
        }
        throw
    }
    $result.quarantine = $quarantine
    return [pscustomobject]$result
}

function Restore-PQOriginalCache {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$CachePath,
        [Parameter(Mandatory)][string]$BackupFile,
        [string]$QuarantineFile = $null,
        [Parameter(Mandatory)][string]$OriginalHash,
        [Parameter(Mandatory)][string]$EvidenceRoot
    )

    $cache = Assert-PQExactCachePath -Path $CachePath
    Test-PQNoReparseComponents -Path $EvidenceRoot | Out-Null
    if (-not (Test-Path -LiteralPath $BackupFile -PathType Leaf) -or (Get-PQSha256 -Path $BackupFile) -ne $OriginalHash) {
        throw 'provider_qualification_backup_missing_for_rollback'
    }
    if (Test-Path -LiteralPath $cache -PathType Leaf) {
        $generated = Join-Path $EvidenceRoot ('generated-cache-' + (Get-PQSha256 -Path $cache).Substring(0, 16) + '.json')
        Move-Item -LiteralPath $cache -Destination $generated
    }
    if (-not [string]::IsNullOrWhiteSpace($QuarantineFile) -and (Test-Path -LiteralPath $QuarantineFile -PathType Leaf) -and (Get-PQSha256 -Path $QuarantineFile) -eq $OriginalHash) {
        Move-Item -LiteralPath $QuarantineFile -Destination $cache
    } else {
        Copy-Item -LiteralPath $BackupFile -Destination $cache
    }
    if ((Get-PQSha256 -Path $cache) -ne $OriginalHash) {
        throw 'provider_qualification_restore_hash_mismatch'
    }
    return $cache
}

function Wait-PQStableCache {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [int]$Samples = 5,
        [int]$IntervalSeconds = 1
    )

    $observed = @()
    for ($index = 0; $index -lt $Samples; $index++) {
        $observed += Get-PQCacheSnapshot -Path $Path
        if ($index -lt ($Samples - 1)) {
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    $keys = @($observed | ForEach-Object { "$($_.sha256)|$($_.size_bytes)|$($_.last_write_utc)" } | Select-Object -Unique)
    return [pscustomobject]@{
        stable = ($keys.Count -eq 1 -and [bool]$observed[0].exists)
        samples = $observed
        final = $observed[-1]
    }
}

function Get-PQDesktopProcessSnapshot {
    [CmdletBinding()]
    param()

    $items = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in @('ChatGPT.exe', 'codex.exe') -and $_.ExecutablePath -like '*WindowsApps*OpenAI.Codex*'
    })
    return @($items | ForEach-Object {
        [pscustomobject]@{
            pid = [int]$_.ProcessId
            parent_pid = [int]$_.ParentProcessId
            name = $_.Name
            app_server = [bool]($_.CommandLine -match 'app-server')
        }
    })
}

function Wait-PQDesktopQuiescent {
    [CmdletBinding()]
    param(
        [int]$TimeoutSeconds = 1800,
        [int]$Samples = 10
    )

    $absent = 0
    $started = Get-Date
    while (((Get-Date) - $started).TotalSeconds -lt $TimeoutSeconds) {
        if (@(Get-PQDesktopProcessSnapshot).Count -eq 0) {
            $absent++
        } else {
            $absent = 0
        }
        if ($absent -ge $Samples) {
            return [pscustomobject]@{ quiescent = $true; absent_samples = $absent; timeout = $false }
        }
        Start-Sleep -Seconds 1
    }
    return [pscustomobject]@{ quiescent = $false; absent_samples = $absent; timeout = $true }
}

function Get-PQWorkerRecoveryDisposition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$State,
        [int]$MaxGenerations = 3
    )

    if ($script:PQTerminalStates -contains [string]$State.state) {
        return 'terminal'
    }
    if ([string]$State.smoke.status -eq 'claimed' -or [string]$State.acceptance.status -eq 'claimed') {
        return 'command_outcome_unknown'
    }
    # These checkpoints are an intentional handoff to the human read-only
    # Verify/Finalize step.  They are not a dead-worker recovery request, even
    # when the profile permits only one Worker generation.
    if (@('verification_passed', 'complete_pending_review') -contains [string]$State.state) {
        return 'handoff_pending'
    }
    if ([int]$State.worker_generation -ge $MaxGenerations) {
        if ($MaxGenerations -eq 1) {
            return 'checkpoint_unsafe'
        }
        return 'generation_limit'
    }

    # A generation may continue only from checkpoints where all side effects are
    # either absent, atomically journaled, or already one-shot completed.  The
    # Worker re-validates Desktop/cache/source-freeze evidence before it uses
    # any of these checkpoints.
    if (@(
        'worker_started', 'supervisor_ready', 'worker_armed',
        'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable',
        'cache_backed_up', 'cache_quarantined', 'smoke_passed',
        'acceptance_passed', 'verification_passed', 'complete_pending_review'
    ) -contains [string]$State.state) {
        if ([bool]$State.cache_mutation_started -and [string]$State.state -eq 'cache_stable') {
            return 'cache_reconciliation_required'
        }
        return 'restart_safe'
    }
    return 'checkpoint_unsafe'
}

Export-ModuleMember -Function @(
    'Get-PQProfile',
    'Assert-PQOperationalAuthorization',
    'Get-PQSanitizedError',
    'Get-PQStablePreflightReason',
    'New-PQPreflightFailure',
    'Get-PQPreflightFailureContext',
    'Get-PQSha256',
    'New-PQLaunchToken',
    'Get-PQTokenHash',
    'Test-PQLaunchToken',
    'Get-PQCommandFingerprint',
    'Write-PQJsonAtomic',
    'Write-PQTextAtomic',
    'Assert-PQNoOrphanTemporaryFiles',
    'Invoke-PQStateLock',
    'Read-PQJson',
    'Copy-PQObject',
    'Test-PQNoReparseComponents',
    'Resolve-PQRunChild',
    'Assert-PQRunRoot',
    'Assert-PQExternalRoot',
    'Assert-PQManifestPath',
    'Test-PQProcessAlive',
    'Assert-PQSupervisorLivenessProbe',
    'Invoke-PQBoundedProcess',
    'New-PQInitialState',
    'Assert-PQStateIdentity',
    'Assert-PQStateSchemaTestContract',
    'Assert-PQTransition',
    'Move-PQRunState',
    'Update-PQRunState',
    'Invoke-PQWorkerLaunchTransaction',
    'Publish-PQWorkerReadyMarker',
    'Invoke-PQSupervisorWorkerStartup',
    'Claim-PQCommand',
    'Complete-PQCommand',
    'Write-PQHeartbeat',
    'New-PQActiveLock',
    'Set-PQActiveLockManifestBinding',
    'Read-PQActiveLock',
    'Claim-PQActiveLockSupervisor',
    'Convert-PQActiveLockToTerminal',
    'Test-PQRunBoundMarker',
    'Assert-PQManifestIdentity',
    'Get-PQCacheSnapshot',
    'Assert-PQExactCachePath',
    'Get-PQCacheHealth',
    'Invoke-PQCacheBackup',
    'Restore-PQOriginalCache',
    'Wait-PQStableCache',
    'Get-PQDesktopProcessSnapshot',
    'Wait-PQDesktopQuiescent',
    'Assert-PQStateSchema',
    'Assert-PQFinalReviewSchema',
    'Get-PQCanonicalBoundarySha256',
    'Assert-PQFinalReviewBindings',
    'Get-PQWorkerRecoveryDisposition'
)
