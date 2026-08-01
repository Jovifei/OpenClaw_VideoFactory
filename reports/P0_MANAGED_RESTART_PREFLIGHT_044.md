# P0 managed restart preflight 044

Timestamp: `2026-07-26T18:34:33+08:00`

| Gate | Result |
| --- | --- |
| User-scope token present | true |
| One-use maintenance-child injection | true |
| Token in maintenance-child command line | false |
| Gateway listener / service loaded / RPC probe | 1 / true / true |
| Gateway service config audit | false |
| Active or queued tasks / unknown tasks | 0 / 0 |
| Configuration SHA matches 030 | true |
| Agents / Bindings | 17 / 14 |
| Cron count | unavailable: `cron list --json` did not return structural JSON |
| Project Gateway processes | 0 |
| zhongshu ready state | unproven: probe was unstructured and contained an error marker |
| Rollback artifact | present |
| `restart --safe --json` help support | true |
| Git worktree | dirty, 41 porcelain entries; preserved |

`can_execute=false`

Blockers: `SAFE_RESTART_ROOT_CAUSE_UNPROVEN`,
`SERVICE_CONFIG_AUDIT_NOT_OK`, `CRON_OBSERVABILITY_UNAVAILABLE`, and
`CORE_CHANNEL_READY_UNPROVEN`.
