# AI Director Phase 2 - 005V1 Local Provider Gate Remediation

## Decision

AI_DIRECTOR_PHASE2_PROVIDER_LOCAL_GATE_REMEDIATED

This is a local contract result only. It is not real Provider qualification,
not formal P2 approval, and not permission to enter 006.

## Why 005V1 was required

The 005V re-entry review returned CHANGES_REQUIRED. The deterministic findings
were: the operational Change Request was not wired into the dispatcher; 005T
evidence accepted alternate session IDs; runtime PNG/WAV inputs were outside
the source freeze; and schema-validation cleanup used an unsafe recursive
deletion path.

005T remains immutable:

- run: session_20260811T175916Z_43092
- state SHA-256: ffc27a599151dd649d428180f67900d74e095120c0f2c1075fae71b77ddff2de
- terminal ledger SHA-256: e72ad3787267162fe4e56b840f6e7f762ccc227eb637d3e45b1bf4db978554f3
- smoke: 0; acceptance: 0; MP4: 0

## Fixes

1. 005V operational modes now read the fixed canonical CR and fail closed
   while its status is baseline_blocked; Preflight requires contract review
   approval and Start/Supervisor/Worker require ready_for_worker.
2. 005T evidence is locked to the historical run ID above and alternate-run
   TestDrive coverage rejects another session.
3. The 005V source freeze now includes 12 runtime assets: five mascot PNGs,
   signature PNG, five Modbus illustration PNGs, and fallback BGM WAV. Each
   file is rechecked by byte length and SHA-256.
4. Schema-validation temporary output uses a containment-checked,
   no-reparse safe-tree cleanup routine.

## Local evidence

- Pester 005R/S/T/U/U1/V: 78 passed, 0 failed, 0 skipped.
- Python Director: 47 passed.
- Python Video: 273 passed.
- Python Video Factory: 5 passed.
- Legacy candidate/final audit group: 56 passed, 1 skipped, 13 subtests.
- PowerShell parser: 0 errors for qualification script/module.
- JSON parsing: run and final-review schemas valid.
- Forbidden control scan: clean.
- git diff --check: exit 0.
- staged index: empty, exit 0.
- LoadOnly source freeze: 83 files; digest
  ecef232e59eda9f020bb7feb18dfda6b685e1cbfba8377d0728f4a04f4b1a800.
- 005T immutable evidence digest:
  5e86bba919fa932da052bad055697d28a7d3e283961d770fec14f5dd6eea205f.

## Review

- Contract reviewer: APPROVED_FOR_LOCAL_GATE_REMEDIATION.
- Security/source-freeze reviewer: APPROVED_FOR_LOCAL_GATE_REMEDIATION.
- Fresh final reviewer: APPROVED_FOR_LOCAL_GATE_REMEDIATION_FINAL.

## Boundary

Branch codex/ai-director-video-factory-phase2-001; HEAD
76180a59ea662bdf168d88baaeb777d3e8eb59ef; index remained empty. The six
protected dirty-file SHA-256 values matched the established baseline before
and after this task. PROJECT_STATUS.yaml remains P0 not_started, P1
blocked_by_P0, P2 blocked_by_P1.

No Preflight, Worker, Supervisor, Rehearse, Status, Verify, codex exec,
Provider, Desktop, cache, config, auth, smoke, acceptance, MP4, OpenClaw,
Feishu, Gateway, Binding, Cron, commit, push, staging, reset, or clean was
performed.

## Next action

The next task must be separately authorized: 005V operational Preflight.
This report does not authorize it. If later real Provider, real MP4, media
gates, and final review all pass, only then may a separate plan for 006 be
written.
