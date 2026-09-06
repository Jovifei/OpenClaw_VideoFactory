# Phase 1 lifecycle evidence 015

CR: `reports/change_requests/PHASE1-LIFECYCLE-EVIDENCE-015.json`.

- Use a new E-drive runtime root and a fresh SQLite database; do not touch the
  production candidate database or delete old attempts.
- Exercise `CandidateStore` cancel and failed→retry transitions and record the
  resulting job/event snapshots from the actual database.
- Read one in-progress job from a separate Python process to prove restart
  recovery, including persisted event/artifact state.
- Force one bounded NVENC failure, then encode the same local visual input with
  CPU, verify the fallback MP4 with ffprobe/full decode, and record both hashes.
- Validate each JSON against `phase1_lifecycle_evidence.schema.json`, then run
  the bounded Phase 1 suites. Stop before Formal Gate and human approval.
