$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue

function New-005U1ReservedWorkerState {
    param([string]$RunId = ('session_005u1_marker_' + [Guid]::NewGuid().ToString('N')))

    $profile = Get-PQProfile -QualificationProfile '005T'
    $state = New-PQInitialState -Profile $profile -RunId $RunId
    $state.revision = 5
    $state.state = 'worker_started'
    $state.stage = 'worker_launch'
    $state.last_checkpoint = 'worker_started'
    $state.source_freeze_sha256 = ('a' * 64)
    $state.supervisor_pid = 97
    $state.supervisor_token_sha256 = ('b' * 64)
    $state.worker_generation = 1
    $state.worker_launch_count = 1
    $state.worker_pid = 0
    $state.worker_token_sha256 = ('c' * 64)
    $state.lease_id = ('d' * 32)
    $state.lease_expires_utc = '2026-08-13T00:00:00.0000000Z'
    Assert-PQStateSchemaTestContract -State $state | Out-Null
    $path = Join-Path $TestDrive ($RunId + '.json')
    $state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
    return [pscustomobject]@{ state = $state; state_path = $path }
}

function Get-005U1MarkerPaths {
    param([Parameter(Mandatory)][string]$RunRoot)
    return [ordered]@{
        supervisor = Join-Path $RunRoot 'SUPERVISOR_READY.txt'
        worker = Join-Path $RunRoot 'WORKER_READY.txt'
        live = Join-Path $RunRoot 'LIVE_WORKER_ARMED.txt'
        close = Join-Path $RunRoot 'CLOSE_CODEX_DESKTOP_NOW.txt'
    }
}

function Assert-005U1ExactMarkerSet {
    param(
        [Parameter(Mandatory)][string]$RunRoot,
        [string[]]$Expected = @()
    )
    $paths = Get-005U1MarkerPaths -RunRoot $RunRoot
    foreach ($name in $paths.Keys) {
        (Test-Path -LiteralPath $paths[$name] -PathType Leaf) | Should Be ($Expected -contains $name)
    }
}

