Describe 'P0 Project Gateway device identity initialization 048' {
    BeforeAll {
        $Root = Split-Path -Parent $PSScriptRoot
        $Store = Get-Content -Raw -LiteralPath (Join-Path $Root 'services\feishu_gateway\openclaw_rpc_official\src\device_store.mjs')
        $Initializer = Get-Content -Raw -LiteralPath (Join-Path $Root 'services\feishu_gateway\openclaw_rpc_official\src\identity_initializer.mjs')
    }

    It 'uses the official OpenClaw v1 generator and never starts a client' {
        $Initializer | Should Match 'loadOrCreate'
        $Initializer | Should Match 'loadIfPresent'
        $Initializer | Should Match 'validateOfflineIdentity'
        $Initializer | Should Not Match 'client\.start\('
        $Initializer | Should Not Match 'new WebSocket'
    }

    It 'requires current user plus SYSTEM ACL and atomic private writes' {
        $Store | Should Match 'S-1-5-18'
        $Store | Should Match 'current_user_and_system'
        $Store | Should Match 'handle\.sync\(\)'
        $Initializer | Should Match 'writePrivateAtomicJson'
    }

    It 'keeps pairing and token state absent during initialization' {
        $Initializer | Should Match 'pairing_status: "not_requested"'
        $Initializer | Should Match 'device_token_present: false'
        $Initializer | Should Not Match 'OPENCLAW_GATEWAY_TOKEN'
    }
}
