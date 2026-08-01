# P1 Offline Candidate Implementation Plan

**Goal:** Implement a reviewable, deterministic P1 video-factory candidate without changing production phase or connecting to OpenClaw/Feishu.

**Boundary:** Candidate-only state is `state/p1_candidate/`; generated jobs are `jobs/p1_candidate/`. Keep the production entrypoint fail-closed unless a `candidate` subcommand is explicitly selected.

## Ordered implementation

- [ ] P1-A: Add SQLite tables, append-only events, transitions, idempotent create, cancel/retry/recovery, and JSON-safe CLI output.
- [ ] P1-B: Add the pinned Remotion project, safe input-contract validator, local Chrome render script, and template contract tests.
- [ ] P1-C: Add fixed-fixture TTS, deterministic cache, SAPI fallback, WAV conversion, and captions/SRT.
- [ ] P1-D: Add four portrait templates and renderer cancellation wiring.
- [ ] P1-E: Add 8 deterministic SVG mascot poses, staging, and contact-sheet rendering.
- [ ] P1-F: Generate and verify three fixture packages plus NVENC and CPU evidence.
- [ ] P1-G: Add dry-run delivery records only; never invoke lark-cli.
- [ ] Verify Python, Pester, schemas, TypeScript, media, dependency integrity, secret/large-file scans, and candidate reports.
- [ ] Write the Obsidian verification note and create a one-time 08:30 evidence-only reminder.

## Stop conditions

Stop the affected increment on a failing test, unavailable permitted dependency, actual secret candidate, renderer/encoder failure without approved fallback, or any attempt to contact OpenClaw/Feishu/ComfyUI/Cron. Record the concrete evidence and do not skip forward.

## Review criteria

The only success label is `P1_CANDIDATE_IMPLEMENTED_OFFLINE`. It is not phase promotion and does not replace the pending P0 R3 real retest.
