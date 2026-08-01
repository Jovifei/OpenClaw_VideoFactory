# P0 Evidence Index V7

## Current implementation and config

- `scripts/mcp_ingest_attachment.py` — explicit root matching, MCP-owned actual size, and non-public trusted declaration adapter.
- `scripts/07_ingest_inbound_media.ps1` — quarantine copy, signature, reparse, TOCTOU, stored-size, and stored-SHA checks.
- `scripts/analyzer_mcp.py` — three deterministic Analyzer MCP tools.
- `reports/change_requests/P0-R2-ANALYSIS-INTENT-GATE-011.json` — approved intent-gate scope and rollback.
- `reports/change_requests/P0-R3-STORED-HASH-INTEGRITY-012.json` — approved stored-hash scope and rollback.
- `reports/P0_009_CONFIG_DIFF.json` — approved semantic change scope and pre-apply gates.
- `reports/P0_009_CONFIG_PATCH.json5` and `reports/P0_009_AGENT_POLICY_BATCH.json` — applied patch inputs.

## Current tests

- `reports/P0_009_FULL_REGRESSION.json` — current suite counts and historical-count separation.
- `tests/test_analyzer_mcp.py` — 31/31 this task.
- `tests/test_trusted_media_roots.py` — 25/25.
- `tests/test_ingest_attachment_core.py` — 45/45 this task.
- `tests/Test-IngestInboundMedia.ps1` and `tests/Test-SingleGroupMediaRouter.ps1` — 82/82 this task (36 + 46).
- `scripts/v28_schema_tests.py` — 88/88 this task.
- `openclaw mcp probe ingest/analyzers --json` — 1 and 3 tools, diagnostics=0.

## Current operational evidence

- `reports/P0_009_PRODUCTION_SMOKE.json` — post-apply Gateway/MCP probe.
- `reports/P0_R1_SIZE_CONTRACT_FIX.json` — repaired trusted-size contract and preserved R1 failure.
- `reports/P0_R1_SIZE_FIELD_TRACE.json` — evidence that Router supplied 67 while trusted stat was 55.
- `reports/P0_R1_SIZE_SECURITY_TESTS.json` — new coverage and current regressions.
- `reports/P0_R1_SIZE_PRODUCTION_SMOKE.md` — two-root no-size/legacy-67 smoke after restart.
- `reports/P0_ANALYZER_MCP_TOOLS.json` — three-tool registration contract.
- `reports/P0_ANALYZER_TOOL_POLICY.json` — exact Analyzer policy.
- `reports/P0_TRUSTED_MEDIA_ROOTS.json` — two-root security contract.
- `reports/child_claude/P0_009_HAIKU_REVIEW_SUMMARY.md` — timeout classification and parent review boundary.

## Boundary evidence

## Live R1 replacement evidence

## Live R2 failure evidence

- `reports/P0_R2_EVENT_TRACE_20260720.json` - PNG quarantine succeeded, then the Router called the image Analyzer; analysis result was not read and R3-R5 were stopped.

- `reports/P0_R1_EVENT_TRACE_20260719.json` - real replacement TXT qualification: new message, server-owned 55-byte contract, fixture SHA, receipt, no Analyzer, and same-group reply.
- `reports/P0_LIVE_EVENT_TRACE_R0_R5.json` and `reports/P0_LIVE_SEQUENCE_QUALIFICATION.json` - R0 PASS, old R1 FAIL preserved, replacement R1 PASS, R2-R5 not run.
- `reports/P0_R2_ANALYSIS_INTENT_GATE_FIX.json/.md` and `reports/P0_R3_STORED_HASH_FIX.json/.md` — independent offline repair evidence.
- `reports/P0_R2_R3_SECURITY_TESTS.json/.md` — this task's focused security regression counts.
- `reports/P0_R2_R3_CONFIG_DIFF.json` — production config/topology unchanged.
- `reports/NEXT_USER_ACTION.md` — offline repair complete; require a new PNG message_id for R2 requalification.

- `reports/P0_009_RECOVERY_AND_CLOSURE.md` — final handoff.
- `reports/NEXT_USER_ACTION.md` — sole user action, fresh R1 TXT reupload.
- `reports/change_requests/P0-LIVE-SEQUENCE-ANALYZER-009.json` — `ready_for_real_channel_sequence`.
- `PROJECT_STATUS.yaml` — intentionally not modified.
