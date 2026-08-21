# AI-DIRECTOR-PHASE2-WORKER-STATE-CONTRACT-REMEDIATION-005U

## Purpose and boundary

Repair the deterministic 005T state-contract defect: `worker_started` is written
before the child process exists, so its `worker_pid` is temporarily zero while
the current schema incorrectly requires a positive PID.  This is a local
Schema/Supervisor contract repair only.  Do not start a Worker or Provider,
run `codex exec`, touch cache/config/auth, alter 005T evidence, or enter 006.

005T remains immutable and terminally `BLOCKED_DETACHED_WORKER_DIED`.
The highest 005U result is
`AI_DIRECTOR_PHASE2_PROVIDER_WORKER_CONTRACT_REMEDIATED`; it authorizes only a
future, separately named Provider qualification (005V).

## Locked state contract

- `supervisor_started`: supervisor is authenticated; worker PID is `0`.
- `worker_started`: generation, launch count, tokens and lease are reserved;
  `worker_pid` may be `0` or a positive PID.
- `supervisor_ready` and every later live/terminal success state require
  `worker_pid >= 1`.
- `worker_started` still requires valid generation/launch count, supervisor
  PID, both token hashes, lease ID/expiry, and the profile generation limit.
- No new state name, schema version, retry, cache operation, or Provider call.

## Execution and review gates

1. Freeze branch/HEAD/index, six protected dirty-file hashes, and the existing
   005T evidence. Run Pester 005R/005S/005T plus Director/Video/VideoFactory
   baselines. On mismatch stop as `BASELINE_BLOCKED`.
2. Add TestDrive-only 005U tests that first reproduce the old
   `worker_started + worker_pid=0` rejection, then require the repaired path:
   `supervisor_started -> worker_started(pid=0) -> PID update -> supervisor_ready`.
   Cover missing leases/tokens/generation, zero PID after ready, CAS conflict,
   one-shot ledgers, sanitization, and unchanged 005T blocked snapshots.
3. Change the JSON Schema so only `worker_started` permits PID zero; keep all
   token, lease, generation and supervisor-PID conditions. Keep positive PID
   requirements from `supervisor_ready` onward and preserve 1.0/1.1 compatibility.
4. Guard Supervisor launch: write the reservation state, create the one-shot
   token, launch the child, reject null/zero/negative PID, atomically persist a
   positive PID, and only then write `supervisor_ready` or any marker. Startup
   failure must sanitize/terminalize and remove the token; recovery code is
   regression-only and no 005T retry is permitted.
5. Run TestDrive fault injection, PowerShell parsing/static scans, Pester, the
   complete Python suites, and legacy regression. Do not invoke Preflight,
   Start, Rehearse, Worker, Supervisor, `codex exec`, or `generate_video`.
6. Run two read-only Luna xhigh reviewers (Schema/State and Lifecycle/Security),
   reproduce every finding, then run a fresh final reviewer. Only
   `APPROVED_FOR_NEW_PROVIDER_QUALIFICATION_PLANNING` closes 005U.
7. Write the 005U report, Change Request, todo/lessons/backlog entries and
   Obsidian update. Verify Git index remains empty, protected hashes are stable,
   005T files/external run are unchanged, forbidden surfaces are untouched, and
   all new evidence is trackable. End with the remediation marker or a specific
   failure status; never write a readiness marker.

## Next task

Only after an approved 005U may a separate plan authorize
`AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V` with a fresh namespace,
fixture, one Worker, one smoke and one acceptance.  006 remains blocked until
005V produces real Provider/media evidence and an independent final approval.
