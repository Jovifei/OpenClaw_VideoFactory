# Codex Master Contract — Current

Updated: 2026-09-05

This file is intentionally short. The detailed current contract now lives in:

- `START_HERE_CODEX.md`
- `PROJECT_STATUS.yaml`
- `docs/CURRENT_ARCHITECTURE.md`
- `docs/PRODUCT_PHASES.md`
- `handoff/codex/PROJECT_HANDOFF_20260905.md`
- `handoff/codex/NEXT_AGENT_PROMPT_20260905.md`
- `handoff/codex/CURRENT_BACKLOG.yaml`
- `runbook/11_PHASE1_COMPLETION.md`

## Current task boundary

Repository: `E:\project\OpenClaw_VideoFactory`

Branch: `codex/phase1-reference-video-analysis-001`

Product phase: `PHASE_1_LOCAL_VIDEO_FACTORY`

Status: `in_progress`.

Goal: finish the local factory so it can:

1. take a Jovi topic and automatically produce an auditable local video;
2. take a Jovi-authorized local reference MP4, analyze it conservatively and produce an original reconstruction;
3. prove lifecycle, quality, human review and the formal Phase 1 Gate.

Phase 2 Feishu/OpenClaw/Cron work is explicitly deferred until Phase 1 passes.

## Mandatory engineering rules

- Fetch and audit the current remote HEAD before changing files.
- Continue on the current branch unless Jovi explicitly changes it.
- Do not reset, clean, auto-stash, rebase or force-push user work.
- Do not create a second video pipeline, DB or orchestration framework.
- Do not make Jianying the mandatory renderer; local MP4 + evidence is the Phase 1 core result.
- Aspect ratio is job-scoped: vertical and landscape profiles both exist.
- Pink Pig personal IP is opt-in and requires Jovi-owned original assets + receipt.
- Do not let historical Codex CLI Provider cache problems block the deterministic local factory.
- Do not run Feishu/Gateway/Binding/OAuth/Cron tasks during Phase 1.
- Do not download models/nodes without explicit approval.
- Do not automatically publish to Douyin.
- Do not report a phase passed from one demo or one green sub-suite.

## Current Definition of Done

Phase 1 is done only after:

- Modbus, Flash/watchdog and FreeRTOS each have one selected current candidate and Prereview;
- required reference-video originality evidence and Jovi human review exist;
- cancel/retry/restart/encoder-fallback machine evidence exists;
- Acceptance Manifest and Boundary Audit exist;
- bounded current regression is green and explicitly scoped;
- independent read-only review passes;
- formal Phase 1 Gate produces `PHASE1_READY.json`;
- only then may `PROJECT_STATUS.yaml` be promoted in a separate closure action.

Do not use the historical `IMPLEMENTATION_BACKLOG.yaml` as the current execution queue; it is retained for compatibility/history. Use `handoff/codex/CURRENT_BACKLOG.yaml`.
