# P0 Feishu Gateway ↔ OpenClaw Gateway RPC contract (P0 offline proof)

Scope: `services/feishu_gateway/*` and `tests/test_feishu_gateway_*`

## Contract owner and transport

- Preferred transport remains the official OpenClaw Gateway RPC surface exposed by OpenClaw.
- In this phase, RPC is exercised through injectable `rpc(...)` call points for offline proof only.
- The local implementation intentionally avoids inventing OpenClaw session semantics and only emits a deterministic payload.

## Request

| Item | Value |
| --- | --- |
| Method | `agent` |
| Session key | `feishu:group:{chat_id}` |
| Sender identity | `sender_id` |
| Payload fields | `agent_id`, `session_key`, `message_id`, `chat_id`, `sender_id`, `text` |
| Mandatory builder | `GatewayPayloadBuilder.for_text(event)` |

## Example

```json
{
  "agent_id": "video-factory",
  "session_key": "feishu:group:oc_xxx",
  "message_id": "om_xxx",
  "chat_id": "oc_xxx",
  "sender_id": "ou_xxx",
  "text": "hello"
}
```

## Timeout and retry

- Contract timeout: `GatewayRpcContract.timeout_seconds` (default `20` seconds in code).
- Retry policy: bounded local retry loop `retries + 1` attempts.
- Runtime helper: `RpcBridge.route_text`.
- Retry stop is fail-closed: when all attempts end in timeout transport states, return with retry count.

## Error mapping

| Gateway result / source code | Normalized status |
| --- | --- |
| `UNAUTHORIZED` | `rpc_unauthorized` |
| `FORBIDDEN` | `rpc_forbidden` |
| `TIMEOUT` | `rpc_timeout` |
| `NETWORK` | `rpc_network_error` |
| `BAD_REQUEST` | `rpc_bad_request` |
| `NOT_FOUND` | `rpc_not_found` |
| transport exception | `rpc_transport_error` |
| missing/unknown | `rpc_unknown_error` / `rpc_malformed` |

## Offline verification evidence

- `services/feishu_gateway/runtime.py`: payload builder, bridge, status mapping, and fail-closed behavior.
- `tests/test_feishu_gateway_runtime.py`:
  - request contract fields,
  - incomplete payload rejection,
  - retry-until-success,
  - transport failure handling,
  - status mapping coverage,
  - malformed result handling.

## Gate-readiness note

- This phase does **not** include verified live official RPC transport against production OpenClaw credentials.
- Offline proof is stable and fail-closed; live transport proof remains blocked by environment authorization and current maintenance mode.
