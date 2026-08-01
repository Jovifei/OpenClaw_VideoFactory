# P0 OpenClaw RPC protocol contract repair 040

Status: `RPC_PROTOCOL_CONTRACT_FIXED:RPC_TOKEN_AUTH_BLOCKED`

## Fixed contract

The Project Adapter now follows the installed OpenClaw 2026.7.1 v4 sequence:

```text
connect.challenge -> connect(role/scopes/caps) -> hello-ok -> health
```

It remains a direct-loopback `gateway-client` / `backend` client, so it does not create, store, or sign a device identity. The challenge nonce is verified only in memory and is never logged or written.

Gateway error handling now exposes only an allowlisted `error_detail_code`; it never returns the server's raw message/details or a credential.

## Evidence

| Check | Result |
| --- | --- |
| Installed OpenClaw v4 schema, synthetic values | PASS |
| Adapter unit tests | 11/11 |
| Adapter + preflight Python tests | 21/21 |
| Full Python suite | 271/271 |
| Pester 035/036 contract tests | 10/10 |
| Schema suite | 88/88 |
| Project `.venv` dependency check | PASS |

The health-only child inherited the user-level token without emitting it. The Adapter received the Gateway challenge and reached authentication. The Gateway returned `AUTH_TOKEN_MISMATCH`; health was therefore not called. Project Gateway process count remained zero, and no Core/Feishu/Binding/Agent/Cron/configuration lifecycle action occurred.

## Stop boundary

The protocol defect is repaired. Cutover remains blocked solely because the securely injected `OPENCLAW_GATEWAY_TOKEN` does not authenticate to the currently running OpenClaw Gateway. Correct or rotate that secure local injection under a separate credential-maintenance authorization; do not send a token in chat.
