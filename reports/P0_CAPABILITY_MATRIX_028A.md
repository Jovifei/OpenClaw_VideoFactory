# P0 Capability Matrix 028A

| Function | Status |
| --- | --- |
| Text message | `ready` |
| Attachment ingress | `ready` |
| Image analysis | `ready-after-channel` |
| Audio analysis | `ready-after-channel` |
| Video analysis | `ready-after-channel` |
| Card action | `ready-after-channel` |
| RPC | `blocked-runtime` |
| Real migration | `blocked-env` |

## Status meanings

- `ready`: the local Gateway/Router contract and offline evidence are complete for the current frozen scope.
- `ready-after-channel`: the downstream analysis path is isolated and prepared, but requires a qualified channel event and OpenClaw admission before real use.
- `blocked-runtime`: the protocol/authenticated RPC path has not been verified in a real isolated runtime.
- `blocked-env`: the required non-production App/Bot/group, access types and maintenance-window authorization are not present.

This matrix is a readiness boundary, not a production acceptance gate.
