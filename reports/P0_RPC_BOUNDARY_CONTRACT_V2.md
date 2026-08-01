# P0 RPC Boundary Contract V2 (024)

Status: `ENFORCED_OFFLINE`

The Project Gateway may submit only a bounded request to Agent `video-factory` and receive its response.

Allowed request context:

```text
agent_id, session_key, message_id,
tenant_id, chat_id, sender_id, thread_id, text,
optional analysis_request(action, receipt_path, stored_path, ticket_hash)
```

The `analysis_request` context identifies a verified card action and quarantined artifacts; it does not name an Analyzer, model, GPU, tool, or alternate Agent. OpenClaw video-factory remains responsible for the deterministic downstream decision.

Rejected:

- a non-`video-factory` Agent;
- Analyzer/model/GPU/tool selectors;
- direct session creation (`rpc_method_not_allowed`);
- invented attachment RPC (`rpc_method_not_available`).

`send_message()` continues to enforce `deliver=false`, preserving the Project Gateway as the only Feishu reply owner after a future authorized cutover. Runtime authentication remains separately blocked because no approved token provider has been injected.
