# P0 Project Device Identity Security 048

| Control | Result |
|---|---|
| Identity location | external private state root; not in repository |
| State-root path form | local non-UNC path |
| ACL | protected inheritance; only current Windows user and SYSTEM have required access |
| Private key representation | official v1 identity state; no key value reported |
| Public key / device identifier | validated internally; no complete value reported |
| Initialization durability | temporary write, sync, atomic rename, then reload validation |
| Incomplete-state handling | initializer fails closed and quarantines only a detected partial identity to an external sibling path |
| Pairing request | absent |
| Device token | absent |
| Shared Gateway token | not read, copied, supplied, or logged |
| Other device identity/token | not read or used |
| Gateway / WebSocket / RPC activity | none |
| Business session, Agent, Tool, Analyzer | none |
| Project Gateway resident process | `0` |
| Command line credentials | none |
| 048 scoped credential scan | 0 candidates |

The initializer removes a token environment variable from its controlled child before execution. It constructs the installed official client only for offline acceptance validation and does not invoke any lifecycle or transport method. Reports contain status projections only and no private key, public key, complete device identifier, pairing request identifier, device token, shared token, or credential derivative.
