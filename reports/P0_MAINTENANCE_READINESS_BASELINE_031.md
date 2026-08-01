# P0 Maintenance Readiness Baseline 031

Status: `READ_ONLY_BASELINE_CAPTURED`

Captured at `2026-07-23T00:10:55.6762381Z` using configuration hashes, safe CLI projections, read-only SQLite aggregation, process-count projections, and Git metadata only.

| Item | Sanitized observation |
| --- | --- |
| OpenClaw configuration | SHA-256 `D6A97F1025698C08F086C1EE565E1AAC1AD30116037E4F135688EDBB1171BE8C` |
| Gateway | Managed service loaded; PID not emitted by the safe no-probe status projection |
| Inventory | 17 Agents, 14 Bindings, 5 stored Cron jobs / 4 enabled |
| zhongshu | Configuration and target-group routing binding present; this is not runtime-consumer proof |
| Tasks | 33 total, 0 active, 33 terminal, 26 succeeded, 7 failed |
| Git | `phase/p0-gate-correction`; 0 remotes; 40 existing porcelain entries; `git diff --check` clean |
| Secret scan | 0 candidate files; raw matches and configuration contents were never emitted |

The baseline does not claim a Feishu connection, a Core Binding consumer, a Project Gateway consumer, a WebSocket owner, a heartbeat, or a real RPC credential. Those facts remain unobserved and fail closed.

No Binding, Gateway, configuration, Agent, Cron, Feishu, RPC, or production process was changed.
