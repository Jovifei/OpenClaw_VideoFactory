$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification005R.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue

Describe 'ProviderQualification005R state contract' {
    It 'increments revision and writes atomically' {
        $state = New-InitialState 'session_test_1'
        $path = Join-Path $TestDrive 'state.json'
        $state = Write-RunState $state $path 'waiting_for_desktop_exit' 'desktop_wait' @{} $null
        $state.revision | Should Be 2
        (Get-Content -Raw $path | ConvertFrom-Json).state | Should Be 'waiting_for_desktop_exit'
    }

    It 'rejects skipped transitions and terminal reopen' {
        $state = New-InitialState 'session_test_2'
        { Write-RunState $state (Join-Path $TestDrive 'state.json') 'cache_stable' 'cache' @{} $null } | Should Throw
        $state = Write-RunState $state (Join-Path $TestDrive 'state2.json') 'blocked' 'preflight' @{} (Get-SanitizedError 'X' 'preflight' 'test')
        { Write-RunState $state (Join-Path $TestDrive 'state2.json') 'prepared' 'preflight' @{} $null } | Should Throw
    }

    It 'rejects repeated smoke and acceptance attempts' {
        $state = New-InitialState 'session_test_3'
        $p = Join-Path $TestDrive 'state3.json'
        $state = Write-RunState $state $p 'waiting_for_desktop_exit' 'wait' @{smoke_attempted=$false;acceptance_attempted=$false} $null
        $state = Write-RunState $state $p 'desktop_quiescent' 'wait' @{} $null
        $state = Write-RunState $state $p 'cache_stable' 'cache' @{} $null
        $state = Write-RunState $state $p 'cache_quarantined' 'cache' @{} $null
        $state = Write-RunState $state $p 'smoke_started' 'smoke' @{smoke_attempted=$true} $null
        { Write-RunState $state $p 'smoke_started' 'smoke' @{smoke_attempted=$true} $null } | Should Throw
    }

    It 'allows the verified success chain and keeps one-shot flags true' {
        $state = New-InitialState 'session_success_chain'
        $p = Join-Path $TestDrive 'success-state.json'
        foreach($step in @(
            @('waiting_for_desktop_exit','wait',@{}),
            @('desktop_quiescent','wait',@{desktop_quiescent=$true}),
            @('cache_stable','cache',@{original_cache_sha256=('a'*64)}),
            @('cache_quarantined','cache',@{}),
            @('smoke_started','smoke',@{smoke_attempted=$true}),
            @('smoke_passed','smoke',@{active_cache_sha256=('b'*64)}),
            @('acceptance_started','acceptance',@{acceptance_attempted=$true}),
            @('acceptance_passed','acceptance',@{}),
            @('verification_passed','verification',@{}),
            @('complete_pending_review','review',@{}),
            @('completed','review',@{})
        )) { $state=Write-RunState $state $p $step[0] $step[1] $step[2] $null }
        $state.revision | Should Be 12
        $state.smoke_attempted | Should Be $true
        $state.acceptance_attempted | Should Be $true
        $state.state | Should Be 'completed'
        { Write-RunState $state $p 'completed' 'review' @{smoke_attempted=$false} $null } | Should Throw
    }

    It 'writes a heartbeat without absolute paths or raw output' {
        $path=Join-Path $TestDrive 'heartbeat.json'
        Write-Heartbeat -Path $path -Stage 'smoke_started' -State 'running'
        $heartbeat=Get-Content -Raw $path | ConvertFrom-Json
        $heartbeat.stage | Should Be 'smoke_started'
        (Get-Content -Raw $path) -match 'E:\\' | Should Be $false
    }
}

