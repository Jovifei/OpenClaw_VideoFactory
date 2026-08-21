# AI-DIRECTOR-PHASE2-PROVIDER-LOCAL-GATE-REMEDIATION-005V1

## Why this remediation exists

The 005V local re-entry tests passed, but independent read-only reviews found
four deterministic contract gaps. This remediation is local code and test
work only. It must finish before any 005V Preflight, Worker, smoke,
acceptance, cache operation, Desktop handoff, or 006 planning.

The old 005V re-entry plan is stopped at CHANGES_REQUIRED and its evidence is
preserved. 005T remains immutable and BLOCKED_DETACHED_WORKER_DIED. The
highest allowed result after this task is
AI_DIRECTOR_PHASE2_PROVIDER_LOCAL_GATE_REMEDIATED.

## Fixed scope

Allowed source edits:

- scripts/provider_qualification.ps1
- scripts/lib/ProviderQualification.psm1
- tests/Test-ProviderQualification005V.ps1

Allowed evidence/docs:

- this plan
- its Change Request
- one remediation report
- tasks/todo.md, tasks/lessons.md, handoff backlog, exact Obsidian append
- exact .gitignore exceptions

Do not edit 005T, old 005V, or 005W reports/CRs, external runs, ledgers,
PROJECT_STATUS.yaml, cache/config/auth, Desktop, OpenClaw, Feishu, Gateway,
Binding, Cron, or Git index/history.

## Four fixes

### A. Operational authorization gate

Read the canonical 005V Change Request only for the operational modes. Require
contract_review_approved_pending_preflight before Preflight and
ready_for_worker before Start/Supervisor/Worker. Reject a baseline_blocked or
prepared re-entry request with a sanitized stable error. Keep LoadOnly and
all local TestDrive tests available. Rehearse remains forbidden.

### B. Exact 005T identity

Accept only session_20260811T175916Z_43092 for 005T evidence. Reject every
alternate session even when its files and hashes are internally consistent.
Add a TestDrive positive fixture using the exact historical run id and a
negative alternate-run test.

### C. Runtime asset byte freeze

Extend the 005V production freeze to include every registry-driven render
asset and the fallback BGM: five mascot PNGs, signature.png, five Modbus
illustration PNGs, and assets/pink_pig/demo_music.wav. Keep registry-declared
hashes and source-freeze file hashes aligned. Add a test that required asset
paths are in the closure and that a changed asset hash is detected.

### D. Safe schema-validation cleanup

Replace the direct recursive Remove-Item used for the schema-validation
temporary tree with the existing no-reparse, containment-checked safe-tree
algorithm. Add a TestDrive regression proving normal cleanup and a source
route assertion proving the unsafe recursive call is absent from the
validation finally block. Do not broaden deletion to any other directory.

## Verification

Run Pester 005R/S/T/U/U1/V plus new remediation tests, parser and JSON
validation, Director 47, Video 273, VideoFactory 5, and legacy
56 passed/1 skipped/13 subtests. Run only LoadOnly source freeze afterwards.
Run no operational qualification mode and access no real cache/config/auth.

Run two fresh read-only Luna xhigh reviews after the fixes, then a fresh final
review. Any source edit invalidates the prior freeze and requires all tests
again. Only an APPROVED local review may produce
AI_DIRECTOR_PHASE2_PROVIDER_LOCAL_GATE_REMEDIATED and the next separately
authorized task remains 005V Preflight, not Worker or 006.
