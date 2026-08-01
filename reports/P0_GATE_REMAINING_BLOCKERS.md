# P0 Gate Remaining Blockers (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
P0 Gate overall: **BLOCKED** (prereview; actual Gate not run).

## Blockers (must resolve before P0 Gate can pass)

### B1. Real Channel qualification incomplete (PRIMARY BLOCKER)
- **Items**: R0 (text), R1 (TXT), R2 (PNG ingress), R3 (PNG analysis), R4 (audio analysis), R5 (MP4 analysis).
- **Status**: `blocked_real_channel_qualification_incomplete`.
- **Why**: requires the user to upload real TXT/PNG/audio/MP4 to the VideoFactory Feishu group. This round captured text + PNG smoke via `openclaw agent` turns (007) but NOT real Feishu Channel events.
- **Unblock**: user runs the `READY_FOR_REAL_CHANNEL_SEQUENCE` (send `P0_TEXT_ROUTER_TEST`, then upload each fixture one at a time per the R0-R5 protocol). Each step's observability evidence updates the V2.5 Feishu evidence files.

### B2. Feishu V2.5 evidence files not current
- **Items**: FEISHU_SMOKE_TEST.json, FEISHU_SINGLE_CONSUMER_TEST.json, FEISHU_INGRESS_TEST.json, FEISHU_EGRESS_TEST.json must be V2.5 schema with required check_ids passed.
- **Status**: blocked (depend on B1 real Channel events + B3 actual egress).
- **Unblock**: refresh these evidence files from the real Channel qualification results.

### B3. Real lark-cli outbound not authorized
- **Item**: actual lark-cli send (Markdown/PNG/TXT/MP4+cover).
- **Status**: `blocked_user_authorization_required`.
- **Why**: this round captured dry-run evidence only (4 dry-runs, exit 0, no actual send). The Gate requires V2.5 actual-egress evidence.
- **Unblock**: user authorizes an actual lark-cli outbound send (separate authorization).

### B4. ffmpeg not on system PATH
- **Item**: Gate runs `ffmpeg -version` directly; fails because ffmpeg is at `C:\ffmpeg\bin\` (not PATH).
- **Status**: blocked (environment), but NOT a P0 architecture blocker.
- **Unblock**: add `C:\ffmpeg\bin` to the system PATH in a maintenance window, OR run the Gate with PATH augmented. (The analyzer runtime works - it uses the absolute path.)

## Conditional (not blockers, but should refresh)

- C1. SHA256SUMS.txt is stale (007 added files). Regenerate in an authorized step.
- C2. OPENCLAW_EXISTING_AGENTS_REGRESSION.json V2.5 not current with 17-agent state. Refresh (007 `verify_007_invariants.py` already proves the invariants).

## Deferred (user explicitly deferred; do NOT fake as passed)

- D1. Codex CLI smoke (V2.5) - `DEFERRED_BY_USER_UNTIL_MAINTENANCE_WINDOW`.
- D2. Codex CLI upgrade + smoke - `DEFERRED_BY_USER_UNTIL_MAINTENANCE_WINDOW`.

## Not blockers (already passed)

11 checks passed (paths, skills, factory fail-closed, openclaw, config validate, nvidia, lark-cli version, codex version, skill visibility, machine inventory, openclaw state).

## Single unblock path

The primary unblock is the user running the real Channel sequence (`READY_FOR_REAL_CHANNEL_SEQUENCE`). That resolves B1, which enables B2. B3 (actual egress) and B4 (ffmpeg PATH) are separate authorizations/maintenance. D1/D2 stay deferred.

## What was NOT done

- P0_READY NOT created.
- PROJECT_STATUS NOT updated.
- Actual Gate NOT run.
- No commit/tag/push.
