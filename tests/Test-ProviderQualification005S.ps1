$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue

function New-TestState {
    param([string]$RunId = 'session_test_005s')
    return New-PQInitialState -Profile (Get-PQProfile -QualificationProfile '005S') -RunId $RunId
}

function Move-TestState {
    param([object]$State, [string]$Path, [string]$Target, [hashtable]$Patch = @{})
    return Move-PQRunState -State $State -StatePath $Path -NewState $Target -Stage 'test' -Patch $Patch
}

Describe 'ProviderQualification 005S profile and state contract' {
    It 'has only fixed profile mappings and keeps 005R closed' {
        (Get-PQProfile -QualificationProfile '005S').task_id | Should Be 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
        (Get-PQProfile -QualificationProfile '005R').start_closed | Should Be $true
        { Get-PQProfile -QualificationProfile 'untrusted' } | Should Throw
    }

    It 'rejects the consumed 005R Start command with a structured exit-two envelope' {
        $entry = Join-Path $PSScriptRoot '..\scripts\provider_qualification_005r.ps1'
        $output = & 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -NoProfile -ExecutionPolicy Bypass -File $entry -Mode Start -Apply 2>$null
        $LASTEXITCODE | Should Be 2
        $document = ($output | Out-String | ConvertFrom-Json)
        $document.status | Should Be 'error'
        $document.error.code | Should Be 'provider_qualification_run_closed'
        $document.error.context.reason | Should Be 'historical_run_closed'
    }

    It 'uses a 1.1 state with all resumable ledger fields' {
        $state = New-TestState
        $state.schema_version | Should Be '1.1'
        $state.qualification_profile | Should Be '005S'
        $state.worker_generation | Should Be 0
        $state.smoke.status | Should Be 'not_started'
        $state.acceptance.attempt_count | Should Be 0
    }

    It 'enforces the prelaunch and worker-armed state chain' {
        $path = Join-Path $TestDrive 'state-chain.json'
        $state = New-TestState
        foreach ($target in @('prelaunch_validated', 'source_frozen', 'supervisor_started', 'worker_started', 'supervisor_ready', 'worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up')) {
            $patch = @{}
            if ($target -eq 'source_frozen') { $patch.source_freeze_sha256 = ('a' * 64) }
            if ($target -eq 'supervisor_started') { $patch = @{ supervisor_pid = 1; supervisor_token_sha256 = ('d' * 64) } }
            if ($target -eq 'worker_started') { $patch = @{ worker_generation = 1; worker_launch_count = 1; supervisor_pid = 1; worker_pid = 0; supervisor_token_sha256 = ('d' * 64); worker_token_sha256 = ('e' * 64); lease_id = ('b' * 32); lease_expires_utc = '2026-08-11T00:00:00.0000000Z' } }
            if ($target -eq 'supervisor_ready') { $patch.worker_pid = 2 }
            if ($target -eq 'desktop_quiescent') { $patch.desktop_quiescent = $true }
            if ($target -eq 'cache_stable') { $patch.original_cache_sha256 = ('c' * 64); $patch.cache_strategy = 'backup_only' }
            $state = Move-TestState -State $state -Path $path -Target $target -Patch $patch
        }
        $state.state | Should Be 'cache_backed_up'
        $state.revision | Should Be 11
        { Move-TestState -State $state -Path $path -Target 'acceptance_started' } | Should Throw
    }

    It 'claims each Provider command only once and cannot reset it' {
        $path = Join-Path $TestDrive 'state-ledger.json'
        $state = New-TestState
        foreach ($target in @('prelaunch_validated', 'source_frozen', 'supervisor_started', 'worker_started', 'supervisor_ready', 'worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable', 'cache_backed_up')) {
            $patch = @{}
            if ($target -eq 'source_frozen') { $patch.source_freeze_sha256 = ('a' * 64) }
            if ($target -eq 'supervisor_started') { $patch = @{ supervisor_pid = 1; supervisor_token_sha256 = ('d' * 64) } }
            if ($target -eq 'worker_started') { $patch = @{ worker_generation = 1; worker_launch_count = 1; supervisor_pid = 1; worker_pid = 0; supervisor_token_sha256 = ('d' * 64); worker_token_sha256 = ('e' * 64); lease_id = ('b' * 32); lease_expires_utc = '2026-08-11T00:00:00.0000000Z' } }
            if ($target -eq 'supervisor_ready') { $patch.worker_pid = 2 }
            if ($target -eq 'desktop_quiescent') { $patch.desktop_quiescent = $true }
            if ($target -eq 'cache_stable') { $patch.original_cache_sha256 = ('c' * 64); $patch.cache_strategy = 'backup_only' }
            $state = Move-TestState -State $state -Path $path -Target $target -Patch $patch
        }
        $state = Claim-PQCommand -State $state -StatePath $path -Command smoke -NewState 'smoke_started' -Fingerprint (Get-PQCommandFingerprint -Name 'smoke')
        $state.smoke.attempt_count | Should Be 1
        { Claim-PQCommand -State $state -StatePath $path -Command smoke -NewState 'smoke_started' -Fingerprint ('e' * 64) } | Should Throw
        { Update-PQRunState -State $state -StatePath $path -Patch @{ smoke = @{ status = 'not_started'; attempt_count = 0; command_fingerprint = $null } } } | Should Throw
    }

    It 'requires a structured terminal error and keeps terminals immutable' {
        $path = Join-Path $TestDrive 'state-terminal.json'
        $state = New-TestState
        { Move-PQRunState -State $state -StatePath $path -NewState 'blocked' -Stage 'test' } | Should Throw
        $error = Get-PQSanitizedError -Code 'BLOCKED_TEST' -Stage 'test' -Reason 'fault_injection'
        $state = Move-PQRunState -State $state -StatePath $path -NewState 'blocked' -Stage 'test' -ErrorObject $error
        { Update-PQRunState -State $state -StatePath $path -Patch @{ heartbeat_sequence = 1 } } | Should Throw
    }
}

