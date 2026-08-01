# P0 Project Gateway Device Pairing Request 047 Retry

## Result

`PROJECT_GATEWAY_DEVICE_PAIRING_BLOCKED:INVALID_REQUEST`

The one authorized official Project-device pairing connection was made to the local Gateway and then ended. The Gateway returned the exact safe top-level code `INVALID_REQUEST` without a safe structured detail code. Therefore this report does not guess whether the cause is signature, device identifier, role, scope, or a broader protocol mismatch.

No `PAIRING_REQUIRED` response was received. No pending request, approval action, or Project device token was created.

## Pre-connection gates

| Gate | Result |
|---|---|
| Loopback listener `127.0.0.1:18789` | one listener present |
| Gateway service status | available through no-RPC-probe service check |
| Project Gateway resident process | `0` |
| External Project state root | present and outside repository |
| ACL | current Windows user plus SYSTEM; protected |
| Official Project identity | loaded and internally verified |
| Pairing status / request id / device token | `not_requested` / absent / absent |
| Existing pending record / active transaction | absent / absent |
| Shared token or other device identity | not read or used |

## Authorized one-shot connection

| Control | Result |
|---|---|
| Official bridge operation | `pairing-request` |
| Connection attempts / connect requests | `1` / `1` |
| Requested role | `operator` |
| Requested scopes | `operator.read` only |
| Project identity | independent; nonce-signature path enabled |
| Shared token supplied | no |
| Child token environment | removed before launch |
| Credentials in child command line | no |
| Child exit / stderr | `0` / absent |
| Gateway result | `INVALID_REQUEST` |
| Pairing metadata persisted | no; no pairing request was returned |

## Durable post-result state

The private pairing attempt transaction was atomically created before connection and persists with status `blocked`. It records the safe error code privately. The Project auth state remains `not_requested`, with no request id and no device token. The bridge disconnected and did not call health, create a business Session, or invoke an Agent, Tool, Analyzer, Feishu action, Core lifecycle action, or Project Gateway process.

## Stop boundary

There is no pending request to approve, so no operator-approval guide is applicable. Do not retry the connection under this authorization. Any repair or diagnostic of the protocol rejection requires separate authorization.
