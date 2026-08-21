# AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V

## Purpose

Run one new, hash-bound real Codex Provider qualification after the approved
005U1 marker-contract remediation. 005T remains immutable and no formal P0/P1/P2
phase is advanced by this task.

## Fixed identity

- profile: `005V`
- task_id: `AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V`
- schema_version: `1.1`
- maximum Worker generations: `1`
- smoke commands: `1`
- acceptance commands: `1`
- rehearsal: forbidden
- external root: `E:/Claude_allow/Download/codex-provider-recovery-005v/`
- fixture: `examples/ai_director_provider_qualification_005v/`
- topic digest: `1224cb6eb1e538f6b33f25664d19c8c22469ddff8b972e81b10404e81fc915d5`
- stable job: `director_1224cb6eb1e538f6`
- output: `pink_pig_modbus_ai_provider_005v.mp4`

## Execution gates

1. Freeze branch, HEAD, empty index, six protected dirty-file hashes, and the
   immutable 005T run/ledger hashes. Run Pester 60, Director 47, Video 273,
   Video Factory 5, and legacy 56 passed/1 skipped/13 subtests. Any mismatch is
   `BASELINE_BLOCKED` and stops the task.
2. Add the 005V profile, task/profile Schema binding, final-review Schema,
   TestDrive contract tests, fixture and Change Request. Rehearsal is rejected;
   old 005R/S/T evidence is never reused.
3. Run parser, forbidden-control, path/raw-output scans, all local regression,
   and three read-only Luna terra/xhigh contract, lifecycle, and security
   reviews. Any source change invalidates the freeze and requires rerunning all
   gates and reviews. Only then mark the Change Request `ready_for_worker`.
4. Run exactly one read-only Preflight. It must prove fresh external root/job,
   no active lock, source-freeze integrity, trusted CLI/media tools, Desktop
   identity, stable cache observation, and unchanged protected boundaries.
5. Run exactly one `Start -Apply`. The Worker must publish the four run-bound
   markers in order before the human closes the entire Codex Desktop. The
   Worker never closes/restarts Desktop. A pre-ready death is terminal and is
   never retried.
6. Require ten one-second absent Desktop samples and five identical cache
   hash/size/mtime samples. Back up the cache byte-for-byte; quarantine only a
   degraded cache, with immediate hash-bound rollback on mismatch.
7. Claim and execute one fixed read-only `codex exec` smoke. Validate Draft
   Schema, 5-9 scenes, healthy cache, bounded output, and raw-artifact cleanup.
   Smoke failure prevents acceptance and records `REAL_PROVIDER_BLOCKED_SMOKE`.
8. Claim and execute one outer `generate_video.py --topic-file ... --factual-brief
   ... --director-provider codex-cli` acceptance. Validate the new stable job,
   Director/Storyboard/Asset/State/Quality contracts and sanitized failure
   state. Never rerun after failure.
9. Validate the real MP4 with FFmpeg/ffprobe, audio level, H.264/AAC,
   1080x1920/30fps/25-60s, subtitle/content safe regions, TTS-scene parity,
   Pink Pig/Composition gates, and all local regressions. On failure record
   `REAL_PROVIDER_MEDIA_OR_REGRESSION_FAILED` and stop.
10. After `READY_TO_REOPEN.txt`, the human may reopen Desktop. Run read-only
    Verify, then three fresh independent Luna terra/xhigh reviews and one final
    reviewer. Only an exact `APPROVED` permits schema-valid final-review evidence,
    `Verify -Finalize`, readonly terminal ledger conversion, and completed state.
11. Write reports, append Obsidian 005V evidence, preserve cache backup, verify
    Git/forbidden boundaries and all child agents are stopped. Success marker is
    `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED`; otherwise preserve the most
    specific blocker and stop. Do not enter 006, Feishu, Cron, or commit/push.

## Mandatory boundaries

No Worker, Provider, cache, Desktop, OAuth, Profile, model, PROJECT_STATUS,
OpenClaw, Feishu, Gateway, Binding, Cron, commit, push, merge, reset, clean or
staging operation is permitted before all local/prelaunch gates pass. The only
human actions are closing Desktop after the run-bound handoff marker and
reopening it after `READY_TO_REOPEN.txt` or `BLOCKED.txt`.
