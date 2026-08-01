# P0 Feishu to OpenClaw Session Mapping Contract (023)

Status: `IMPLEMENTED_AND_OFFLINE_TESTED`

## Mapping

`SessionKeyMapper(agent_id="video-factory")` maps the Feishu identity pair to:

```text
agent:<agent_id>:feishu:<sha256(chat_id)[0:24]>:<sha256(sender_id)[0:24]>
```

The key contains no raw Feishu chat or sender identifier. Each digest component is a 96-bit prefix of SHA-256 and is deterministic for the same input.

| Feishu identity | Required property |
| --- | --- |
| same chat + same sender | identical session key |
| same chat + different sender | different session key |
| different chat + same sender | different session key |
| missing chat or sender | fail with `feishu_identity_required` |

## OpenClaw API use

1. Create/adopt the key with `sessions.create({key, agentId})`.
2. Send a text turn with `agent({message, agentId, sessionKey, deliver:false, timeout})`.
3. Keep `deliver=false`; only Project Feishu Gateway converts the returned reply into a Feishu response.

## Security and audit controls

- The mapper is pure and has no network, file, or token dependency.
- Raw IDs must never enter structured logs; callers log only the existing one-way event/chat/sender hashes.
- The Adapter does not pass Feishu file keys, media paths, or attachment event payloads to OpenClaw RPC.
- One Feishu user is isolated from another even when both are in the same group.

## Continuity boundary

The existing offline `GatewayPayloadBuilder` still uses its historical group-only key (`feishu:group:<chat_id>`). This task intentionally does not replace it, because changing that established key would split existing group history and requires an approved migration decision. The 023 mapper is the required per-user contract for the Project Gateway activation path; it is not silently applied to the current Binding.
