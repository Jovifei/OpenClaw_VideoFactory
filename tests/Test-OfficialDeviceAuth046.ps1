Describe 'P0 Project Gateway official device auth 046' {
    BeforeAll {
        $Root = Split-Path -Parent $PSScriptRoot
        $OfficialClient = Join-Path $Root 'services/feishu_gateway/openclaw_rpc_official/src/official_client.mjs'
        $Contract = Join-Path $Root 'services/feishu_gateway/openclaw_rpc_official/src/bridge_contract.mjs'
        $PythonBridge = Join-Path $Root 'services/feishu_gateway/official_rpc_bridge.py'
        $Runtime = Join-Path $Root 'services/feishu_gateway/runtime_server.py'
    }

    It 'uses the installed official device client with the minimum operator scope' {
        $source = Get-Content -Raw -LiteralPath $OfficialClient
        $contract = Get-Content -Raw -LiteralPath $Contract
        $source | Should Match 'GatewayClient'
        $source | Should Match 'MINIMUM_SCOPES'
        $contract | Should Match 'operator\.read'
        $source | Should Not Match 'operator\.admin'
        $source | Should Match 'delete process\.env\.OPENCLAW_GATEWAY_TOKEN'
    }

    It 'keeps Python out of private device state and requires local IPC session authentication' {
        $python = Get-Content -Raw -LiteralPath $PythonBridge
        $python | Should Match 'VIDEO_FACTORY_BRIDGE_SESSION'
        $python | Should Not Match 'device\.json'
        $python | Should Not Match 'device-auth\.json'
    }

    It 'disables the legacy shared-token adapter as the runtime default' {
        $runtime = Get-Content -Raw -LiteralPath $Runtime
        $runtime | Should Match 'legacy_shared_token_adapter_disabled'
        $runtime | Should Match 'official_rpc_bridge'
        $runtime | Should Not Match 'openclaw_rpc\.client import'
        (Get-Content -Raw -LiteralPath $Contract) | Should Match 'bridge_method_forbidden'
    }
}
