# P0 Gate Prereview (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Method: read-only audit mirroring `scripts/90_acceptance_gate.py` p0_checks. The actual Gate was NOT run (it would write `gate_p0.json`/`gate_p0.md` and `P0_READY.json` if passed - all prohibited this round). `P0_READY` was NOT created. `PROJECT_STATUS` was NOT updated.

## Summary

| Status | Count |
| --- | --- |
| passed | 11 |
| conditional | 2 |
| deferred | 2 |
| blocked | 11 |
| **overall** | **BLOCKED** |

## Passed (11)

- required paths (START_HERE_CODEX.md, PROJECT_STATUS.yaml, AGENTS.md, skills, config, scripts, runbook, handoff)
- local skill count (13 required skills present)
- factory fail-closed before implementation (scripts/factory.py contains "production pipeline is not implemented")
- runtime: openclaw --version
- runtime: openclaw config validate (exit 0)
- runtime: nvidia-smi (RTX 4070 SUPER detected)
- runtime: lark-cli --version (1.0.9)
- runtime: codex --version
- Skill visibility (SKILL_VISIBILITY.json passed)
- machine inventory evidence (reports/machine_inventory.json)
- OpenClaw state evidence (reports/openclaw_state)

## Conditional (2)

- **release checksums (SHA256SUMS.txt)**: the 007 round added new files (scripts, reports, fixtures) not reflected in SHA256SUMS.txt; some entries may be stale/mismatched. Fix: regenerate SHA256SUMS.txt in a separate authorized step (not this round).
- **existing agents/bindings regression (V2.5)**: OPENCLAW_EXISTING_AGENTS_REGRESSION.json exists but may not be V2.5 schema or current with the 007 17-agent state. The 007 `verify_007_invariants.py` independently confirms 17 agents / 14 bindings / other 13 unchanged, but the V2.5 evidence file needs refresh.

## Deferred (2)

- **direct Codex CLI smoke (V2.5)**: `DEFERRED_BY_USER_UNTIL_MAINTENANCE_WINDOW` (not faked as passed).
- **Codex CLI upgrade + smoke**: `DEFERRED_BY_USER_UNTIL_MAINTENANCE_WINDOW`.

## Blocked (11)

- **runtime: ffmpeg** - `ffmpeg` is NOT on the system PATH (the Gate runs `ffmpeg -version` directly, which fails). ffmpeg 8.1.1 IS installed at `C:\ffmpeg\bin\` (verified). Fix: add `C:\ffmpeg\bin` to PATH in a separate authorized environment change, OR the Gate must be run with PATH augmented. Not a P0 architecture blocker; an environment/PATH issue.
- **Feishu text ingress** - FEISHU_SMOKE_TEST.json not V2.5-passed with required check_id.
- **Feishu single consumer (V2.5)** - FEISHU_SINGLE_CONSUMER_TEST.json not V2.5-passed.
- **Feishu TXT/PNG/MP4 ingress + safe media (V2.5)** - FEISHU_INGRESS_TEST.json not V2.5-passed.
- **lark-cli Markdown/PNG/TXT/MP4 egress + idempotency (V2.5)** - FEISHU_EGRESS_TEST.json not V2.5-passed (dry-run evidence captured this round is NOT the V2.5 actual-egress evidence the Gate requires).
- **real Channel TXT event (R1)** - `blocked_real_channel_qualification_incomplete` (requires user upload).
- **real Channel PNG ingress (R2)** - blocked_real_channel_qualification_incomplete.
- **real Channel PNG analysis (R3)** - blocked_real_channel_qualification_incomplete.
- **real Channel audio analysis (R4)** - blocked_real_channel_qualification_incomplete.
- **real Channel MP4 analysis (R5)** - blocked_real_channel_qualification_incomplete.
- **real lark-cli outbound (actual send)** - `blocked_user_authorization_required` (dry-run only this round).

## Honest classification

The P0 Gate is BLOCKED. The blockers fall into three groups:

1. **Real Channel qualification** (R1-R5 + V2.5 Feishu evidence): requires the user to upload TXT/PNG/audio/MP4 to the VideoFactory Feishu group. This is the `READY_FOR_REAL_CHANNEL_SEQUENCE` next step. Cannot be faked.
2. **Real lark-cli outbound**: requires user authorization for an actual send. Dry-run evidence is captured; actual send is not authorized.
3. **Environment/PATH** (ffmpeg) + **deferred Codex CLI**: not P0 architecture blockers; resolvable in a maintenance window.

## What was NOT done (prohibited)

- The actual `python scripts/90_acceptance_gate.py --gate p0` was NOT run.
- `P0_READY.json` was NOT created.
- `PROJECT_STATUS.yaml` was NOT updated.
- No commit/tag/push.

## Evidence

- `reports/P0_GATE_PREREVIEW.json` (full check list)
- `scripts/p0_gate_prereview.py` (read-only audit mirroring the Gate)
