# P0 Real Qualification Environment Design

## Safety objective

Provide a short-lived, non-production environment that can prove the three A-category controls without changing the production Feishu Binding, production bot, production group, or production OpenClaw state.

## Preferred topology

```text
Feishu test App + test Bot
          |
          v
     test group
          |
          v
Project Gateway qualification instance
          |
          v
isolated OpenClaw qualification Gateway
          |
          v
video-factory Router (test session / test data only)
```

### Isolation decisions

| Resource | Preferred requirement | Reason |
| --- | --- | --- |
| Feishu App | Yes, new dedicated test App | Separate credentials, event stream, callback signature and audit boundary |
| Feishu Bot | Yes, Bot owned by the test App | Prevents production bot delivery and consumer ambiguity |
| Feishu group | Yes, dedicated test group | Restricts TXT/PNG/card fixtures to a non-production chat |
| OpenClaw Gateway instance | Yes, isolated instance or operator-approved isolated profile | Avoids sharing the production channel owner and config state |
| RPC token | Yes, new non-production token with minimum route permissions | Proves auth without exposing or reusing production credentials |
| Configuration directory | Yes, separate qualification directory and runtime/PID/log paths | Prevents config, lease, state, and logs from overlapping production |

## Fallback options

1. Dedicated test App + dedicated test group + isolated OpenClaw instance: preferred and required for a clean qualification.
2. Dedicated test App + dedicated test group using an existing host: allowed only if the Gateway instance, config directory, RPC endpoint, PID, lease, and log paths are isolated and independently observed.
3. Short maintenance-window ownership change in the existing production group: last resort, requires explicit written approval for each stop/start and remains a controlled migration rehearsal, not an implicit default.

## Non-production acceptance boundaries

- Test messages contain no production media or confidential content.
- The qualification Gateway has a distinct owner identity and fenced lease.
- No production Binding or Cron is edited.
- The operator can stop the qualification instance and restore the prior entry within the agreed recovery objective.
- All event, chat, sender, file, token, and message content values are masked or hashed in evidence.

## Unknowns to resolve before execution

- Whether the installed OpenClaw supports an isolated instance/profile with a distinct RPC endpoint.
- Whether the Feishu test App can provide the required long-connection and signed callback permissions.
- Whether the Project Gateway launcher can accept the separate config, PID, lease, and log paths without code or production configuration changes.
- Whether a test-only Router/session namespace is available.

These are design questions only. 027 does not probe credentials, start a process, or connect Feishu.
