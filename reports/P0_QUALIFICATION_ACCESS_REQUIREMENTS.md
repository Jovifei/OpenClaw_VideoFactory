# P0 Qualification Access Requirements

## Purpose

These are the minimum, separately authorized inputs for a future controlled qualification. They do not authorize a production cutover.

| Required authorization | Minimal use | Evidence to retain | Not authorized by this document |
| --- | --- | --- | --- |
| OpenClaw RPC token | Inject only through the approved local token provider for a loopback connect/health and one bounded test request | Redacted connection result, request correlation hash, timeout outcome | Reading, recording, or committing the token; production Agent changes |
| Feishu test-app credentials | Test-app long connection and signed callback validation against a non-production test group | App identity class, callback verification result, event hashes | Production app use, production group traffic, or permanent Binding changes |
| Maintenance window | Operator-owned, time-bounded controlled test channel | Window start/end, observer, stop criteria | Formal production migration without a new written authorization |
| Gateway start permission | Start the Project runtime only in the approved test window with fenced owner controls | PID/health/owner evidence without secrets | Restarting the current OpenClaw Gateway or stopping its Feishu Binding outside the window |

## Required confirmations before any controlled runtime attempt

- [ ] Test-app credentials are distinct from the production application.
- [ ] The RPC token is available through an approved secret provider and is never printed.
- [ ] An operator owns the test-window stop/rollback decision.
- [ ] The old Binding's stop and restoration commands have been reviewed by the operator.
- [ ] A fenced exclusive-consumer implementation and independent observer are available.
- [ ] The reply-to-message analysis admission is implemented by OpenClaw, not by a card shortcut.

## Current result

No credential, test-app, maintenance-window, or runtime-start authorization was supplied to this qualification. No access was requested from the operating system and no live connection was attempted.
