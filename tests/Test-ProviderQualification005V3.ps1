$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue
$entryScript = Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1'
. $entryScript -QualificationProfile '005V3' -LoadOnly

Describe 'ProviderQualification 005V3 preflight observability contract' {
    It 'binds a diagnostic-only profile and rejects operational modes' {
        $profile = Get-PQProfile -QualificationProfile '005V3'
        $profile.profile | Should Be '005V3'
        $profile.task_id | Should Be 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-DIAGNOSTICS-005V3'
        $profile.schema_version | Should Be '1.1'
        $profile.max_worker_generations | Should Be 0
        $profile.allow_rehearsal | Should Be $false
        $profile.start_closed | Should Be $true

        $request = [pscustomobject]@{
            id = $profile.task_id
            mode = 'single_read_only_preflight_diagnostic'
            execution_status = 'ready_for_diagnostic_preflight'
            maximum_preflight_commands = 1
            maximum_worker_generations = 0
            maximum_smoke_commands = 0
            maximum_acceptance_commands = 0
            allow_rehearsal = $false
            allows_read_only_preflight_probes = $true
            allows_read_only_metadata_probes = $true
            allows_read_only_hash_probes = $true
            allows_read_only_process_probes = $true
            does_not_authorize_cache_mutation = $true
            does_not_authorize_config_auth_mutation = $true
            does_not_authorize_desktop_control = $true
            does_not_authorize_desktop_operation = $true
            does_not_authorize_worker_start = $true
            does_not_authorize_provider_execution = $true
            does_not_authorize_oauth_profile_model_config_changes = $true
            does_not_authorize_commit_or_push = $true
        }
        { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $request -Mode 'Preflight' } | Should Not Throw
        foreach ($field in @(
            'allows_read_only_preflight_probes', 'allows_read_only_metadata_probes',
            'allows_read_only_hash_probes', 'allows_read_only_process_probes',
            'does_not_authorize_cache_mutation', 'does_not_authorize_config_auth_mutation',
            'does_not_authorize_desktop_control', 'does_not_authorize_desktop_operation',
            'does_not_authorize_worker_start', 'does_not_authorize_provider_execution',
            'does_not_authorize_oauth_profile_model_config_changes', 'does_not_authorize_commit_or_push'
        )) {
            $invalid = [pscustomobject]@{}
            foreach ($property in $request.PSObject.Properties) { $invalid | Add-Member -NotePropertyName $property.Name -NotePropertyValue $property.Value }
            $invalid.$field = $false
            { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $invalid -Mode 'Preflight' } | Should Throw 'provider_qualification_change_request_not_authorized'
        }
        foreach ($mode in @('Start', 'Rehearse', 'Supervisor', 'Worker', 'Status', 'Verify')) {
            { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $request -Mode $mode } | Should Throw 'provider_qualification_diagnostic_profile_only'
        }
    }

    It 'creates a schema-shaped sanitized failure without raw exception data' {
        $raw = 'private C:\secret\token abc PROMPT=do-not-copy cache models command --profile hidden'
        $failure = New-PQPreflightFailure -Gate 'codex_cli' -Substep 'version_probe' -Reason (Get-PQStablePreflightReason -RawReason $raw)
        $context = Get-PQPreflightFailureContext -Exception $failure
        $document = New-PQPreflightFailureEnvelope -Gate $context.gate -Substep $context.substep -Reason $context.reason -ExitCode $context.exit_code
        $json = $document.error | ConvertTo-Json -Depth 8 -Compress
        $parsed = $json | ConvertFrom-Json
        $parsed.code | Should Be 'provider_qualification_preflight_failed'
        $parsed.message | Should Be 'Provider preflight stopped.'
        $parsed.context.stage | Should Be 'preflight'
        $parsed.context.gate | Should Be 'codex_cli'
        $parsed.context.substep | Should Be 'version_probe'
        $parsed.context.reason | Should Be 'unexpected_error'
        $parsed.context.exit_code | Should Be $null
        $json | Should Not Match 'secret|token|PROMPT|cache|profile|command'
        @($parsed.PSObject.Properties.Name) | Should Be @('code', 'message', 'context')
        @($parsed.context.PSObject.Properties.Name) | Should Be @('stage', 'gate', 'substep', 'reason', 'exit_code')
    }

    It 'builds the actual outer CLI envelope without raw failure data' {
        $document = New-PQPreflightFailureEnvelope -Gate 'cache_snapshot' -Substep 'json_parse' -Reason 'cache_invalid' -ExitCode 1
        $document.status | Should Be 'error'
        $document.error.code | Should Be 'provider_qualification_preflight_failed'
        $document.error.message | Should Be 'Provider preflight stopped.'
        $document.error.context.gate | Should Be 'cache_snapshot'
        $document.error.context.substep | Should Be 'json_parse'
        $document.error.context.reason | Should Be 'cache_invalid'
        ($document | ConvertTo-Json -Depth 8 -Compress) | Should Not Match 'C:\\|token|PROMPT|models|--profile'
    }

    It 'preserves stable gate, substep and reason values for every preflight gate' {
        $cases = @(
            @('authorization', 'change_request', 'change_request_not_authorized'),
            @('source_freeze', 'source_freeze_hash', 'source_freeze_drift'),
            @('external_root', 'external_root_path', 'fresh_evidence_required'),
            @('active_lock', 'active_lock_probe', 'active_run_exists'),
            @('fresh_job', 'job_path', 'fresh_job_required'),
            @('fresh_evidence', 'external_root_entries', 'fresh_evidence_required'),
            @('git_boundary', 'git_index', 'git_index_changed'),
            @('codex_cli', 'path_resolution', 'cli_not_npm'),
            @('codex_cli', 'version_probe', 'cli_version_unsupported'),
            @('codex_cli', 'help_probe', 'cli_help_unavailable'),
            @('codex_cli', 'required_flags', 'cli_flag_missing'),
            @('media_tools', 'tool_path', 'media_tool_unavailable'),
            @('media_tools', 'tool_hash', 'media_tool_changed'),
            @('immutable_005t', 'evidence_identity', 'immutable_005t_invalid'),
            @('immutable_005t', 'evidence_hash', 'immutable_005t_drift'),
            @('cache_snapshot', 'json_parse', 'cache_invalid'),
            @('cache_snapshot', 'health', 'cache_unhealthy'),
            @('environment_hashes', 'baseline_hash', 'environment_baseline_missing'),
            @('environment_hashes', 'config_hash', 'config_changed'),
            @('environment_hashes', 'auth_hash', 'auth_changed'),
            @('desktop_snapshot', 'process_probe', 'desktop_probe_failed')
        )
        foreach ($case in $cases) {
            $exception = New-PQPreflightFailure -Gate $case[0] -Substep $case[1] -Reason $case[2]
            $context = Get-PQPreflightFailureContext -Exception $exception
            $context.stage | Should Be 'preflight'
            $context.gate | Should Be $case[0]
            $context.substep | Should Be $case[1]
            $context.reason | Should Be $case[2]
        }
    }

    It 'normalizes known raw errors and hides unknown errors' {
        (Get-PQStablePreflightReason -RawReason 'provider_qualification_cli_not_npm') | Should Be 'cli_not_npm'
        (Get-PQStablePreflightReason -RawReason 'BLOCKED_PROVIDER_CACHE_MISSING') | Should Be 'cache_missing'
        (Get-PQStablePreflightReason -RawReason 'provider_qualification_auth_changed') | Should Be 'auth_changed'
        (Get-PQStablePreflightReason -RawReason 'System.Exception: C:\private\raw') | Should Be 'unexpected_error'
    }

    It 'wraps a gate exception with only the fixed diagnostic context' {
        $failure = $null
        try {
            Invoke-PQPreflightGate -Gate 'media_tools' -Substep 'tool_hash' -Action {
                throw 'C:\private\ffmpeg.exe leaked in a raw provider command'
            } | Out-Null
        } catch {
            $failure = $_.Exception
        }
        $failure | Should Not Be $null
        $context = Get-PQPreflightFailureContext -Exception $failure
        $context.gate | Should Be 'media_tools'
        $context.substep | Should Be 'tool_hash'
        $context.reason | Should Be 'unexpected_error'
        $failure.Message | Should Be 'Provider preflight stopped.'
        $failure.ToString() | Should Not Match 'ffmpeg|private|provider command'
    }

    It 'keeps 005V2 terminal and prevents bridge reuse' {
        $bridge = Get-Content -Raw (Join-Path $PSScriptRoot '..\reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2.json') | ConvertFrom-Json
        $bridge.execution_status | Should Be 'preflight_blocked'
        $bridge.result.status | Should Be 'PREFLIGHT_BLOCKED'
        $bridge.result.command_count | Should Be 1
        $bridge.result.smoke_attempts | Should Be 0
        $bridge.result.acceptance_attempts | Should Be 0
        { Assert-PQOperationalAuthorization -Profile (Get-PQProfile -QualificationProfile '005V3') -ChangeRequest $bridge -Mode 'Preflight' } | Should Throw
    }

    It 'resolves its own diagnostic CR and never consumes the 005V2 counter' {
        $profile = Get-PQProfile -QualificationProfile '005V3'
        $request = Get-PQOperationalChangeRequest -Mode 'Preflight'
        $request.id | Should Be $profile.task_id
        $request.execution_status | Should Be 'prepared_pending_diagnostic_review'
        $request.maximum_preflight_commands | Should Be 1
        $request.maximum_worker_generations | Should Be 0
        $request.maximum_smoke_commands | Should Be 0
        $request.maximum_acceptance_commands | Should Be 0
        $request.allows_read_only_preflight_probes | Should Be $true
        $request.allows_read_only_metadata_probes | Should Be $true
        $request.allows_read_only_hash_probes | Should Be $true
        $request.allows_read_only_process_probes | Should Be $true
        $request.does_not_authorize_provider_execution | Should Be $true
        $request.does_not_authorize_oauth_profile_model_config_changes | Should Be $true
        $request.does_not_authorize_desktop_operation | Should Be $true
        $request.id | Should Not Be 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2'
    }

    It 'hash-binds the immutable 005V2 bridge and rejects changed terminal facts' {
        $freeze = Get-PQ005V2ImmutableEvidenceFreeze
        $freeze.task_id | Should Be 'AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2'
        $freeze.execution_status | Should Be 'preflight_blocked'
        $freeze.result_status | Should Be 'PREFLIGHT_BLOCKED'
        $freeze.command_count | Should Be 1
        $freeze.smoke_attempts | Should Be 0
        $freeze.acceptance_attempts | Should Be 0
        $freeze.mp4_count | Should Be 0
        { Assert-PQ005V2ImmutableEvidenceFreezeDocument -Evidence $freeze } | Should Not Throw
    }

    It 'includes the new error contract and test in the diagnostic freeze target set' {
        $source = Get-Content -Raw (Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1')
        $source | Should Match 'provider_qualification_preflight_error.schema.json'
        $source | Should Match 'Test-ProviderQualification005V3.ps1'
        $source | Should Match 'provider_qualification_preflight_failed'
        $source | Should Match 'New-PQPreflightFailureEnvelope'
        $source | Should Match 'Get-PQPreflightFailureContext'
        $source | Should Match 'Invoke-PQPreflightGate'
        $targets = @(Get-PQSourceFreezeTargetList -IncludeFixture)
        ($targets -contains 'schemas/ops/provider_qualification_preflight_error.schema.json') | Should Be $true
        ($targets -contains 'tests/Test-ProviderQualification005V3.ps1') | Should Be $true
        $fixtures = @(Get-PQFixtureFreezeTargets -QualificationProfile (Get-PQProfile -QualificationProfile '005V3') -IncludeFixture)
        $fixtures | Should Be @(
            'examples\ai_director_provider_qualification_005v/topic.txt',
            'examples\ai_director_provider_qualification_005v/factual_brief.json',
            'examples\ai_director_provider_qualification_005v/README.md'
        )
    }

    It 'does not invoke external commands or operational modes from this test file' {
        $tokens = $null
        $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($PSCommandPath, [ref]$tokens, [ref]$errors)
        @($errors).Count | Should Be 0
        @($ast.FindAll({ param($node)
            $node -is [System.Management.Automation.Language.CommandAst] -and
            ($node.InvocationOperator -eq [System.Management.Automation.Language.TokenKind]::Ampersand -or
             [string]$node.GetCommandName() -match '^(Start-Process|Invoke-Expression|Stop-Process|taskkill|codex|python|powershell|pwsh)$')
        }, $true)).Count | Should Be 0
    }
}
