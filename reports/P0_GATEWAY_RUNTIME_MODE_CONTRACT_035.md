# P0 Gateway Runtime Mode Contract 035

## Modes

| Mode | Feishu transport | RPC behavior | Readiness | Current use |
|---|---|---|---|---|
| `offline` | fake/absent | no credential read; no RPC probe | always false | tests and local isolation |
| `production-preflight` | not started | real token authentication plus `health` | true only after both succeed | maintenance T-60/T-10 |
| `production` | must be real Feishu | must use authenticated RPC | requires Feishu and RPC | guarded; unavailable in 035 |

## Isolation guarantees

- `offline` never invokes the token provider or network probe.
- `production-preflight` cannot initialize a Feishu transport. It validates only
  the OpenClaw RPC credential and health.
- `production` currently returns
  `production_transport_unavailable`, writes no PID, and starts no process.
- `ready=true` is possible only in `production-preflight` after a successful
  authenticated RPC health check.
- Missing/rejected credentials never fall back to offline or to the Core path.

The production guard is intentional. Removing it requires a separately reviewed
real Feishu connection implementation and a maintenance-window execution task.
Task 035 does not provide either authority.
