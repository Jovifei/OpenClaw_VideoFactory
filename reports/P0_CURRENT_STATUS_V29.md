# Current Status V29

`PROJECT_GATEWAY_DEVICE_PAIRING_BLOCKED:PROJECT_DEVICE_IDENTITY_FILE_MISSING`

047 did not connect to the Gateway. The repaired private directory ACL is healthy, but the Project-owned official device identity is not present at the authorized state root. Since the pairing protocol requires that identity to sign the Gateway nonce, the requested one pairing connection remains unused.

The Core Gateway remains listening on 18789. Core Feishu and the Project Gateway were not changed.

