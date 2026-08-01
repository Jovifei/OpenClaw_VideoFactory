# P0 Evidence Index V21

| Evidence | Purpose | Result |
|---|---|---|
| `P0_FEISHU_PLUGIN_ORIGIN_AUDIT_033.json` | Installed plugin identity and hashes | PASS |
| `P0_SHADOW_PLUGIN_LOAD_ROOT_CAUSE_033.json` | Initial load blockers and Shadow-only fixes | RESOLVED_IN_SHADOW |
| `P0_SHADOW_FEISHU_PLUGIN_LIFECYCLE_033.json` | Sanitized lifecycle result | READY |
| `P0_SHADOW_FEISHU_PLUGIN_RUNTIME_PROOF_033.md/json` | Real plugin and Gateway readiness | PASS |
| `P0_SHADOW_FEISHU_TRANSPORT_PROOF_033.md` | Fake SDK and network isolation | PASS |
| `P0_CORE_FEISHU_ACCOUNT_CONTROL_CONTRACT_033.md` | Account-scoped RPC contract | READY_IN_SHADOW |
| `P0_SHADOW_FEISHU_PLUGIN_INDEPENDENT_REVIEW_033.md` | Independent read-only review | PASS |
| `P0_FEISHU_GATEWAY_MAINTENANCE_RUNBOOK_V5.md` | Controlled window and rollback | PREPARED |

Raw Shadow probe artifacts are kept under
`experiments/core_feishu_control_contract/shadow/`; reports intentionally
omit paths, credentials, tokens, and raw CLI excerpts.