function Invoke-005U1ProductionStartupSeam {
    param(
        [ValidateSet('none','token','start_throw','start_null','start_zero','pid_persist','pid_file','ready_promote','supervisor_marker','worker_died','worker_missing','worker_malformed','arm','live','close','block')]
        [string]$Failure = 'none'
    )

    $reserved = New-005U1ReservedWorkerState
    $state = $reserved.state
    $statePath = $reserved.state_path
    $runRoot = Join-Path $TestDrive $state.run_id
    New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
    $paths = Get-005U1MarkerPaths -RunRoot $runRoot
    $tokenPath = Join-Path $runRoot 'worker.token'
    $workerPidPath = Join-Path $runRoot 'worker.pid'
    $markerOrder = New-Object System.Collections.ArrayList
    $case = $Failure

    $writeToken = {
        param($path, $content)
        if ($case -eq 'token') { throw 'private E:\\token' }
        Set-Content -LiteralPath $path -Value $content -Encoding UTF8
    }.GetNewClosure()
    $startProcess = {
        if ($case -in @('start_throw','block')) { throw 'private E:\\process' }
        if ($case -eq 'start_null') { return $null }
        if ($case -eq 'start_zero') { return [pscustomobject]@{ Id = 0 } }
        return [pscustomobject]@{ Id = 41 }
    }.GetNewClosure()
    $writePidFile = {
        param($pid)
        if ($case -eq 'pid_file') { throw 'private E:\\pid' }
        Set-Content -LiteralPath $workerPidPath -Value ([string]$pid) -Encoding UTF8
    }.GetNewClosure()
    $promoteReady = {
        param($current, $path, $pid)
        if ($case -in @('pid_persist','ready_promote')) { throw 'provider_qualification_state_schema_invalid' }
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
    $removeToken = {
        param($path)
        if (Test-Path -LiteralPath $path -PathType Leaf) { Remove-Item -LiteralPath $path -Force }
    }.GetNewClosure()
    $removePidFile = {
        param($pid)
        Remove-Item -LiteralPath $workerPidPath -Force -ErrorAction SilentlyContinue
    }.GetNewClosure()
    $writeMarker = {
        param($root, $name, $content)
        if ($case -eq 'supervisor_marker' -and $name -eq 'SUPERVISOR_READY.txt') { throw 'private E:\\supervisor' }
        if ($case -eq 'live' -and $name -eq 'LIVE_WORKER_ARMED.txt') { throw 'private E:\\live' }
        if ($case -eq 'close' -and $name -eq 'CLOSE_CODEX_DESKTOP_NOW.txt') { throw 'private E:\\close' }
        Set-Content -LiteralPath (Join-Path $root $name) -Value $content -Encoding UTF8
        [void]$markerOrder.Add($name)
        return (Join-Path $root $name)
    }.GetNewClosure()
    $waitForWorkerReady = {
        param($current, $worker, $root, $runId, $generation, $lease)
        if ($case -eq 'worker_died') { return [pscustomobject]@{ ready = $false; code = 'BLOCKED_DETACHED_WORKER_DIED'; reason = 'worker_died_before_ready' } }
        if ($case -eq 'worker_missing') { return [pscustomobject]@{ ready = $false; code = 'BLOCKED_WORKER_NOT_ARMED'; reason = 'handshake_missing' } }
        if ($case -eq 'worker_malformed') {
            Set-Content -LiteralPath (Join-Path $root 'WORKER_READY.txt') -Value 'worker_ready:malformed' -Encoding UTF8
            return [pscustomobject]@{ ready = $false; code = 'BLOCKED_WORKER_NOT_ARMED'; reason = 'handshake_invalid' }
        }
        Publish-PQWorkerReadyMarker -State $current -RunRoot $root -RunId $runId -WorkerPid ([int]$worker.Id) -WriteMarker $writeMarker | Out-Null
        return [pscustomobject]@{ ready = $true; code = $null; reason = $null }
    }.GetNewClosure()
    $armWorker = {
        param($current, $path)
        if ($case -eq 'arm') { throw 'provider_qualification_state_conflict' }
        $next = $current | ConvertTo-Json -Depth 20 | ConvertFrom-Json
        $next.state = 'worker_armed'
        $next.stage = 'worker_armed'
        $next.last_checkpoint = 'worker_armed'
        $next.revision = [int]$current.revision + 1
        $next.error = $null
        Assert-PQStateSchemaTestContract -State $next | Out-Null
        $next | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
        return $next
    }.GetNewClosure()
    $blockState = {
        param($current, $path, $error)
        if ($case -eq 'block') { throw 'private E:\\blocked' }
        if (@('completed','failed','blocked') -contains [string]$current.state) { return $current }
        $next = $current | ConvertTo-Json -Depth 20 | ConvertFrom-Json
        $next.state = 'blocked'
        $next.stage = 'supervisor'
        $next.last_checkpoint = 'blocked'
        $next.revision = [int]$current.revision + 1
        $next.error = $error
        Assert-PQStateSchemaTestContract -State $next | Out-Null
        $next | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
        return $next
    }.GetNewClosure()

    $result = Invoke-PQSupervisorWorkerStartup -State $state -StatePath $statePath -TokenFile $tokenPath -Token ('secret-' + $state.run_id) `
        -RunRoot $runRoot -RunId $state.run_id -SupervisorPid 97 `
        -WriteToken $writeToken -StartProcess $startProcess -WritePidFile $writePidFile `
        -PromoteReady $promoteReady -RemoveToken $removeToken -RemovePidFile $removePidFile -WriteMarker $writeMarker `
        -WaitForWorkerReady $waitForWorkerReady -ArmWorker $armWorker -BlockState $blockState
    return [pscustomobject]@{
        result = $result
        run_root = $runRoot
        marker_paths = $paths
        token_path = $tokenPath
        state_path = $statePath
        marker_order = @($markerOrder)
    }
}

Describe 'ProviderQualification 005U1 production marker integration seam' {
    It 'uses the shared production seam from Supervisor and the production Worker-ready publisher' {
        $scriptPath = Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1'
        $source = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8
        $supervisorStart = $source.IndexOf('function Invoke-PQSupervisor {', [System.StringComparison]::Ordinal)
        $workerStart = $source.IndexOf('function Invoke-PQWorker {', [System.StringComparison]::Ordinal)
        $rehearsalStart = $source.IndexOf('function Start-PQRehearsal {', [System.StringComparison]::Ordinal)
        $supervisorStart | Should BeGreaterThan -1
        $workerStart | Should BeGreaterThan $supervisorStart
        $rehearsalStart | Should BeGreaterThan $workerStart
        $supervisorBody = $source.Substring($supervisorStart, $workerStart - $supervisorStart)
        $workerBody = $source.Substring($workerStart, $rehearsalStart - $workerStart)
        $supervisorBody | Should Match 'Invoke-PQSupervisorWorkerStartup'
        $supervisorBody | Should Not Match 'Invoke-PQWorkerLaunchTransaction -State \$state'
        $supervisorBody | Should Match 'Write-PQRunMarker -RunRoot \$runRoot -Name \$name -Content \$content'
        $workerBody | Should Match 'Publish-PQWorkerReadyMarker'
        $workerBody | Should Match 'Write-PQRunMarker -RunRoot \$runRoot -Name \$name -Content \$content'
    }

    It 'writes all four exact production markers in order on the positive control path' {
        $run = Invoke-005U1ProductionStartupSeam -Failure 'none'
        $run.result.succeeded | Should Be $true
        $run.result.state.state | Should Be 'worker_armed'
        Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @('supervisor','worker','live','close')
        (Get-Content -LiteralPath $run.marker_paths.supervisor -Raw).Trim() | Should Be ('supervisor_ready:' + $run.result.state.run_id)
        (Get-Content -LiteralPath $run.marker_paths.worker -Raw).Trim() | Should Be ('worker_ready:' + $run.result.state.run_id + ':1:' + ('d' * 32) + ':41')
        (Get-Content -LiteralPath $run.marker_paths.live -Raw).Trim() | Should Be ('worker_armed:' + $run.result.state.run_id + ':1:' + ('d' * 32) + ':41:97')
        (Get-Content -LiteralPath $run.marker_paths.close -Raw).Trim() | Should Be ('close_desktop_now:' + $run.result.state.run_id + ':1:' + ('d' * 32) + ':41:97')
        ($run.marker_order -join ',') | Should Be 'SUPERVISOR_READY.txt,WORKER_READY.txt,LIVE_WORKER_ARMED.txt,CLOSE_CODEX_DESKTOP_NOW.txt'
        (Test-Path -LiteralPath $run.token_path) | Should Be $true
    }

    It 'leaves no production markers for pre-ready launch failures and cleans the token' {
        foreach ($failure in @('token','start_throw','start_null','start_zero','pid_persist','pid_file','ready_promote')) {
            $run = Invoke-005U1ProductionStartupSeam -Failure $failure
            $run.result.succeeded | Should Be $false
            Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @()
            (Test-Path -LiteralPath $run.token_path) | Should Be $false
            $run.result.state.state | Should Be 'blocked'
            (Get-Content -LiteralPath $run.state_path -Raw) | Should Not Match 'private E:\\'
        }
    }

    It 'keeps only the supervisor marker when Worker dies or does not produce a ready marker' {
        foreach ($failure in @('worker_died','worker_missing')) {
            $run = Invoke-005U1ProductionStartupSeam -Failure $failure
            $run.result.succeeded | Should Be $false
            Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @('supervisor')
            $run.result.state.state | Should Be 'blocked'
            (Test-Path -LiteralPath $run.token_path) | Should Be $false
        }
    }

    It 'does not publish any downstream marker when the supervisor-ready marker write fails' {
        $run = Invoke-005U1ProductionStartupSeam -Failure 'supervisor_marker'
        $run.result.succeeded | Should Be $false
        Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @()
        $run.result.state.state | Should Be 'blocked'
        (Test-Path -LiteralPath $run.token_path) | Should Be $false
        (Get-Content -LiteralPath $run.state_path -Raw) | Should Not Match 'private E:\\supervisor'
    }

    It 'never arms a Worker after a malformed external WORKER_READY marker' {
        $run = Invoke-005U1ProductionStartupSeam -Failure 'worker_malformed'
        $run.result.succeeded | Should Be $false
        Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @('supervisor','worker')
        (Get-Content -LiteralPath $run.marker_paths.worker -Raw).Trim() | Should Be 'worker_ready:malformed'
        $run.result.state.state | Should Be 'blocked'
        (Test-Path -LiteralPath $run.token_path) | Should Be $false
    }

    It 'does not publish live or close markers when the worker_armed transition fails' {
        $run = Invoke-005U1ProductionStartupSeam -Failure 'arm'
        $run.result.succeeded | Should Be $false
        Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @('supervisor','worker')
        $run.result.state.state | Should Be 'blocked'
        (Test-Path -LiteralPath $run.token_path) | Should Be $false
        (Get-Content -LiteralPath $run.state_path -Raw) | Should Not Match 'private E:\\'
    }

    It 'does not publish downstream markers when the live or close marker write fails' {
        $live = Invoke-005U1ProductionStartupSeam -Failure 'live'
        $live.result.succeeded | Should Be $false
        Assert-005U1ExactMarkerSet -RunRoot $live.run_root -Expected @('supervisor','worker')
        $live.result.state.state | Should Be 'blocked'
        (Get-Content -LiteralPath $live.state_path -Raw) | Should Not Match 'private E:\\live'

        $close = Invoke-005U1ProductionStartupSeam -Failure 'close'
        $close.result.succeeded | Should Be $false
        Assert-005U1ExactMarkerSet -RunRoot $close.run_root -Expected @('supervisor','worker','live')
        $close.result.state.state | Should Be 'blocked'
        (Get-Content -LiteralPath $close.state_path -Raw) | Should Not Match 'private E:\\close'
    }

    It 'returns a fail-closed result when blocked snapshot persistence itself fails' {
        $run = Invoke-005U1ProductionStartupSeam -Failure 'block'
        $run.result.succeeded | Should Be $false
        $run.result.blocked_persisted | Should Be $false
        $run.result.failure_reason | Should Be 'blocked_state_persist_failed'
        Assert-005U1ExactMarkerSet -RunRoot $run.run_root -Expected @()
    }
}

Describe 'ProviderQualification 005U1 Worker-ready publisher' {
    It 'rejects an unready state or a mismatched PID before it writes the exact production leaf' {
        $reserved = New-005U1ReservedWorkerState
        $root = Join-Path $TestDrive 'publisher'
        New-Item -ItemType Directory -Path $root -Force | Out-Null
        $writer = { param($runRoot, $name, $content) Set-Content -LiteralPath (Join-Path $runRoot $name) -Value $content -Encoding UTF8 }.GetNewClosure()

        { Publish-PQWorkerReadyMarker -State $reserved.state -RunRoot $root -RunId $reserved.state.run_id -WorkerPid 41 -WriteMarker $writer } | Should Throw
        (Test-Path -LiteralPath (Join-Path $root 'WORKER_READY.txt')) | Should Be $false

        $ready = Copy-PQObject -Value $reserved.state
        $ready.worker_pid = 41
        $ready.state = 'supervisor_ready'
        $ready.stage = 'test'
        $ready.last_checkpoint = 'supervisor_ready'
        $ready.revision = [int]$reserved.state.revision + 1
        Assert-PQStateSchemaTestContract -State $ready | Out-Null
        { Publish-PQWorkerReadyMarker -State $ready -RunRoot $root -RunId $ready.run_id -WorkerPid 42 -WriteMarker $writer } | Should Throw
        (Test-Path -LiteralPath (Join-Path $root 'WORKER_READY.txt')) | Should Be $false
    }
}
