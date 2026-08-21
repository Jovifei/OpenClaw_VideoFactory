# AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T

## Purpose and hard boundary

005S is terminally blocked because its only detached rehearsal Worker died before
Desktop quiescence. This is a new, independently namespaced qualification attempt;
it must not reopen, mutate, or reuse 005S or 005R evidence.

The highest success state is `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED` (product
evidence only). `PROJECT_STATUS.yaml` remains P0 `not_started`, P1/P2 blocked.
No OpenClaw, Feishu, Gateway, Binding, OAuth, Profile, model, Cron, commit, push,
reset, clean, or second video pipeline is allowed.

External run root: `E:/Claude_allow/Download/codex-provider-recovery-005t/`.
Only one detached Worker, one smoke command, and one acceptance command are allowed.
The Worker may not close, terminate, suspend, or restart Codex Desktop. Jovi must
close/reopen Desktop manually only after the run-bound handoff marker is written.

## Closed-loop execution

1. **Freeze and baseline.** Read project instructions and the 005S terminal report;
   record branch, HEAD, empty index, complete status, and six protected dirty-file
   hashes. Run the local Pester, Director, Video, VideoFactory, and legacy suites.
   Any mismatch is `BASELINE_BLOCKED` and stops the task.
2. **Fresh namespace.** Create a new Change Request, verify that the 005T external
   root, fixture directory, stable job directory, and output name do not exist, and
   record a manifest. Never delete an existing directory to make it fresh.
3. **Contract gate.** Finish profile-driven launcher/schema/Worker tests in TestDrive;
   require PowerShell parse success, strict lease/PID/token invariants, canonical
   command fingerprints, active-lock containment, source-freeze binding, supervisor
   liveness checks, one-shot ledgers, and recursive raw-output cleanup. A read-only
   contract reviewer and a security reviewer must both approve before any Worker.
4. **Prelaunch review.** Create the 005T topic/factual brief only from the already
   verified Modbus sources. No manual Storyboard, asset ID, path, prompt, or model
   output may be written. Freeze source hashes and bind the prelaunch reviewer result
   hash to the run manifest and active lock.
5. **Preflight.** Run the profile's read-only preflight. It must confirm npm Codex CLI
   version/flags, protected boundary, fresh run/job, no active 005T lock, Desktop
   process classification, and stable external-root containment. It may record only
   hashes, sizes, counts, and relative artifact references.
6. **Start and handoff.** Start exactly one hidden Supervisor/Worker pair with fixed
   argument arrays and run-bound launch tokens. Wait for `WORKER_READY` and
   `CLOSE_CODEX_DESKTOP_NOW` containing the exact run ID. If the Worker dies before
   ready, record `BLOCKED_DETACHED_WORKER_DIED`; do not restart it.
7. **Quiescence and cache gate.** After Jovi closes the entire Desktop, require 10
   one-second absent-process samples and 5 identical cache hash/size/mtime samples.
   Drift, timeout, or Desktop respawn yields the most specific BLOCKED status and no
   cache move.
8. **Hash-bound cache operation.** Back up the exact active cache byte-for-byte and
   verify its hash before any move. Quarantine only a degraded cache; healthy cache
   remains in place. Any mismatch performs byte-exact rollback and ends as
   `BLOCKED_PROVIDER_RECOVERY`.
9. **One smoke.** Atomically claim the smoke ledger before invoking the fixed
   read-only `codex exec` command. Validate Draft schema/scene count/cache health,
   delete raw stdout/stderr after hashing, and never retry. Failure is
   `REAL_PROVIDER_BLOCKED_SMOKE`.
10. **One acceptance.** Atomically claim acceptance and invoke `generate_video.py`
    once with the 005T fixture. Validate sanitized reports, completed/failed state,
    Script/Storyboard/Asset/Composition/Pink Pig contracts, and no old-evidence
    references. Failure is `PROVIDER_RECOVERED_ACCEPTANCE_FAILED`.
11. **Media and regression gate.** Decode and ffprobe the new MP4; require 1080x1920,
    30 FPS, H.264, AAC, 25–60 seconds, audible audio, subtitle safe area, no content
    overlap, 4+ Registry knowledge assets, and report/ffprobe agreement. Run the
    complete local suites. Any failure is `REAL_PROVIDER_MEDIA_OR_REGRESSION_FAILED`.
12. **Reopen, Verify, and independent review.** After `READY_TO_REOPEN`, Jovi may
    reopen Desktop. Verify is read-only and run-bound. Three reviewers (Provider /
    media / Git-environment) must be reproduced by Luna; a new final reviewer must
    return `APPROVED`. Reviewers may not request a second smoke or acceptance.
13. **Evidence delivery.** Write the 005T quiescence/run/final reports, update the
    Obsidian current-state pages and a new 005T page, append `tasks/todo.md` and
    `tasks/lessons.md`, and verify `.gitignore`, index, protected hashes, and banned
    surfaces. On any failure, write the exact blocker and stop.

## Required artifacts

```text
reports/CODEX_DESKTOP_QUIESCENCE_AUDIT_005T.json
reports/CODEX_PROVIDER_DETACHED_RUN_005T.json
reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005T.md
reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T.json
examples/ai_director_provider_qualification_005t/README.md
examples/ai_director_provider_qualification_005t/topic.txt
examples/ai_director_provider_qualification_005t/factual_brief.json
```

The final report must distinguish local/fake evidence from real Provider evidence
and must never write `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED` unless every gate
above, including independent final review, has evidence.
