# P0 Session Isolation V2 (024)

Status: `IMPLEMENTED_AND_OFFLINE_TESTED`

## Contract

```text
agent:video-factory:feishu:
  tenant:<sha256(tenant_id)[0:24]>:
  chat:<sha256(chat_id)[0:24]>:
  sender:<sha256(sender_id)[0:24]>:
  thread:<sha256(thread_id)[0:24]>
```

Raw identifiers never appear in the key. Message and card contracts require `tenant_id` and `thread_id`; a card uses its verified `operator_id` as the sender identity for the OpenClaw request.

## Isolation proof

| Case | Result |
| --- | --- |
| same tenant/chat/user/thread | stable key |
| same group, user A vs B | isolated |
| same user/thread, tenant A vs B | isolated |
| same user/group, thread A vs B | isolated |
| duplicate event | rejected before another RPC request |

## Migration boundary

The historical group-only session key is replaced only in the Project Gateway code path. The current OpenClaw Binding is unchanged. A future cutover must explicitly accept that V2 begins isolated per-user/thread histories; no existing live session was migrated in 024.