Describe 'ProviderQualification 005S containment and locking' {
    It 'rejects relative path escape and rooted replacement' {
        $root = Join-Path $TestDrive 'session_test_path'
        New-Item -ItemType Directory -Path $root | Out-Null
        (Resolve-PQRunChild -RunRoot $root -RelativePath 'state.json') | Should Be (Join-Path $root 'state.json')
        { Resolve-PQRunChild -RunRoot $root -RelativePath '..\outside.json' } | Should Throw
        { Resolve-PQRunChild -RunRoot $root -RelativePath 'C:\outside.json' } | Should Throw
    }

    It 'fails closed when a prior raw Provider artifact is retained' {
        $root = Join-Path $TestDrive 'raw-retention'
        $raw = Join-Path $root 'raw\smoke'
        New-Item -ItemType Directory -Path $raw -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $raw 'stdout.txt') -Value 'untrusted output' -Encoding UTF8
        { Assert-PQNoOrphanTemporaryFiles -RunRoot $root } | Should Throw
    }

    It 'binds an active lock to the exact profile and run' {
        $root = Join-Path $TestDrive 'locks'
        New-Item -ItemType Directory -Path $root | Out-Null
        $profile = [pscustomobject]@{
            profile = '005S'
            task_id = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
            schema_version = '1.1'
            external_root = $root
            start_closed = $false
        }
        $token = 'a' * 64
        $lock = New-PQActiveLock -ExternalRoot $root -Profile $profile -RunId 'session_test_lock' -SupervisorPid 0 -SupervisorTokenHash (Get-PQTokenHash -Token $token)
        (Read-PQActiveLock -ExternalRoot $root).run_id | Should Be 'session_test_lock'
        { New-PQActiveLock -ExternalRoot $root -Profile $profile -RunId 'session_other_lock' -SupervisorPid 321 -SupervisorTokenHash (Get-PQTokenHash -Token $token) } | Should Throw
        Claim-PQActiveLockSupervisor -ExternalRoot $root -Profile $profile -RunId 'session_test_lock' -SupervisorPid 456 -SupervisorToken $token | Out-Null
        (Read-PQActiveLock -ExternalRoot $root).supervisor_pid | Should Be 456
    }

    It 'requires exact run-bound review markers' {
        $marker = Join-Path $TestDrive 'marker.txt'
        Set-Content -LiteralPath $marker -Value 'final_review_approved:session_test_marker:abc' -Encoding UTF8
        (Test-PQRunBoundMarker -MarkerPath $marker -RunId 'session_test_marker' -Prefix 'final_review_approved' -Suffix 'abc') | Should Be $true
        (Test-PQRunBoundMarker -MarkerPath $marker -RunId 'session_other_marker' -Prefix 'final_review_approved' -Suffix 'abc') | Should Be $false
    }

    It 'rejects a second supervisor owner and an invalid launch token' {
        $root = Join-Path $TestDrive 'supervisor-ownership'
        New-Item -ItemType Directory -Path $root | Out-Null
        $profile = [pscustomobject]@{
            profile = '005S'
            task_id = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
            schema_version = '1.1'
            external_root = $root
            start_closed = $false
        }
        $token = 'a' * 64
        New-PQActiveLock -ExternalRoot $root -Profile $profile -RunId 'session_supervisor_lock' -SupervisorPid 0 -SupervisorTokenHash (Get-PQTokenHash -Token $token) | Out-Null
        { Claim-PQActiveLockSupervisor -ExternalRoot $root -Profile $profile -RunId 'session_supervisor_lock' -SupervisorPid 123 -SupervisorToken ('b' * 64) } | Should Throw
        Claim-PQActiveLockSupervisor -ExternalRoot $root -Profile $profile -RunId 'session_supervisor_lock' -SupervisorPid 123 -SupervisorToken $token | Out-Null
        { Claim-PQActiveLockSupervisor -ExternalRoot $root -Profile $profile -RunId 'session_supervisor_lock' -SupervisorPid 456 -SupervisorToken $token } | Should Throw
    }

    It 'converts only a terminal, fully-exited active lock to a readonly ledger' {
        $root = Join-Path $TestDrive 'terminal-lock'
        New-Item -ItemType Directory -Path $root | Out-Null
        $profile = [pscustomobject]@{
            profile = '005S'
            task_id = 'AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S'
            schema_version = '1.1'
            external_root = $root
            start_closed = $false
        }
        $token = 'c' * 64
        New-PQActiveLock -ExternalRoot $root -Profile $profile -RunId 'session_terminal_lock' -SupervisorPid 0 -SupervisorTokenHash (Get-PQTokenHash -Token $token) | Out-Null
        $state = [pscustomobject]@{ run_id = 'session_terminal_lock'; state = 'blocked' }
        { Convert-PQActiveLockToTerminal -ExternalRoot $root -Profile $profile -State $state -SupervisorExited $false -WorkerExited $true } | Should Throw
        $ledger = Convert-PQActiveLockToTerminal -ExternalRoot $root -Profile $profile -State $state -SupervisorExited $true -WorkerExited $true
        (Test-Path -LiteralPath $ledger -PathType Leaf) | Should Be $true
        ((Get-Item -LiteralPath $ledger -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) | Should Not Be 0
    }
}

