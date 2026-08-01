Describe 'P0 Shadow Feishu plugin lifecycle 033' {
    BeforeAll {
        $Root = Split-Path -Parent $PSScriptRoot
        $ResultPath = Join-Path $Root 'experiments/core_feishu_control_contract/shadow/lifecycle-result.json'
        $ReportPath = Join-Path $Root 'reports/P0_SHADOW_FEISHU_PLUGIN_LIFECYCLE_033.json'
        $Preflight = Join-Path $Root 'scripts/migration/core_feishu_control/preflight.py'
        $Postcheck = Join-Path $Root 'scripts/migration/core_feishu_control/postcheck.py'
        $Python = Join-Path $Root '.venv/Scripts/python.exe'
        if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
    }

    It 'has qualified Shadow lifecycle evidence' {
        $result = Get-Content -Raw -LiteralPath $ReportPath | ConvertFrom-Json
        $result.status | Should Be 'SHADOW_FEISHU_PLUGIN_LIFECYCLE_READY'
        $result.shadow_only | Should Be $true
        $result.execution | Should Be 'SHADOW_ONLY_NOT_PRODUCTION'
    }

    It 'keeps the target account isolated from the secondary account' {
        $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
        $result.calls.status_after_start.account_states.'shadow-secondary'.running | Should Be $false
        $result.calls.status_after_stop.account_states.'shadow-secondary'.running | Should Be $false
    }

    It 'rejects production execution' {
        foreach ($script in @($Preflight, $Postcheck)) {
            $output = & $Python $script --shadow-result $ResultPath --execute 2>&1
            $LASTEXITCODE | Should Be 2
            ($output -join "`n") | Should Match 'PRODUCTION_EXECUTION_DISABLED_033'
        }
    }
}
