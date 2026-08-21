# AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2

This is a one-time authorization bridge for the already approved local
005V1 contract remediation. It authorizes exactly one read-only 005V
Preflight and nothing else.

It does not authorize Start, Supervisor, Worker, Rehearse, codex exec, smoke,
acceptance, cache mutation, Desktop close/reopen, OAuth/Profile/model/config
changes, OpenClaw/Feishu/Gateway/Binding/Cron, PROJECT_STATUS edits, commit,
push, staging, reset, or clean. Historical 005V and 005T reports/CRs remain
immutable.

Before the operational command, rerun only the local contract test and parser
gate. Then execute:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/provider_qualification.ps1 -QualificationProfile 005V -Mode Preflight

Capture exit code and sanitized JSON only. On any failure, stop with the
specific blocked status. On success, stop immediately after recording the
read-only Preflight evidence; a new authorization is required for Worker.

## Execution closure — 2026-08-14

The single authorized command was executed once. It returned exit code `1`
with the sanitized reason `unexpected_error`. No retry was made. Read-only
postflight checks found no 005V external run root, active lock, stable job,
READY/BLOCKED marker, Worker, smoke, acceptance, or MP4. The bridge is closed
as `PREFLIGHT_BLOCKED`; any further diagnostic or qualification action requires
a new Change Request and authorization.