Describe 'ProviderQualification 005S fault-injection contracts' {
    It 'enforces the runtime JSON schema before every state write' {
        $state = New-TestState -RunId 'session_runtime_schema'
        Assert-PQStateSchema -State $state
        $invalid = Copy-PQObject -Value $state
        $invalid.revision = 0
        { Assert-PQStateSchema -State $invalid } | Should Throw
    }

    It 'rejects an invalid lease timestamp through the runtime schema gate' {
        $state = New-TestState -RunId 'session_invalid_lease'
        $state.lease_expires_utc = 'not-a-date'
        { Assert-PQStateSchema -State $state } | Should Throw
    }

    It 'does not allow established booleans or cache strategy to regress' {
        $path = Join-Path $TestDrive 'monotonic-state.json'
        $state = New-TestState -RunId 'session_monotonic'
        foreach ($target in @('prelaunch_validated', 'source_frozen', 'supervisor_started', 'worker_started', 'supervisor_ready', 'worker_armed', 'waiting_for_desktop_exit', 'desktop_quiescent', 'cache_stable')) {
            $patch = @{}
            if ($target -eq 'source_frozen') { $patch.source_freeze_sha256 = ('a' * 64) }
            if ($target -eq 'supervisor_started') { $patch = @{ supervisor_pid = 1; supervisor_token_sha256 = ('d' * 64) } }
            if ($target -eq 'worker_started') { $patch = @{ worker_generation = 1; worker_launch_count = 1; supervisor_pid = 1; worker_pid = 0; supervisor_token_sha256 = ('d' * 64); worker_token_sha256 = ('e' * 64); lease_id = ('b' * 32); lease_expires_utc = '2026-08-11T00:00:00.0000000Z' } }
            if ($target -eq 'supervisor_ready') { $patch.worker_pid = 2 }
            if ($target -eq 'desktop_quiescent') { $patch.desktop_quiescent = $true; $patch.desktop_seen_before_quiescence = $true }
            if ($target -eq 'cache_stable') { $patch.original_cache_sha256 = ('c' * 64); $patch.cache_strategy = 'backup_only' }
            $state = Move-TestState -State $state -Path $path -Target $target -Patch $patch
        }
        { Update-PQRunState -State $state -StatePath $path -Patch @{ desktop_quiescent = $false } } | Should Throw
        { Update-PQRunState -State $state -StatePath $path -Patch @{ cache_strategy = 'quarantine_rebuild' } } | Should Throw
    }

    It 'rejects a stale state writer instead of overwriting a newer revision' {
        $path = Join-Path $TestDrive 'state-conflict.json'
        $original = New-TestState -RunId 'session_state_conflict'
        $current = Move-TestState -State $original -Path $path -Target 'prelaunch_validated'
        { Move-TestState -State $original -Path $path -Target 'prelaunch_validated' } | Should Throw
        $current.revision | Should Be 2
    }

    It 'classifies claimed commands and unsafe cache mutation as non-restartable' {
        $state = New-TestState -RunId 'session_recovery_matrix'
        $state.state = 'worker_armed'
        (Get-PQWorkerRecoveryDisposition -State $state) | Should Be 'restart_safe'
        $state.smoke = [ordered]@{ status = 'claimed'; attempt_count = 1; command_fingerprint = ('d' * 64) }
        (Get-PQWorkerRecoveryDisposition -State $state) | Should Be 'command_outcome_unknown'
        $state.smoke = [ordered]@{ status = 'not_started'; attempt_count = 0; command_fingerprint = $null }
        $state.state = 'cache_stable'
        $state.cache_mutation_started = $true
        (Get-PQWorkerRecoveryDisposition -State $state) | Should Be 'cache_reconciliation_required'
        $state.state = 'completed'
        (Get-PQWorkerRecoveryDisposition -State $state) | Should Be 'terminal'
    }

    It 'keeps sanitized errors free of paths and raw exception text' {
        $error = Get-PQSanitizedError -Code 'BLOCKED_TEST' -Stage 'bad/stage' -Reason 'C:\private\secret'
        $error.context.stage | Should Be 'qualification'
        $error.context.reason | Should Be 'unexpected_error'
        ($error | ConvertTo-Json -Depth 8) -match 'private|secret|C:\\' | Should Be $false
    }
}

