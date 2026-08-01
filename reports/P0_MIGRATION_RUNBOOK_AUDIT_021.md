# Migration Runbook Audit 021

The Runbook is a correct safety outline but is not executable yet.

| Section | Present | Missing / required before execution |
|---|---|---|
| Before | Backup, health, workload, Binding checks | Exact approved backup command/path, workload query, message-volume source, operator sign-off |
| Stop old Binding | Intent stated | Supported OpenClaw command/config procedure, confirmation signal, maximum outage timer |
| Start project Gateway | Intent stated | Launcher command, working directory, environment contract, log path, PID file, readiness probe, graceful shutdown |
| One consumer | Intent stated | Source of process/socket/identity evidence and duplicate-event/reply capture method |
| Text/attachment/card | Intent stated | Approved real test payloads, expected result, timeout, evidence location, abort criteria |
| Rollback | Intent stated | Exact restore procedure, bounded recovery objective, post-restore session evidence, owner |

Manual confirmation is mandatory at every transition. A redacted configuration backup must exist before any stop operation. No current Runbook step authorizes a production action by itself.
