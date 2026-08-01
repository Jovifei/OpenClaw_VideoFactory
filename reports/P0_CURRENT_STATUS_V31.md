# Current Status V31

`PROJECT_GATEWAY_DEVICE_PAIRING_BLOCKED:INVALID_REQUEST`

The Project-owned official device identity is intact and the one newly authorized loopback pairing attempt completed without using a shared token. The Gateway returned `INVALID_REQUEST` with no safe structured detail code; no pairing request and no device token were created.

The result is a protocol-level blocker with an exact received code, not proof of a signature, role, scope, or device-id failure. No retry, approval, Project Gateway start, Core Feishu action, Feishu traffic, configuration change, migration, or P0 Gate action occurred.

The Project-owned identity and device-token state are external to the repository. A separate broad filename scan found four pre-existing Shadow-fixture paths under `experiments/`; their contents were not read or changed and they are not this Project identity.
