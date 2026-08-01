# P0 OpenClaw RPC Protocol Audit (023)

Status: `VERIFIED_FROM_LOCAL_RUNTIME_AND_TYPES`  
Scope: Project Feishu Gateway RPC only; no Feishu connection, Binding, Agent, Cron, OAuth, or production configuration was changed.

## Evidence

| Source | Verified fact |
| --- | --- |
| Installed OpenClaw CLI | `2026.7.1 (2d2ddc4)` |
| `gateway status --require-rpc` | Exit `0`; the installed Gateway RPC read probe is healthy. |
| `gateway call health --json` | Safe Boolean projection: `ok=true`. Raw health output was not retained. |
| Local endpoint | `ws://127.0.0.1:18789` (loopback only). |
| `dist/version-CwNT1gaY.js` | Gateway protocol version and minimum general client version are both `4`. SHA-256: `FB5BF01F88B38B22BB05BB91538FED58DB58038359E43017B68E4C989C971F76`. |
| `dist/schema-BuOFpc7K.js` | Defines `ConnectParamsSchema`, request/response frames, `AgentParamsSchema`, `SessionsCreateParamsSchema`, and `SessionsSendParamsSchema`. SHA-256: `B5B672DD1CE3579E2B030567EF192355374C052934CB4E252B793E08647D54AB`. |
| `dist/client-info-CcqJJIan.js` | Permits `gateway-client` client ID and `backend` client mode. SHA-256: `8FA9964EAF6F74D8DEDC9201005FDE402F24478CB2CBAB2FE37AA06378065E97`. |

The installed source agrees with the [Gateway protocol](https://docs.openclaw.ai/gateway/protocol), [Gateway CLI](https://docs.openclaw.ai/cli/gateway), and [Gateway integration guidance](https://docs.openclaw.ai/reference/openclaw-sdk-api-design).

## Verified wire contract

1. Transport is a text WebSocket using JSON frames.
2. Every request is `{type:"req", id, method, params}`; the matching reply is `{type:"res", id, ok, payload|error}`. Unrelated event frames may occur before the matching response.
3. The first accepted request is `connect`. Its required payload is `minProtocol`, `maxProtocol`, and `client`; the adapter sends protocol `4`, client `gateway-client`, and mode `backend`.
4. Authentication belongs in `connect.params.auth`. The installed schema accepts `token`, `bootstrapToken`, `deviceToken`, password, and runtime tokens; this project Adapter intentionally accepts only an explicitly injected shared-token provider. It never creates a device identity, pairs a device, or reads a token from OpenClaw configuration.
5. A successful handshake has `payload.type="hello-ok"`; the Adapter validates that marker and negotiated protocol before sending any request.
6. `agent` accepts `message`, optional `agentId`, `sessionKey`, `attachments`, `timeout`, and `deliver`. Project text sends use `deliver=false`, preserving the Project Gateway as the only Feishu reply owner.
7. Session APIs are `sessions.create` (`key`, `agentId`, optional metadata) and `sessions.send` (`key`, `agentId`, `message`, optional attachment metadata). The Adapter uses `sessions.create` for creation and `agent` for the project text request because the latter is the CLI-backed agent-run method.
8. No `attachment_event` RPC method was found in the installed protocol schema or official Gateway method evidence. `send_attachment_event()` therefore returns `rpc_method_not_available`; attachment safety remains on the existing `ingest_attachment` path.

## Adapter error policy

| Condition | Adapter status | Retry |
| --- | --- | --- |
| missing token provider value | `rpc_credentials_missing` | no |
| authentication rejection | `rpc_unauthorized` / `rpc_forbidden` | no |
| invalid request | `rpc_bad_request` | no |
| timeout | `rpc_timeout` | reconnect and retry |
| network/transport failure | `rpc_transport_error` / `rpc_network_error` | reconnect and retry |
| unsupported method | `rpc_method_not_available` | no |

## SDK decision

The installed OpenClaw release ships the Gateway protocol implementation and its own CLI client. No external package was added and no OpenClaw internals were copied. The Python Adapter implements only the audited wire envelopes and is tested with injected sockets.

## Remaining runtime boundary

The local loopback RPC service is available, but `OPENCLAW_GATEWAY_TOKEN` is not present in this process. The existing CLI can use its local credential resolution; the Project Adapter is deliberately not allowed to read that credential store or impersonate it. Therefore an independently authenticated Adapter connection has not been claimed.
