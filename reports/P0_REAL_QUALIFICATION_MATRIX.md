# P0 Real Qualification Matrix

## Execution gate

Design only. Every row requires a test-group identifier, an operator, a timestamp, redacted event/request hashes, and an explicit rollback decision. No row was executed in 027.

| ID | Path | Test | Pass evidence | Immediate failure action |
| --- | --- | --- | --- | --- |
| RPC-01 | Text | Gateway connects to isolated OpenClaw RPC | Authenticated connection and health response, values redacted | Stop qualification; do not send text |
| RPC-02 | Text | Stable session mapping | Same test chat/sender/thread maps to one stable session; different sender/thread maps separately | Stop and preserve trace |
| RPC-03 | Text | Request correlation | Gateway event hash, RPC request id, Router receipt and response correlate | Stop; no retry until reconciled |
| RPC-04 | Text | Retry | A controlled retry has one logical response and no duplicate Router action | Stop; mark ambiguous delivery |
| RPC-05 | Text | Timeout recovery | Timeout path reaches bounded recovery or dead-letter without duplicate response | Roll back if recovery is not bounded |
| ATT-01 | Attachment | TXT ingress | Receipt, SHA and quarantine evidence; no unintended analysis | Stop attachment testing |
| ATT-02 | Attachment | PNG ingress | Receipt, SHA and quarantine evidence; no unintended analysis | Stop attachment testing |
| CARD-01 | Card | Upload produces bounded card | Test-group card returned with masked ticket evidence | Stop card testing |
| CARD-02 | Card | `card.action.trigger` click | Operator/chat/action/ticket validated; ticket consumed once; request trace recorded | Stop and invalidate test ticket |
| CARD-03 | Card | Analysis admission | OpenClaw-owned durable analysis request is present; no direct Analyzer/Gateway compute call | Stop; do not repeat click |
| CON-01 | Consumer | Before/after owner | Before old=1/new=0; after old=0/new=1; one authenticated WebSocket | Immediate rollback |
| CON-02 | Consumer | Duplicate detection | No duplicate event or reply hashes during the window | Immediate rollback and reconcile |
| RB-01 | Rollback | Forced Gateway start/health failure | New owner stops, old entry restores, text and attachment paths pass | Continue rollback, then stop |
| RB-02 | Rollback | Recovery boundary | State/event reconciliation, measured RTO/RPO and loss boundary recorded | Keep production entry unchanged |

## Required test data

- One harmless text message.
- One small TXT fixture.
- One small PNG fixture.
- One attachment upload followed by the approved card flow.
- No production files, identifiers, or secrets.

## Evidence rule

`PASS` is valid only for an executed row with independent observer evidence. A plan, fake event, static inspection, or absent error is `NOT_EXECUTED`, not a pass.
