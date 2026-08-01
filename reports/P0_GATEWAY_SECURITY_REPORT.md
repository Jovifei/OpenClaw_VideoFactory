# Gateway security report

- Secrets are environment-only: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `OPENCLAW_GATEWAY_URL`, `OPENCLAW_GATEWAY_TOKEN`.
- Secret scan result: 0 unresolved secrets (from `reports/SECURITY_GIT_SECRET_SCAN.json` and `reports/SECURITY_CREDENTIAL_EXPOSURE_AUDIT.md`).
- Ticket state retains only digest fields and expiry/use flags; sender/chat/event_id are SHA-256 hashed before durable persistence.
- Events are deduplicated before dispatch; card validation enforces chat/sender/action matching, expiry, and one-time use.
- Runtime state and state files are ignored by Git.

No real secret values or real Feishu connection were used in this phase.
