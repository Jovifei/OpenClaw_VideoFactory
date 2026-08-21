$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue

Describe 'ProviderQualification 005T profile mapping' {
    It 'uses an isolated task, root, fixture and report namespace' {
        $profile = Get-PQProfile -QualificationProfile '005T'
        $profile.profile | Should Be '005T'
        $profile.task_id | Should Be 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
        $profile.schema_version | Should Be '1.1'
        $profile.external_root | Should Be 'E:\Claude_allow\Download\codex-provider-recovery-005t'
        $profile.fixture_directory | Should Be 'examples\ai_director_provider_qualification_005t'
        $profile.expected_topic_digest | Should Be 'fbe64e97fba1bcaaf2ff7de47d0385febe75f0b339cc5d3f543e4196d7f1fc70'
        $profile.output_name | Should Be 'pink_pig_modbus_ai_provider_005t.mp4'
        $profile.prelaunch_audit_path | Should Be 'reports\CODEX_PROVIDER_PRELAUNCH_AUDIT_005T.json'
        $profile.start_closed | Should Be $true
    }

    It 'keeps the 005S fingerprint stable and supports a 005T namespace' {
        $old = [System.BitConverter]::ToString(
            [System.Security.Cryptography.SHA256]::Create().ComputeHash(
                [System.Text.Encoding]::UTF8.GetBytes('AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S:smoke:v1')
            )
        ).Replace('-', '').ToLowerInvariant()
        (Get-PQCommandFingerprint -Name 'smoke') | Should Be $old
        $new = Get-PQCommandFingerprint -Name 'smoke' -TaskId 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
        $new | Should Not Be $old
    }

    It 'binds a claimed command to the 005T task identity' {
        $profile = Get-PQProfile -QualificationProfile '005T'
        $state = New-PQInitialState -Profile $profile -RunId 'session_005t_ledger'
        $path = Join-Path $TestDrive '005t-state.json'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'prelaunch_validated' -Stage 'test'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'source_frozen' -Stage 'test' -Patch @{ source_freeze_sha256 = ('a' * 64) }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'supervisor_started' -Stage 'test' -Patch @{ supervisor_pid = 1; supervisor_token_sha256 = ('b' * 64) }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'worker_started' -Stage 'test' -Patch @{ worker_generation = 1; worker_launch_count = 1; worker_pid = 0; worker_token_sha256 = ('c' * 64); lease_id = ('d' * 32); lease_expires_utc = '2026-08-11T00:00:00.0000000Z' }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'supervisor_ready' -Stage 'test' -Patch @{ worker_pid = 2 }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'worker_armed' -Stage 'test'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'waiting_for_desktop_exit' -Stage 'test'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'desktop_quiescent' -Stage 'test' -Patch @{ desktop_quiescent = $true }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'cache_stable' -Stage 'test' -Patch @{ original_cache_sha256 = ('e' * 64); cache_strategy = 'backup_only' }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'cache_backed_up' -Stage 'test'
        $fp = Get-PQCommandFingerprint -Name 'smoke' -TaskId $profile.task_id
        { Claim-PQCommand -State $state -StatePath $path -Command smoke -NewState 'smoke_started' -Fingerprint $fp -TaskId $profile.task_id } | Should Not Throw
    }

    It 'creates a schema-valid 005T 1.1 state snapshot' {
        $profile = Get-PQProfile -QualificationProfile '005T'
        $state = New-PQInitialState -Profile $profile -RunId 'session_005t_schema'
        $state.task_id | Should Be 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
        $state.qualification_profile | Should Be '005T'
        { Assert-PQStateSchema -State $state } | Should Not Throw
    }

    It 'rejects a mismatched 005T task/profile pair' {
        $profile = Get-PQProfile -QualificationProfile '005T'
        $state = New-PQInitialState -Profile $profile -RunId 'session_005t_mismatch'
        $state.task_id = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
        { Assert-PQStateSchema -State $state } | Should Throw
    }

    It 'rejects a second worker generation for the single-attempt 005T profile' {
        $profile = Get-PQProfile -QualificationProfile '005T'
        $state = New-PQInitialState -Profile $profile -RunId 'session_005t_generation'
        $path = Join-Path $TestDrive '005t-generation.json'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'prelaunch_validated' -Stage 'test'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'source_frozen' -Stage 'test' -Patch @{ source_freeze_sha256 = ('a' * 64) }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'supervisor_started' -Stage 'test' -Patch @{ supervisor_pid = 1; supervisor_token_sha256 = ('b' * 64) }
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'worker_started' -Stage 'test' -Patch @{ worker_generation = 1; worker_launch_count = 1; worker_pid = 0; worker_token_sha256 = ('c' * 64); lease_id = ('d' * 32); lease_expires_utc = '2026-08-11T00:00:00.0000000Z' }
        { Move-PQRunState -State $state -StatePath $path -NewState 'supervisor_ready' -Stage 'test' -Patch @{ worker_generation = 2; worker_launch_count = 2; worker_pid = 3; worker_token_sha256 = ('e' * 64); lease_id = ('f' * 32); lease_expires_utc = '2026-08-11T00:01:00.0000000Z' } } | Should Throw
    }
}
