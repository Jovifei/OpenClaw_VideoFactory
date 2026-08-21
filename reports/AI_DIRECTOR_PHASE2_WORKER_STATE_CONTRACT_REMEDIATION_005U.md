# AI Director Phase 2 — Worker State Contract Remediation 005U

## 1. 当前真实阶段

005T remains immutable and terminally `BLOCKED_DETACHED_WORKER_DIED`.
The pre-ready audit classified the root cause as `CODE_DEFECT + SCHEMA_MISMATCH`:
Supervisor persisted `worker_started` with `worker_pid=0` before creating the
Worker, while the previous schema required a positive PID for that state.

005U is local contract remediation only. No Worker, Provider, cache, Desktop,
smoke, acceptance, or real MP4 was run. Formal `PROJECT_STATUS.yaml` remains
P0 `not_started`, P1/P2 blocked.

## 2. Remediation

- `worker_started` now means generation/token/lease reservation; PID may be zero.
- Generation, launch count, Supervisor PID, both token hashes and lease remain
  mandatory and generation/launch count must match.
- `supervisor_ready` and every later live/success state still require
  `worker_pid >= 1`.
- Supervisor checks Start-PQProcess, rejects null/non-positive PID, persists the
  PID before `supervisor_ready`, and emits no ready/handoff marker on failure.
- Worker writes `WORKER_READY` only after `supervisor_ready` and PID equality.
- Launch failures persist sanitized `WORKER_CONTRACT_FAILED` and remove the
  exact run-bound token file.

## 3. Evidence and tests

Pester 005R/005S/005T/005U: **50 passed, 0 failed, 0 skipped**.
Python suites: Director **47 passed**, Video **273 passed**, Video Factory
**5 passed**. Legacy candidate/final-audit suite: **56 passed, 1 skipped,
13 subtests passed**.

PowerShell parser errors: 0. Forbidden provider/process-control scan: clean.
Schema checks cover reservation PID zero, mandatory bindings, positive PID at
`supervisor_ready`, historical 1.0 compatibility, 005T one-generation limit,
CAS/run conflicts and unchanged one-shot ledgers. TestDrive fault injection
also covers Start-PQProcess throw, null/PID-zero return, PID persistence/CAS
failure, ready-promotion failure, token cleanup, absence of readiness markers,
and sanitized structured `WORKER_CONTRACT_FAILED` blocked snapshots.

## 4. Independent reviews

Schema/State reviewer: `APPROVED_FOR_NEW_PROVIDER_QUALIFICATION_PLANNING`.
Lifecycle/Security reviewer: `APPROVED_FOR_NEW_PROVIDER_QUALIFICATION_PLANNING`.
These approvals authorize only planning a future qualification; they do not
prove Provider, Desktop, cache, smoke, acceptance, media, or Phase 2 readiness.

## 5. Protected evidence and boundaries

005T external run `session_20260811T175916Z_43092`, state hash
`ffc27a599151dd649d428180f67900d74e095120c0f2c1075fae71b77ddff2de`, and its
readonly terminal ledger hash
`e72ad3787267162fe4e56b840f6e7f762ccc227eb637d3e45b1bf4db978554f3` remain
unchanged. No cache/config/auth access, Worker/Provider command, Desktop
operation, OpenClaw/Feishu/Gateway/Binding/Cron change, PROJECT_STATUS change,
commit, push, reset, or clean occurred.

The six protected dirty-file hashes were recorded before implementation and
remain unchanged. The Git index remains empty.

Protected SHA-256 evidence:

| File | SHA-256 |
|---|---|
| `PROJECT_STATUS.yaml` | `cd0dc97280ed86abac748dceaff73a45587a92656d4481e782b37aa33002785d` |
| `reports/P0_ACCEPTANCE_MATRIX_V2.yaml` | `acccf9e9440776583857c67ba15094ef461f1b61dfe0ebd436fa68b4e3b6905e` |
| `scripts/analysis_request.py` | `68bdd12ebc45d92fff17ae01dec7f6c4efcd0cef3e89aeb68434ec9ebed9ea1d` |
| `scripts/analyzer_mcp.py` | `bcf09db631eed87316c4d2b0664abc159470860b0d3e84c7e8c3460071e09d90` |
| `scripts/mcp_ingest_attachment.py` | `313f00b8f855faaf2ad22cd01a61d987670d0ff02ff4c9de3d57970039a7d52b` |
| `scripts/media_action_ticket.py` | `794b0ed4dea1fb18eb52371d1fcddc4724d8d781b141b09214545e5af19699e5` |

## 6. Remaining debt and next task

The historical 005S multi-generation recovery path still attempts a PID-zero
reservation while in a PID-required state; it is not part of 005U and must not
be used by 005V. Real Provider qualification, real MP4/media evidence, and
final independent approval are still missing.

The first final review returned `FAIL_REVIEW` because the launch fault matrix
was not present. A second review then found a Windows PowerShell BOM/stdin
validator defect; the validator now decodes `utf-8-sig` and has a dedicated
regression. The fresh final reviewer returned
`APPROVED_FOR_NEW_PROVIDER_QUALIFICATION_PLANNING` after the corrected
`50/50` Pester run.

The next task is only a separately authorized
`AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V` plan. 006 Video Agent
Orchestration remains blocked.

## Latest external audit erratum — 2026-08-13

The latest independent audit returned `FAIL_REVIEW`: the TestDrive suite
asserted that a generic `*.ready` path did not exist, but that path was never
owned by the production Supervisor/Worker marker code. Therefore the claim
that all production readiness and Desktop-handoff markers were suppressed on
failure was not proven. 005U1 is restricted to repairing that evidence gap;
005V and 006 remain unauthorized.

FAIL_REVIEW
