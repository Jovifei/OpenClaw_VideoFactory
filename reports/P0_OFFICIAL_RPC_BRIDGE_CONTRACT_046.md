# Official RPC Bridge Contract 046

## Supported boundary

The Python runtime calls a one-shot Node child through stdin/stdout. A random session value is passed only in the child environment and request body. The Node child rejects a missing or mismatched session. Neither side writes credentials to project files, logs, reports, configuration, or command arguments.

## Method allowlist

| Method | Current state |
|---|---|
| `health` | active; fail-closed before networking when no Project identity exists |
| `session.resolve` | contract-reserved; returns `bridge_method_not_active` |
| `agent.request` | contract-reserved; returns `bridge_method_not_active` |
| `request.status` | contract-reserved; returns `bridge_method_not_active` |

Requests must target `video-factory`. Tool, model, configuration, channel, device-management, and admin-shaped fields are rejected. The bridge never creates a business Session, invokes an Agent, sends a message, or calls a tool during this task.

## Preflight behavior

With an empty external identity store, health returns `device_identity_missing`. This was observed on 2026-07-26 without identity creation or network connection. It is the intended fail-closed state before a user-authorized pairing request.

