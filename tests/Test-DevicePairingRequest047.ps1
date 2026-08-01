Describe 'P0 Project Gateway device pairing request 047' {
    BeforeAll {
        $Root = Split-Path -Parent $PSScriptRoot
        $Store = Get-Content -Raw -LiteralPath (Join-Path $Root 'services\feishu_gateway\openclaw_rpc_official\src\device_store.mjs')
        $Client = Get-Content -Raw -LiteralPath (Join-Path $Root 'services\feishu_gateway\openclaw_rpc_official\src\official_client.mjs')
    }

    It 'creates a durable transaction before starting the client' {
        $Store | Should Match 'prepared_not_connected'
        $Store | Should Match 'writePrivateAtomicJson'
        $Store | Should Match 'handle\.sync\(\)'
        $Client.IndexOf('createTransaction(') | Should BeLessThan $Client.IndexOf('client = new GatewayClient')
    }

    It 'limits the request to the Project identity and operator.read' {
        $Client | Should Match 'clientName: CLIENT_ID'
        $Client | Should Match 'deviceIdentity: projectIdentity'
        $Client | Should Match 'scopes: \[\.\.\.MINIMUM_SCOPES\]'
        $Client | Should Not Match 'operator\.admin'
    }

    It 'does not issue health or business RPC from the pairing branch' {
        $Client | Should Not Match 'client\.request\('
        $Client | Should Match 'pairing_preflight_failed'
        $Client | Should Match 'pairing_persistence_failed'
    }
}
