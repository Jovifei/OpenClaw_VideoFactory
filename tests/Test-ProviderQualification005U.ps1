$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue

function New-005UReservedWorkerState {
    param([string]$RunId = ('session_005u_worker_reservation_' + [Guid]::NewGuid().ToString('N')))

    $profile = Get-PQProfile -QualificationProfile '005T'
    $state = New-PQInitialState -Profile $profile -RunId $RunId
    $state.revision = 5
    $state.state = 'worker_started'
    $state.stage = 'worker_launch'
    $state.last_checkpoint = 'worker_started'
    $state.source_freeze_sha256 = ('a' * 64)
    $state.supervisor_pid = 1
    $state.supervisor_token_sha256 = ('b' * 64)
    $state.worker_generation = 1
    $state.worker_launch_count = 1
    $state.worker_pid = 0
    $state.worker_token_sha256 = ('c' * 64)
    $state.lease_id = ('d' * 32)
    $state.lease_expires_utc = '2026-08-12T00:00:00.0000000Z'
    Assert-PQStateSchemaTestContract -State $state | Out-Null
    return $state
}

function Move-005UTestState {
    param(
        [Parameter(Mandatory)]$State,
        [Parameter(Mandatory)][string]$StatePath,
        [Parameter(Mandatory)][string]$NewState,
        [Parameter(Mandatory)][string]$Stage,
        [hashtable]$Patch = @{},
        [object]$ErrorObject = $null
    )
    $next = Copy-PQObject -Value $State
    foreach ($key in $Patch.Keys) { $next.$key = $Patch[$key] }
    $next.state = $NewState
    $next.stage = $Stage
    $next.last_checkpoint = $NewState
    $next.revision = [int]$State.revision + 1
    $next.error = $ErrorObject
    Assert-PQStateSchemaTestContract -State $next | Out-Null
    $next | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $StatePath -Encoding UTF8
    return $next
}

function New-005USupervisorStartedState {
    param([string]$RunId = ('session_005u_identity_' + [Guid]::NewGuid().ToString('N')))
    $state = New-PQInitialState -Profile (Get-PQProfile -QualificationProfile '005T') -RunId $RunId
    $state.revision = 4
    $state.state = 'supervisor_started'
    $state.stage = 'supervisor'
    $state.last_checkpoint = 'supervisor_started'
    $state.source_freeze_sha256 = ('a' * 64)
    $state.supervisor_pid = 1
    $state.supervisor_token_sha256 = ('b' * 64)
    Assert-PQStateSchemaTestContract -State $state | Out-Null
    return $state
}

function New-005UBlockedState {
    param([Parameter(Mandatory)]$State, [Parameter(Mandatory)][string]$StatePath, [Parameter(Mandatory)]$ErrorObject)
    return Move-005UTestState -State $State -StatePath $StatePath -NewState 'blocked' -Stage 'worker_launch' -ErrorObject $ErrorObject
}

function Get-005UWorkerReservationPatch {
    return @{
        supervisor_pid = 1
        supervisor_token_sha256 = ('b' * 64)
        worker_generation = 1
        worker_launch_count = 1
        worker_pid = 0
        worker_token_sha256 = ('c' * 64)
        lease_id = ('d' * 32)
        lease_expires_utc = '2026-08-12T00:00:00.0000000Z'
    }
}

