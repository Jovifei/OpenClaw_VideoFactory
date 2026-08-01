# P0 managed restart result 045

`openclaw gateway restart --wait 30s --json` was executed exactly once after
all preflight gates passed.

| Field | Result |
| --- | --- |
| Pre-restart PID | 67516 |
| Post-restart PID | 45180 |
| Exit code | 0 |
| Structured result | `restarted` |
| Command duration | 31.505 seconds |
| Port 18789 after restart | one listener |
| Service loaded / official RPC probe / config audit | pass / pass / pass |
| Recovery start | not invoked |

The restart command's elapsed time is not a measurement of listener outage.
No second restart, force operation, skip-deferral operation, manual process
termination, or Core/Project lifecycle action was performed.
