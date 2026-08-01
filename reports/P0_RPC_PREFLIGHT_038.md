# P0 Zhongshu RPC Preflight 038

Captured read-only on 2026-07-26 (Asia/Shanghai). This preflight did not
start a listener, start the Project Gateway, connect to Feishu, or control the
Core Feishu consumer.

## Terminal status

`RPC_PREFLIGHT_FAILED:RPC_AUTH_FAILED`

## Credential-safe result

The secure user environment entry is present. The already-running Codex
process had not inherited it, so a one-time preflight child inherited that
entry for this probe only. No credential value, length, prefix, suffix, digest,
or other derived metadata was displayed, persisted, or logged.

## RPC production-preflight result

The verified path was the Project Gateway `production-preflight` RPC probe,
not offline mode. It invoked the existing authenticate-and-health contract
without starting an HTTP listener or a Feishu transport. Its sanitized result
was:

| Check | Result |
|---|---|
| RPC endpoint available | true |
| Authentication successful | false |
| Session ready | false |
| Error mapping | `RPC_AUTH_FAILED` |
| Project Gateway processes | 0 |

The RPC adapter received a usable credential and reached the endpoint, but the
Gateway rejected its connect request with the sanitized Adapter status
`rpc_bad_request` / `INVALID_REQUEST`. Authentication and session therefore
remain false rather than inferred. The existing preflight contract maps that
failure to `RPC_AUTH_FAILED`.

This result does **not** prove the Token is wrong: the Gateway reported an
invalid request before an authentication outcome. A separate, code-authorized
RPC Adapter protocol-contract repair is required before another live
preflight; this task does not modify the Adapter or enter T0.

## Read-only maintenance baseline

| Check | Result |
|---|---|
| Rollback artifacts present | 10, including the Zhongshu rollback plan |
| OpenClaw configuration SHA-256 | `D6A97F1025698C08F086C1EE565E1AAC1AD30116037E4F135688EDBB1171BE8C` |
| Git status | 41 untracked; 0 staged; 0 modified |
| Scoped secret-pattern candidate files | 0 |
| Project Gateway status file | absent |

## Verification

- The runtime contract distinguishes `production-preflight` from `offline`.
  The former has `not_started_preflight`; offline uses `fake_transport`.
- Focused Python contract tests passed: 30/30.
- No lifecycle, configuration, Binding, Agent, Cron, Feishu, commit, or push
  action was performed.