Describe 'ProviderQualification 005U worker launch fault injection' {
    function Invoke-005ULaunchCase {
        param([ValidateSet('none','throw','null','zero','cas','pid_file','ready')][string]$Failure = 'none')
        $state = New-005UReservedWorkerState -RunId ('session_005u_launch_' + [Guid]::NewGuid().ToString('N'))
        $statePath = Join-Path $TestDrive ($state.run_id + '.json')
        $tokenPath = Join-Path $TestDrive ($state.run_id + '.token')
        $case = $Failure
        $writeToken = { param($path, $content) Set-Content -LiteralPath $path -Value $content -Encoding UTF8 }.GetNewClosure()
        $startProcess = {
            if ($case -eq 'throw') { throw 'private E:\raw' }
            if ($case -eq 'null') { return $null }
            if ($case -eq 'zero') { return [pscustomobject]@{ Id = 0 } }
            return [pscustomobject]@{ Id = 41 }
        }.GetNewClosure()
        $writePidFile = {
            param($pid)
            if ($case -eq 'pid_file') { throw 'private E:\pid' }
            Set-Content -LiteralPath (Join-Path $TestDrive '005u-worker.pid') -Value ([string]$pid) -Encoding UTF8
        }.GetNewClosure()
        $promoteReady = {
            param($current, $path, $pid)
            if ($case -in @('cas','ready')) { throw 'provider_qualification_state_conflict' }
            $next = $current | ConvertTo-Json -Depth 20 | ConvertFrom-Json
            $next.worker_pid = $pid
            $next.state = 'supervisor_ready'
            $next.stage = 'supervisor'
            $next.last_checkpoint = 'supervisor_ready'
            $next.revision = [int]$current.revision + 1
            $next.error = $null
            Assert-PQStateSchemaTestContract -State $next | Out-Null
            $next | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
            return $next
        }.GetNewClosure()
        $removeToken = { param($path) if (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -Force } }.GetNewClosure()
        $removePidFile = { param($pid) Remove-Item -LiteralPath (Join-Path $TestDrive '005u-worker.pid') -Force -ErrorAction SilentlyContinue }.GetNewClosure()
        $result = Invoke-PQWorkerLaunchTransaction -State $state -StatePath $statePath -TokenFile $tokenPath -Token ('secret-' + $state.run_id) `
            -WriteToken $writeToken -StartProcess $startProcess -WritePidFile $writePidFile `
            -PromoteReady $promoteReady -RemoveToken $removeToken -RemovePidFile $removePidFile
        return [pscustomobject]@{ result = $result; state_path = $statePath; token_path = $tokenPath }
    }

    It 'persists a structured blocked snapshot when Start-PQProcess throws' {
        $run = Invoke-005ULaunchCase -Failure 'throw'
        $run.result.succeeded | Should Be $false
        $run.result.failure_reason | Should Be 'worker_start_failed'
        $blocked = New-005UBlockedState -State $run.result.state -StatePath $run.state_path -ErrorObject (Get-PQSanitizedError -Code 'WORKER_CONTRACT_FAILED' -Stage 'worker_launch' -Reason $run.result.failure_reason)
        $blocked.state | Should Be 'blocked'
        $blocked.error.code | Should Be 'WORKER_CONTRACT_FAILED'
        (Test-Path -LiteralPath $run.token_path) | Should Be $false
        (Get-Content -LiteralPath $run.state_path -Raw) | Should Not Match 'private E:\\raw'
    }

    It 'rejects a null or zero PID before readiness and cleans the token' {
        foreach ($failure in @('null', 'zero')) {
            $run = Invoke-005ULaunchCase -Failure $failure
            $run.result.succeeded | Should Be $false
            $run.result.failure_reason | Should Be 'worker_pid_invalid'
            $run.result.worker_pid | Should Be 0
            (Test-Path -LiteralPath $run.token_path) | Should Be $false
        }
    }

    It 'keeps CAS and PID persistence failures fail-closed without markers' {
        foreach ($failure in @('cas', 'pid_file', 'ready')) {
            $run = Invoke-005ULaunchCase -Failure $failure
            $run.result.succeeded | Should Be $false
            $error = Get-PQSanitizedError -Code 'WORKER_CONTRACT_FAILED' -Stage 'worker_launch' -Reason $run.result.failure_reason
            $blocked = New-005UBlockedState -State $run.result.state -StatePath $run.state_path -ErrorObject $error
            $blocked.state | Should Be 'blocked'
            $blocked.error.code | Should Be 'WORKER_CONTRACT_FAILED'
            $blocked.error.context.reason | Should Be $run.result.failure_reason
            (Test-Path -LiteralPath $run.token_path) | Should Be $false
        }
    }

    It 'completes only after positive PID persistence and supervisor_ready' {
        $run = Invoke-005ULaunchCase -Failure 'none'
        $run.result.failure_reason | Should Be $null
        $run.result.succeeded | Should Be $true
        $run.result.worker_pid | Should Be 41
        $run.result.state.state | Should Be 'supervisor_ready'
        $run.result.state.worker_pid | Should Be 41
        (Test-Path -LiteralPath $run.token_path) | Should Be $true
    }
}

