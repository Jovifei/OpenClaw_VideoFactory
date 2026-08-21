# AI Director Phase 2 Worker Marker Integration Remediation 005U1

## 1. Current status

The latest independent 005U audit remains authoritative: the prior generic
`*.ready` assertion did not prove production marker suppression. This task
repairs that evidence gap only. It does not qualify the real Provider and does
not authorize 005V or 006.

Local result:

```text
AI_DIRECTOR_PHASE2_PROVIDER_MARKER_EVIDENCE_READY_FOR_EXTERNAL_AUDIT
```

Formal `PROJECT_STATUS.yaml` remains unchanged: P0 is `not_started`, P1 is
blocked by P0, and P2 is blocked by P1. Product capability remains locally
remediated pending real Provider qualification.

## 2. Immutable 005T boundary

- Run: `session_20260811T175916Z_43092`
- Terminal status: `BLOCKED_DETACHED_WORKER_DIED`
- `state.json` SHA-256: `ffc27a599151dd649d428180f67900d74e095120c0f2c1075fae71b77ddff2de`
- terminal ledger SHA-256: `e72ad3787267162fe4e56b840f6e7f762ccc227eb637d3e45b1bf4db978554f3`
- smoke attempts: 0
- acceptance attempts: 0
- Provider MP4: none

005U1 did not start or modify that run.

## 3. Remediation

The shared module now exposes two production-used seams:

- `Invoke-PQSupervisorWorkerStartup` owns the initial Worker launch,
  positive-PID persistence, `supervisor_ready`, Worker-ready validation,
  `worker_armed`, and downstream marker publication.
- `Publish-PQWorkerReadyMarker` validates `supervisor_ready` plus the persisted
  Worker PID before writing the Worker-ready marker.

`Invoke-PQSupervisor` and `Invoke-PQWorker` call these seams directly. The
initial launch path no longer keeps a separate inline implementation.

The exact production marker leaves under test are:

```text
SUPERVISOR_READY.txt
WORKER_READY.txt
LIVE_WORKER_ARMED.txt
CLOSE_CODEX_DESKTOP_NOW.txt
```

The positive control creates all four through the same seam and verifies exact
content and order. Failure injection verifies the exact marker set after token,
process, PID, CAS, PID-file, promotion, Worker-ready, arm, LIVE, CLOSE and
blocked-snapshot failures. The prior arbitrary `<run>.ready` assertion was
removed.

## 4. Local evidence

Main-agent reproductions:

```text
Pester 005R/005S/005T/005U/005U1: 60 passed, 0 failed, 0 skipped
tests/director:                       47 passed
tests/video:                         273 passed
video_factory/tests:                  5 passed
legacy:                               56 passed, 1 skipped, 13 subtests
PowerShell parser:                     0 errors on four target files
forbidden-control scan:                PASS
```

The legacy group was also run inside the sandbox; its single Chrome contact
sheet case was blocked by the managed sandbox. A separately authorized,
read-only out-of-sandbox rerun produced the result above.

Current implementation evidence hashes:

```text
scripts/provider_qualification.ps1
f53c0938f4eb847e72c0da98bb3a69d7228f11c2e2d8483e3e81c871accd79a9

scripts/lib/ProviderQualification.psm1
5b3e9cdde35fff0904277d31c79c24413e6ec736921c286bfa837b947573109e

schemas/ops/provider_qualification_run.schema.json
97162af261ec3093d94b2e742c650f61caf53cbbb109745f009ec7efc79dc5c5

tests/Test-ProviderQualification005U.ps1
7043db17d23a328a3be7e0b1a220786ccfd6924d3195f510b404de56602013b6

tests/Test-ProviderQualification005U1.ps1
be11cbe02e9c45409bb46392d3ac63b06f0dad21304f6633aa32eaf6f6cce122
```

## 5. Independent local reviews

- Specification reviewer: `APPROVED`. It confirmed production binding, exact
  marker leaves, a non-vacuous positive control, and the required failure
  matrix.
- Code-quality reviewer: `APPROVED`. It confirmed state/CAS/token cleanup,
  sanitized failure handling, one-shot preservation, PowerShell compatibility,
  and no real-process behavior in tests.
- Fresh internal final reviewer: `READY_FOR_EXTERNAL_AUDIT`. It independently
  reconciled production binding, the marker matrix, full regressions, Git and
  the immutable 005T evidence boundary.

These are local reviews. They do not replace the requested fresh external
read-only audit.

## 6. Protected and forbidden boundaries

The protected dirty-file SHA-256 values remained:

```text
PROJECT_STATUS.yaml cd0dc97280ed86abac748dceaff73a45587a92656d4481e782b37aa33002785d
reports/P0_ACCEPTANCE_MATRIX_V2.yaml acccf9e9440776583857c67ba15094ef461f1b61dfe0ebd436fa68b4e3b6905e
scripts/analysis_request.py 68bdd12ebc45d92fff17ae01dec7f6c4efcd0cef3e89aeb68434ec9ebed9ea1d
scripts/analyzer_mcp.py bcf09db631eed87316c4d2b0664abc159470860b0d3e84c7e8c3460071e09d90
scripts/mcp_ingest_attachment.py 313f00b8f855faaf2ad22cd01a61d987670d0ff02ff4c9de3d57970039a7d52b
scripts/media_action_ticket.py 794b0ed4dea1fb18eb52371d1fcddc4724d8d781b141b09214545e5af19699e5
```

005U1 did not start Supervisor/Worker, execute `codex exec`, run smoke or
acceptance, access cache/config/auth, close Desktop, create MP4, modify
OpenClaw/Feishu/Gateway/Binding/Cron, or stage/commit/push.

## 7. Remaining debt and next action

- Real Provider, real MP4 and media gates remain unproven.
- 005T and earlier blocked namespaces remain immutable.
- Historical 005S multi-generation recovery remains separate debt and must not
  be enabled by a future one-Worker qualification.
- A fresh external read-only audit must now review this exact current tree.
- Only an external approval may unlock planning of a new, separately authorized
  `AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V`.
- 006 Video Agent Orchestration, Feishu and Cron remain blocked.

AI_DIRECTOR_PHASE2_PROVIDER_MARKER_EVIDENCE_READY_FOR_EXTERNAL_AUDIT
