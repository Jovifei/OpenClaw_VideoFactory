# P0 Final Execution Baseline 037

Captured read-only on 2026-07-26 Asia/Shanghai. No credential value, raw
configuration, raw log, or identity was retained.

## Host and Git

| Field | Result |
|---|---|
| OpenClaw | `2026.7.1 (2d2ddc4)` |
| Branch | `phase/p0-gate-correction` |
| Git status entries | 41 untracked; 0 staged; 0 modified |
| Git remotes | 0 |
| OpenClaw config SHA-256 | `D6A97F1025698C08F086C1EE565E1AAC1AD30116037E4F135688EDBB1171BE8C` |

## Security and runtime

| Field | Result |
|---|---|
| `OPENCLAW_GATEWAY_TOKEN` present | false |
| Project runtime-log token markers | 0 |
| Project Gateway runtime processes | 0 |
| Project Gateway command-line token markers | 0 |
| Project-wide text secret-pattern candidate files | 0 |
| Rollback plan present | true |
| Project Gateway status | stopped/unknown health; no PID |
| Core observer | unknown; `CORE_CONSUMER_RUNTIME_OBSERVABILITY_UNAVAILABLE` |

## Counts

Current official read-only commands for Agents, Bindings, and Cron each exited
1 without a usable structured result. Counts are therefore **unavailable** in
this baseline. The older 034 snapshot values (Agents 17, Bindings 14, Cron 4)
are historical context only and are not treated as current evidence.

## Outcome

`WAITING_RPC_TOKEN`

After a secure Token injection and successful authenticated preflight, the next
state is `WAITING_MAINTENANCE_WINDOW`; no lifecycle action is authorized by this
baseline alone.
