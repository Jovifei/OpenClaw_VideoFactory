# P0 Evidence Index V5

Operating state: `conditional_not_passed` (P0 Gate not run; 007 production implementation complete and smoke-verified).

| Area | Evidence | State |
| --- | --- | --- |
| Baseline before | `P0_SINGLE_GROUP_ROUTER_BASELINE_BEFORE.json/.md` | captured; SHA `c7098b22...5660d` verified |
| Change request | `change_requests/P0-SINGLE-GROUP-MEDIA-ROUTER-007.json` | authorized execution round |
| Haiku A-F reviews | `child_claude/SINGLE_GROUP_MEDIA_SCOPE_REVIEW.md`, `SINGLE_GROUP_ROUTER_TOOL_POLICY_REVIEW.md`, `INGEST_ATTACHMENT_CONTRACT_REVIEW.md`, `INTERNAL_ANALYZER_AGENTS_REVIEW.md`, `RTX4070S_MEDIA_RUNTIME_REVIEW.md`, `SINGLE_GROUP_ROUTER_MIGRATION_REVIEW.md` | all 6 completed |
| ingest_attachment tool | `P0_INGEST_ATTACHMENT_TOOL.json/.md`, `scripts/mcp_ingest_attachment.py`, `scripts/run_ingest_safe.ps1`, `scripts/07_ingest_inbound_media.ps1` | implemented; MCP probe 1 tool; 17/17 tests |
| Multi-attachment | `P0_MULTI_ATTACHMENT_CONTRACT.md` | implemented; 32/32 legacy unchanged |
| GPU lock | `P0_GPU_MEDIA_LOCK_CONTRACT.md`, `scripts/gpu_media_lock.py` | implemented; 4/4 lock tests |
| Router tool policy | `P0_ROUTER_TOOL_POLICY.json/.md` | prepared + applied |
| Internal analyzers | `P0_INTERNAL_MEDIA_AGENTS.json/.md` | 3 binding-less agents applied |
| Config diff | `P0_SINGLE_GROUP_ROUTER_CONFIG_DIFF.json/.md`, `P0_SINGLE_GROUP_ROUTER_CONFIG_DIFF_APPLIED.json` | applied; SHA `3001ec3b...` |
| Tests | `P0_SINGLE_GROUP_ROUTER_TESTS.json/.md` | 94/94 |
| Runtime smoke | `P0_SINGLE_GROUP_ROUTER_RUNTIME_SMOKE.json/.md`, `scripts/smoke_007_attachment.py` | text + PNG PASS; audio/MP4 deferred |
| Migration | `P0_SINGLE_GROUP_ROUTER_MIGRATION.md` | 3 restarts documented |
| Rollback | `P0_SINGLE_GROUP_ROUTER_ROLLBACK.md` | prepared; not triggered |
| Implementation | `P0_SINGLE_GROUP_ROUTER_IMPLEMENTATION.json/.md` | master report |
| Post-change invariants | `scripts/verify_007_invariants.py` | 17 agents / 14 bindings / 4 cron / 1 consumer / 3 analyzers no binding / other 13 unchanged |
| Local runtime | `child_claude/RTX4070S_MEDIA_RUNTIME_REVIEW.md` | PyTorch cu128 + faster-whisper 1.2.1 + ffmpeg 8.1.1 (C:\ffmpeg\bin); no local VLM |
| Old routes (not retried) | `P0_PLUGIN_OWNED_BINDING_MIGRATION.md`, `P0_FULL_AGENT_PROXY_VALIDATION.md`, `P0_PREINGEST_ARCHITECTURE_OPTIONS.md`, `P0_CHANNEL_MIDDLEWARE_FEASIBILITY.md` | design blocked; 007 used scope-deny + tool-policy instead |

## Secrets policy

All apiKeys, appSecrets, gateway token, real target-group id, and file_keys are masked in every report. Real identifiers live only in the live config and the MCP server env (read from config at apply time).

## Protected state retained

No P0 Gate, P0_READY, PROJECT_STATUS update, commit, tag, push, P1, model install/download, real Feishu outbound, OAuth/Binding/Cron change.
