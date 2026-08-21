# AI Director Phase 2 Remediation 004 Execution Record

This file records the execution boundary for the user-approved remediation
plan. The full task specification is the 004 implementation plan in the
current Codex task. Luna must use `subagent-driven-development`, preserve the
six pre-existing dirty files, and stop on any unclassified failure.

## Locked decisions

- Repair lifecycle failed snapshots and stale Director reports.
- Retire the historical Candidate render/TTS/subtitle/quality execution code;
  retain only state/control/inventory compatibility.
- Do not run or repair the Direct Codex CLI Provider.
- Do not modify OpenClaw, Feishu, Gateway, Binding, OAuth, Cron, or
  `PROJECT_STATUS.yaml`.
- Do not stage, commit, push, reset, clean, merge, or rebase.

## Baseline evidence

- `tests/director`: 32 passed.
- `tests/video`: 273 passed.
- `video_factory/tests`: 5 passed.
- legacy candidate/final-audit suite: 56 passed, 1 skipped because Windows
  symbolic links are unavailable; no test failures.
- branch: `codex/ai-director-video-factory-phase2-001`.
- HEAD: `76180a59ea662bdf168d88baaeb777d3e8eb59ef`.

## Ten stages

1. Freeze boundary and add the Change Request.
2. Add sanitized execution-error normalization and atomic state failure API.
3. Cover every Phase 2 exception boundary in `run_topic`.
4. Reset Director run artifacts and reject stale failure reports.
5. Remove the historical Candidate media execution chain.
6. Keep Candidate CLI control commands and fail retired commands structurally.
7. Update docs and error contracts.
8. Run directed tests, legacy regression, and media evidence checks.
9. Run three specialist reviews and one final independent review.
10. Write the remediation report, update Obsidian, recheck hashes, and stop.

The final status may be `AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED`, `FAIL_IMPLEMENTATION`,
or `BLOCKED`; it may not be a Phase 2 Ready status.