Describe 'ProviderQualification005R cache safety' {
    It 'projects a valid test cache without exposing model content' {
        $cache = Join-Path $TestDrive 'models_cache.json'
        $models = @(1..9 | ForEach-Object { [ordered]@{ model_index=$_ } })
        [ordered]@{ models=$models } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $cache -Encoding UTF8
        $sample = Get-CacheSnapshot $cache
        $sample.json_valid | Should Be $true
        $sample.model_count | Should Be 9
        $sample.missing_base_instructions_count | Should Be 9
        $sample.PSObject.Properties.Name -contains 'model_index' | Should Be $false
    }

    It 'rejects any cache path other than the exact target' {
        { Assert-ExactCachePath (Join-Path $TestDrive 'models_cache.json') } | Should Throw
    }

    It 'does not move a cache when hash samples drift' {
        $cache = Join-Path $TestDrive 'models_cache.json'
        [ordered]@{models=@()} | ConvertTo-Json | Set-Content -LiteralPath $cache -Encoding UTF8
        $first = Get-CacheSnapshot $cache
        Add-Content -LiteralPath $cache -Value ' ' -Encoding UTF8
        $second = Get-CacheSnapshot $cache
        ($first.sha256 -eq $second.sha256) | Should Be $false
    }

    It 'rejects external path traversal and absolute replacement' {
        $root=Join-Path $TestDrive 'run-root'; New-Item -ItemType Directory -Path $root | Out-Null
        { Assert-ExternalPath (Join-Path $root '..\outside') $root } | Should Throw
        { Assert-ExternalPath 'C:\outside\state.json' $root } | Should Throw
    }

}

Describe 'ProviderQualification005R schema and sanitization' {
    It 'requires structured context for blocked errors' {
        $schema=Join-Path $PSScriptRoot '..\schemas\ops\provider_qualification_run.schema.json'
        $sample=[ordered]@{schema_version='1.0';task_id='AI-DIRECTOR-PHASE2-DESKTOP-DETACHED-PROVIDER-QUALIFICATION-005R';run_id='session_schema';revision=1;state='blocked';stage='smoke';desktop_quiescent=$false;original_cache_sha256=$null;active_cache_sha256=$null;smoke_attempted=$true;acceptance_attempted=$false;artifacts=@();error=[ordered]@{code='X';message='safe';context=[ordered]@{stage='smoke';reason='safe'}}}
        $path=Join-Path $TestDrive 'schema-state.json'; $sample | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
        & 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe' -c 'import json,sys,jsonschema; jsonschema.validate(json.load(open(sys.argv[1],encoding=''utf-8-sig'')),json.load(open(sys.argv[2],encoding=''utf-8-sig'')))' $path $schema 2>$null
        $LASTEXITCODE | Should Be 0
    }

    It 'rejects a blocked state with null error' {
        $schema=Join-Path $PSScriptRoot '..\schemas\ops\provider_qualification_run.schema.json'
        $sample=[ordered]@{schema_version='1.0';task_id='AI-DIRECTOR-PHASE2-DESKTOP-DETACHED-PROVIDER-QUALIFICATION-005R';run_id='session_schema_null';revision=1;state='blocked';stage='smoke';desktop_quiescent=$false;original_cache_sha256=$null;active_cache_sha256=$null;smoke_attempted=$false;acceptance_attempted=$false;artifacts=@();error=$null}
        $path=Join-Path $TestDrive 'schema-state-null.json'; $sample | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
        $priorPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $ignored = & 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe' -c 'import json,sys,jsonschema; jsonschema.validate(json.load(open(sys.argv[1],encoding=''utf-8-sig'')),json.load(open(sys.argv[2],encoding=''utf-8-sig'')))' $path $schema 2>&1
            $exitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $priorPreference
        }
        $exitCode | Should Not Be 0
    }
}

Describe 'ProviderQualification005R forbidden surface scan' {
    It 'contains no process termination or privileged provider controls' {
        $content = (Get-Content -Raw (Join-Path $PSScriptRoot '..\scripts\provider_qualification_005r.ps1')) + (Get-Content -Raw $module)
        foreach($bad in @('Stop-Process','taskkill','danger-full-access','workspace-write','--model','--profile','--add-dir','codex login','codex upgrade')) { $content -match [regex]::Escape($bad) | Should Be $false }
    }
}
