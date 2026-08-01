Describe 'P0 Zhongshu final cutover unblock 036' {
    BeforeAll {
        $Root = Split-Path -Parent $PSScriptRoot
        $StartScript = Join-Path $Root 'scripts/feishu_gateway/start_gateway.ps1'
        $Precheck = Join-Path $Root 'scripts/migration/final_cutover_precheck.py'
        $Python = Join-Path $Root '.venv/Scripts/python.exe'
    }

    It 'performs a command-line secret scan after a child process is created' {
        $source = Get-Content -Raw -LiteralPath $StartScript
        $source | Should Match 'Test-GatewayCommandLineSecretSafe'
        $source | Should Match 'Get-CimInstance Win32_Process'
        $source | Should Match 'gateway_command_line_credential_detected'
        $source | Should Not Match '\$launchArguments[^\r\n]*OPENCLAW_GATEWAY_TOKEN'
    }

    It 'keeps the final precheck read-only and account-bound' {
        $source = Get-Content -Raw -LiteralPath $Precheck
        $source | Should Match 'ACCOUNT = "zhongshu"'
        foreach ($forbidden in @('channels.stop', 'channels.start', 'Start-Process', 'Invoke-RestMethod', 'requests.')) {
            $source | Should Not Match [regex]::Escape($forbidden)
        }
    }

    It 'does not need an ambient token for missing-credential validation' {
        Remove-Item Env:OPENCLAW_GATEWAY_TOKEN -ErrorAction SilentlyContinue
        $output = & $StartScript -Mode production-preflight -ValidateOnly 2>&1
        $LASTEXITCODE | Should Be 2
        (($output -join "`n") | ConvertFrom-Json).status | Should Be 'RPC_CREDENTIAL_REQUIRED'
    }
}
