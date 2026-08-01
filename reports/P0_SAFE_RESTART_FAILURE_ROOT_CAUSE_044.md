# P0 safe restart failure root cause 044

## Evidence boundary

043B attempted the only authorized `openclaw gateway restart --safe --json` once.
It exited `1`, produced no retained structured result, left PID `13144` in place,
and did not interrupt port `18789`. Its original stdout, stderr, and command
timestamps were deliberately not persisted. A repeat is prohibited.

## Installed control path

OpenClaw 2026.7.1 source establishes that `--safe` calls the authenticated
`gateway.restart.request` RPC (`lifecycle-CciWmoyE.js:209-227`), which delegates
through `callGatewayCli` (`call-dBhJbczL.js:740-741`). The existing 043B
maintenance-child Adapter reached that authentication boundary on the unchanged
runtime and received `AUTH_TOKEN_MISMATCH`.

That makes authentication a plausible cause, but it is not a direct record of
the 043B CLI exit. Without the omitted stderr/structured payload, the required
exact branch cannot be proven.

## Classification

`SAFE_RESTART_UNKNOWN_FAILURE`

The classification is intentionally not `SAFE_RESTART_AUTH_REJECTED`. No safe
restart was replayed to obtain missing evidence.

The ordinary restart source path is distinct: `runDaemonRestart` selects the
service manager when `--safe` is absent (`lifecycle-CciWmoyE.js:299-318`), and
the token-drift check is warning-only before `service.restart`
(`lifecycle-core-BHOLC5Q0.js:434-476`). This proves implementation separation,
not authorization to bypass an unproven safe-restart failure.