Describe 'ProviderQualification 005U worker reservation state contract' {
    It 'accepts the fully-bound in-memory reservation contract' {
        $state = New-005UReservedWorkerState
        { Assert-PQStateSchemaTestContract -State $state } | Should Not Throw
    }

    It 'accepts a fully-bound worker_started reservation before the process has a PID' {
        $state = New-005UReservedWorkerState

        $state.state | Should Be 'worker_started'
        $state.worker_pid | Should Be 0
        $state.worker_generation | Should Be 1
        $state.worker_launch_count | Should Be 1
        $state.smoke.attempt_count | Should Be 0
        $state.acceptance.attempt_count | Should Be 0
        { Assert-PQStateSchemaTestContract -State $state } | Should Not Throw
    }

    It 'keeps all reservation bindings mandatory when worker_started has no PID' {
        $state = New-005UReservedWorkerState

        $missingGeneration = Copy-PQObject -Value $state
        $missingGeneration.worker_generation = 0
        { Assert-PQStateSchemaTestContract -State $missingGeneration } | Should Throw

        $mismatchedGeneration = Copy-PQObject -Value $state
        $mismatchedGeneration.worker_launch_count = 2
        { Assert-PQStateSchemaTestContract -State $mismatchedGeneration } | Should Throw

        $missingSupervisor = Copy-PQObject -Value $state
        $missingSupervisor.supervisor_pid = 0
        { Assert-PQStateSchemaTestContract -State $missingSupervisor } | Should Throw

        $missingWorkerToken = Copy-PQObject -Value $state
        $missingWorkerToken.worker_token_sha256 = $null
        { Assert-PQStateSchemaTestContract -State $missingWorkerToken } | Should Throw

        $missingLease = Copy-PQObject -Value $state
        $missingLease.lease_id = $null
        { Assert-PQStateSchemaTestContract -State $missingLease } | Should Throw

        $missingExpiry = Copy-PQObject -Value $state
        $missingExpiry.lease_expires_utc = $null
        { Assert-PQStateSchemaTestContract -State $missingExpiry } | Should Throw

        $unexpectedPid = Copy-PQObject -Value $state
        $unexpectedPid.worker_pid = 41
        { Assert-PQStateSchemaTestContract -State $unexpectedPid } | Should Throw
    }

    It 'requires a persisted positive Worker PID after worker_started' {
        $state = New-005UReservedWorkerState

        $supervisorReady = Copy-PQObject -Value $state
        $supervisorReady.state = 'supervisor_ready'
        { Assert-PQStateSchemaTestContract -State $supervisorReady } | Should Throw

        $workerArmed = Copy-PQObject -Value $state
        $workerArmed.state = 'worker_armed'
        { Assert-PQStateSchemaTestContract -State $workerArmed } | Should Throw
    }

    It 'allows supervisor_ready only after the Worker PID is atomically persisted' {
        $state = New-005UReservedWorkerState
        $path = Join-Path $TestDrive 'reservation-pid-persisted.json'
        $ready = Move-005UTestState -State $state -StatePath $path -NewState 'supervisor_ready' -Stage 'test' -Patch @{ worker_pid = 41 }
        $ready.state | Should Be 'supervisor_ready'
        $ready.worker_pid | Should Be 41
        { Assert-PQStateSchemaTestContract -State $ready } | Should Not Throw
    }

    It 'keeps the 005T one-generation ceiling and one-shot ledgers intact' {
        $state = New-005UReservedWorkerState

        $secondGeneration = Copy-PQObject -Value $state
        $secondGeneration.worker_generation = 2
        $secondGeneration.worker_launch_count = 2
        { Assert-PQStateSchemaTestContract -State $secondGeneration } | Should Throw

        $state.smoke.status | Should Be 'not_started'
        $state.smoke.attempt_count | Should Be 0
        $state.acceptance.status | Should Be 'not_started'
        $state.acceptance.attempt_count | Should Be 0
    }

    It 'rejects stale writers and run identity conflicts around the reservation transition' {
        $profile = Get-PQProfile -QualificationProfile '005T'
        $current = New-005USupervisorStartedState -RunId 'session_005u_conflict'
        Assert-PQStateIdentity -State $current -Profile $profile -RunId 'session_005u_conflict'
        $wrongRun = Copy-PQObject -Value $current
        $wrongRun.run_id = 'session_005u_other'
        { Assert-PQStateIdentity -State $wrongRun -Profile $profile -RunId 'session_005u_conflict' } | Should Throw
    }
}
