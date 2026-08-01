# Feishu Gateway Maintenance Runbook V2

- **T-30:** Create and hash a redacted backup; confirm all authorizations and rollback owner.
- **T-10:** Run preflight snapshot checks; confirm no active jobs/pending media and existing single core consumer.
- **T0:** Stop old Feishu entrance only using the separately approved operator command; prove it exited.
- **T+1:** Start project Gateway only after a separately approved production-mode transport integration exists; the 022 launcher is offline-only.
- **T+2:** Query `/health` and `/ready`; require one consumer plus verified RPC and Feishu connection.
- **T+5:** Send the approved real text test and retain one-route/one-reply evidence.
- **T+10:** Send the approved real attachment test and retain receipt/cleanup evidence.
- **T+15:** Send the approved card-action test and retain ticket/Analyzer evidence.

At any failure: immediately stop the project Gateway, execute the approved core Binding restoration, verify text/attachment/session recovery, and record a sanitized event timeline. This document is a procedure, not migration authorization.
