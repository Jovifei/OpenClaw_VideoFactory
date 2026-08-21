# AI Director Phase 2 Real Provider Qualification 005V

## Terminal status

`BASELINE_BLOCKED`

This is a local baseline stop, not a real Provider result. 005V did not run
Preflight, start a Supervisor or Worker, access the Provider cache or auth
files, execute `codex exec`, claim smoke or acceptance, generate an MP4, or
request a Codex Desktop handoff.

## Completed local evidence

- Pester 005R/005S/005T/005U/005U1/005V: `76 passed, 0 failed, 0 skipped`.
- Director regression: `47 passed`.
- Video regression: `273 passed`.
- Video Factory regression: `5 passed`.
- The 005V local contract keeps `worker_started` as a PID-zero reservation,
  promotes to `supervisor_ready` only with a positive persisted PID, binds all
  final-review protected hashes, and has no runtime schema-validator bypass.

## Blocking baseline evidence

The locked legacy candidate group did not meet its required
`56 passed / 1 skipped / 13 subtests` result. Its contact-sheet test fails at
`tests/test_p1_candidate_media.py::CandidateMediaTests::test_all_mascot_poses_are_deterministic_and_contact_sheet_is_png`:

```text
mascot_contact_sheet_failed:2147483651:local_path_redacted
```

`2147483651` is `0x80000003` (`STATUS_BREAKPOINT`) from the local headless
Chrome child. The exact test was rerun once with a fresh repository-local
`TEMP`/`TMP` root and failed identically. No browser security flag was relaxed,
no browser was replaced, and no product renderer code was changed.

The rechecks created repository-local pytest artifacts. Cleanup was attempted
only after confirming the exact paths were non-reparse children of this
workspace; Windows file locking prevented completion, so the remaining
temporary artifacts are preserved and disclosed rather than forcibly removed.

## Boundary verification

- Branch: `codex/ai-director-video-factory-phase2-001`.
- HEAD: `76180a59ea662bdf168d88baaeb777d3e8eb59ef`.
- Index: empty.
- `git diff --check`: passed.
- All six protected pre-existing dirty-file SHA-256 values matched their locked
  baseline.
- The formal `PROJECT_STATUS.yaml` and the immutable 005T blocked evidence were
  not modified.

## Next allowed action

Resolve or independently prove the Chrome-host legacy baseline in a separately
bounded environment task. Only after that baseline is clean may a fresh 005V
local source-freeze/review gate be re-run. 005V has not consumed its Worker,
smoke, or acceptance authority.
