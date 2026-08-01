# P0 Evidence Index V8

## Fresh live qualification

- `reports/P0_LIVE_MEDIA_BASELINE_BEFORE.json/.md` — immutable 012 baseline.
- `reports/P0_LIVE_MEDIA_R2_QUALIFICATION_012.json/.md` — new PNG R2 PASS and bare MP4 ingress-only PASS, with masked IDs and receipt/hash/size evidence.
- `reports/P0_LIVE_EVENT_TRACE_R0_R5.json/.md` — old R2 FAIL preserved; replacement R2 and R2V recorded; R3-R5 not run.
- `reports/P0_LIVE_SEQUENCE_QUALIFICATION.json/.md` — sequence stopped at `READY_FOR_R3`.

## Child review summaries

- `reports/child_claude/P0_LATEST_INGRESS_REVIEW.md`
- `reports/child_claude/P0_LIVE_ANALYSIS_REVIEW.md`
- `reports/child_claude/P0_REAL_EGRESS_REVIEW.md`
- `reports/child_claude/P0_GIT_PUBLICATION_REVIEW.md`

## Unchanged implementation evidence

Existing offline repair tests and prior R0/R1 evidence remain indexed by V7 reports. No production configuration, Gateway, Binding, Agent, Cron, or `PROJECT_STATUS.yaml` changed.

## P0-TWO-MESSAGE-ANALYSIS-INTENT-013

- `reports/P0_TWO_MESSAGE_ANALYSIS_CONTRACT.md` — attachment-first, Reply-targeted contract and fail-closed error map.
- `reports/P0_ANALYSIS_REQUEST_SCHEMA.json` — independent request schema and immutable receipt boundary.
- `reports/P0_TWO_MESSAGE_ANALYSIS_IMPLEMENTATION.json/.md` — changed files, four-field Analyzer surface, and production-state diff.
- `reports/P0_TWO_MESSAGE_ANALYSIS_TESTS.json/.md` — actual Python/Pester/MCP/V2.8 results.
- `reports/P0_TWO_MESSAGE_ANALYSIS_SMOKE.md` — fake attachment + Reply + Analyzer proof; no live R3 claim.
- `reports/P0_TWO_MESSAGE_ANALYSIS_CONFIG_DIFF.json` — config SHA unchanged; new MCP tool requires a separately authorized runtime reload if the live allowlist does not expose it.
- Old same-message R3 evidence remains `NOT_RUN_INVALID_MESSAGE_SHAPE`; it is not promoted to PASS.

## Live R3 failure

- `reports/P0_R3_TWO_MESSAGE_EVENT_20260720.json/.md` records the real Reply event, the two `analysis_intent_not_recognized` rejections, the unauthorized `analyze image` substitution, and the later Analyzer trace.
- The new live R3 failure is recorded separately and is not promoted to PASS; R4/R5 remain stopped.