Describe 'ProviderQualification 005S schema and static safety' {
    It 'keeps 1.0 and 1.1 documents structurally distinct' {
        $legacy = New-PQInitialState -Profile (Get-PQProfile -QualificationProfile '005R') -RunId 'session_legacy_schema'
        $current = New-TestState -RunId 'session_current_schema'
        $legacy.schema_version | Should Be '1.0'
        $current.schema_version | Should Be '1.1'
        $current.PSObject.Properties.Name -contains 'qualification_profile' | Should Be $true
    }

    It 'validates both historical 1.0 and current 1.1 state snapshots against the shared schema' {
        $schema = Join-Path $PSScriptRoot '..\schemas\ops\provider_qualification_run.schema.json'
        $legacy = New-PQInitialState -Profile (Get-PQProfile -QualificationProfile '005R') -RunId 'session_legacy_schema'
        $current = New-TestState -RunId 'session_current_schema'
        $legacyPath = Join-Path $TestDrive 'legacy.json'
        $currentPath = Join-Path $TestDrive 'current.json'
        $legacy | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $legacyPath -Encoding UTF8
        $current | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $currentPath -Encoding UTF8
        $python = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
        & $python -c 'import json,sys,jsonschema; s=json.load(open(sys.argv[1],encoding=''utf-8-sig'')); [jsonschema.validate(json.load(open(p,encoding=''utf-8-sig'')),s) for p in sys.argv[2:]]' $schema $legacyPath $currentPath 2>$null
        $LASTEXITCODE | Should Be 0
    }

    It 'contains no forbidden execution controls' {
        $content = (Get-Content -Raw (Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1')) + (Get-Content -Raw $module)
        foreach ($bad in @('Stop-Process', 'taskkill', 'danger-full-access', 'workspace-write', '--model', '--profile', '--add-dir', 'codex login', 'codex upgrade', 'resume')) {
            $content -match [regex]::Escape($bad) | Should Be $false
        }
    }
}
