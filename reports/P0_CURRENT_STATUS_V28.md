# Current Status V28

`PROJECT_GATEWAY_DEVICE_AUTH_BLOCKED:PAIRING_ATTEMPT_PERSISTENCE_FAILED_ACL_REPAIRED_REAUTHORIZATION_REQUIRED`

The shared Gateway token is no longer the Project Gateway production-preflight default. The official device-auth bridge is implemented and tested, but a fresh one-request pairing authorization is required because the earlier authorized attempt left no verifiable approval artifact before the ACL repair.

The existing OpenClaw Gateway remains running, its 18789 listener is present, Core Feishu was not changed, and the Project Gateway process count is zero.

