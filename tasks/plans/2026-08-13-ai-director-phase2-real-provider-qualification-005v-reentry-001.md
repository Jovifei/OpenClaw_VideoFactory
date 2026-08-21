# AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V-REENTRY-001

## Purpose and stop boundary

This is a local-only re-entry gate after 005W. It does not run Provider
Preflight, Desktop inspection, cache inspection, Worker, smoke, acceptance,
Codex, or media generation. It does not authorize 006.

The historical 005V report and Change Request remain immutable. 005T remains
BLOCKED_DETACHED_WORKER_DIED. The only successful terminal marker allowed here
is READY_FOR_PROVIDER_PREFLIGHT, meaning that a separate human authorization is
still required before any real Provider action.

## Frozen identity

- Parent evidence: 005W CHROME_HOST_BASELINE_005W
- Task id: AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V-REENTRY-001
- Profile under review: 005V
- Branch: codex/ai-director-video-factory-phase2-001
- Expected HEAD: 76180a59ea662bdf168d88baaeb777d3e8eb59ef
- No staging, commit, push, merge, reset, clean, or PROJECT_STATUS edit.
- Protected six-file hashes must be captured before and after.

## Allowed writes

Only this plan, its Change Request, a new local-gate report/audit, exact task
and handoff status additions, exact ignore exceptions, and specified Obsidian
append-only notes may change. Existing 005T, 005V, and 005W reports, Change
Requests, external run roots, fixtures, and ledgers are not rewritten.

## Eight execution gates

### 1. Baseline and identity

Re-read START_HERE_CODEX.md, PROJECT_STATUS.yaml, AGENTS.md, tasks/lessons.md,
the 005T/005V/005W reports, and the relevant Obsidian pages. Record branch,
HEAD, index state, status, protected hashes, and immutable 005T hashes.

### 2. Local contract tests

Run the current 005R, 005S, 005T, 005U, 005U1, and 005V Pester suites using
Windows PowerShell with ExecutionPolicy Bypass. Run Director, Video,
VideoFactory, and the fixed legacy candidate suite with unique local
basetemp directories. No test may access the real cache, config, auth,
Desktop, Provider, or external run roots. Any unexpected count or failure is
BASELINE_BLOCKED and stops the plan.

### 3. Static and parser gates

Parse all qualification scripts/modules/tests and JSON schemas. Run
git diff --check and verify an empty index. Scan qualification sources for
Stop-Process, taskkill, danger-full-access, workspace-write, model/profile
switching, login, upgrade, raw credential/output logging, and a second video
pipeline. Record warnings separately from failures.

### 4. Production source freeze

Use the script's LoadOnly path and Get-PQSourceFreeze -IncludeFixture. This
must be read-only and must not invoke Preflight. Confirm the 005V production
dependency closure, fixture files, final-review schema, all U/U1/V tests,
generate_video and Director/pink-pig/video-factory imports, and the immutable
005T evidence hashes are included. Any source drift invalidates the freeze and
requires returning to Gate 2.

### 5. Local prelaunch audit

Create a new structured audit containing only local evidence: test counts,
parser/static results, source-freeze digest, Git boundary, 005W approval,
005T immutable hashes, and explicit zero counts for Provider/cache/auth/
Desktop/smoke/acceptance/MP4 actions. Do not call the operational Preflight
mode. The Change Request remains prepared_pending_contract_review until the
read-only reviewers approve.

### 6. Independent reviews

Temporarily dispatch three Luna xhigh read-only reviewers, one each for
profile/schema/final-review binding, lifecycle/marker/one-shot behavior, and
security/source-freeze/Git/005T immutability. They may not edit, start
processes, read cache/config/auth, or substitute for parent tests. Stop each
agent immediately after its result. Reproduce every finding in the parent.

### 7. Final local decision

Start one fresh Luna xhigh final reviewer after all findings are reproduced.
APPROVED_FOR_005V_LOCAL_GATE_REENTRY is required. If approved and all local
evidence is consistent, write READY_FOR_PROVIDER_PREFLIGHT. Otherwise write
BASELINE_BLOCKED, SOURCE_FREEZE_DRIFT, LOCAL_CONTRACT_REVIEW_FAILED, or
FAIL_REVIEW with the most specific evidence.

### 8. Documentation and stop

Write the new report and audit, append tasks/todo.md, tasks/lessons.md,
handoff/codex/IMPLEMENTATION_BACKLOG.yaml, and the specified Obsidian pages.
Re-run Git boundary and protected hashes. Stop immediately at
READY_FOR_PROVIDER_PREFLIGHT. The next action must be separately authorized:
one real 005V Preflight, followed only by its own Provider qualification plan.

## Required report fields

The report must distinguish formal P0/P1/P2 state from product capability,
list every command and count, preserve old evidence classes, show no Provider
actions, include protected hashes before/after, list reviewers, and state that
READY_FOR_PROVIDER_PREFLIGHT is not Provider qualification and does not permit
006, Feishu, Gateway, Binding, Cron, or automatic operation.
