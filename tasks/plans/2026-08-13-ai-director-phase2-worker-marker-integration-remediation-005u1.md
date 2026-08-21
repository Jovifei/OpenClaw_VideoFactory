# AI-DIRECTOR-PHASE2-WORKER-MARKER-INTEGRATION-REMEDIATION-005U1

## Goal

Repair only the 005U production-marker evidence gap identified by the latest
independent audit. The implementation must prove, through the production
Supervisor/Worker integration seam and exact run-root marker names, that
pre-ready failures cannot publish readiness or Desktop-handoff evidence.

## Locked boundaries

- No Supervisor, Worker, Provider, `codex exec`, smoke, acceptance, cache,
  config, auth, Desktop, OpenClaw, Feishu, Cron, MP4, commit, push or formal
  phase operation.
- Preserve the terminal 005T run and all six protected dirty-file hashes.
- Do not plan or execute 005V or 006 in this task.
- Modify only the shared qualification script/module, 005U/005U1 Pester
  tests, task/report/backlog documentation, exact `.gitignore` exceptions and
  the designated Obsidian pages.

## Execution

1. Freeze Git, 005T, protected-hash and current-test baselines; record the
   latest external `FAIL_REVIEW` as authoritative.
2. Add failing TestDrive tests using the exact production marker leaves:
   `SUPERVISOR_READY.txt`, `WORKER_READY.txt`, `LIVE_WORKER_ARMED.txt`, and
   `CLOSE_CODEX_DESKTOP_NOW.txt`. A success control must create and validate
   all four so absence assertions cannot be vacuous.
3. Extract the real pre-ready Supervisor/Worker marker path into exported,
   dependency-injected functions used by the production entrypoints. Keep
   state/schema behavior, token cleanup and sanitized blocked snapshots.
4. Cover token/start/PID/CAS/pid-file/ready/handshake/armed/marker failures,
   plus exact content binding and success ordering. Never use a generic
   `*.ready` proof.
5. Run Pester (>50, zero failures), PowerShell parsers, Director 47, Video
   273, Video Factory 5, legacy 56/1 skipped/13 subtests, static forbidden
   scan, Git/hash/005T boundary audit and independent spec/quality/final
   reviews.
6. Update reports, task/backlog and Obsidian. Stop with
   `AI_DIRECTOR_PHASE2_PROVIDER_MARKER_EVIDENCE_READY_FOR_EXTERNAL_AUDIT` or
   the most specific failure state. External approval is still required
   before planning 005V.
