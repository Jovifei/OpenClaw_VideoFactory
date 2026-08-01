Describe 'P0 Zhongshu cutover preflight unblock 035' {
    BeforeAll {
        $Root = Split-Path -Parent $PSScriptRoot
        $StartScript = Join-Path $Root 'scripts/feishu_gateway/start_gateway.ps1'
        $StatusScript = Join-Path $Root 'scripts/feishu_gateway/status_gateway.ps1'
        $Observer = Join-Path $Root 'scripts/migration/inspect_core_feishu_runtime.py'
    }

    It 'keeps missing RPC credentials unready without starting a process' {
        Remove-Item Env:OPENCLAW_GATEWAY_TOKEN -ErrorAction SilentlyContinue
        $output = & $StartScript -Mode production-preflight -ValidateOnly 2>&1
        $LASTEXITCODE | Should Be 2
        $result = ($output -join "`n") | ConvertFrom-Json
        $result.running | Should Be $false
        $result.ready | Should Be $false
        $result.status | Should Be 'RPC_CREDENTIAL_REQUIRED'
    }

    It 'accepts an inherited credential reference without exposing its value' {
        $fixtureValue = 'fixture-credential-value'
        $env:OPENCLAW_GATEWAY_TOKEN = $fixtureValue
        $output = & $StartScript -Mode production-preflight -ValidateOnly 2>&1
        $LASTEXITCODE | Should Be 0
        ($output -join "`n") | Should Not Match $fixtureValue
        (($output -join "`n") | ConvertFrom-Json).credential_present | Should Be $true
    }

    It 'guards production mode before any process is started' {
        $output = & $StartScript -Mode production -ValidateOnly 2>&1
        $LASTEXITCODE | Should Be 2
        $result = ($output -join "`n") | ConvertFrom-Json
        $result.running | Should Be $false
        $result.status | Should Be 'production_transport_unavailable'
    }

    It 'never places the RPC token in the launch argument list' {
        $source = Get-Content -Raw -LiteralPath $StartScript
        $launchBlock = [regex]::Match(
            $source,
            '(?s)\$launchArguments\s*=\s*@\(.*?\)\s*\r?\n\$process'
        ).Value
        $launchBlock | Should Not BeNullOrEmpty
        $launchBlock | Should Not Match 'OPENCLAW_GATEWAY_TOKEN'
        $launchBlock | Should Not Match '(?i)--token|--password|--secret'
    }

    It 'keeps the runtime observer read-only' {
        $source = Get-Content -Raw -LiteralPath $Observer
        $source | Should Match 'channels\.status'
        $source | Should Not Match 'channels\.stop'
        $source | Should Not Match 'channels\.start'
        $source | Should Not Match '(?i)config\s+(set|unset)|agents\s+bind|agents\s+unbind'
    }

    It 'reports mode readiness and RPC state from status' {
        $source = Get-Content -Raw -LiteralPath $StatusScript
        foreach ($field in @('ready', 'mode', 'feishu_connection', 'openclaw_rpc')) {
            $source | Should Match $field
        }
    }

    It 'inspects the child command line without retaining a credential value' {
        $source = Get-Content -Raw -LiteralPath $StartScript
        $source | Should Match 'Get-CimInstance Win32_Process'
        $source | Should Match 'gateway_command_line_credential_detected'
        $source | Should Not Match '\$OriginalToken|\$HadToken'
    }
}
