# P0 Remaining Actions V21

1. Obtain explicit authorization for the controlled zhongshu maintenance
   window.
2. Re-run the current read-only preflight against a fresh production snapshot
   immediately before any window; do not rely on this Shadow evidence for
   current consumer ownership.
3. During the authorized window only, execute the reviewed stop/start and
   text, TXT, PNG, and card checks in Runbook V5.
4. Roll back immediately on any listed failure and publish the execution
   result.

Until item 1 is recorded, production execution is `NOT_APPLIED`.
