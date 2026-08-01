# zhongshu Consumer-Ownership Audit 031

Result: `CONSUMER_OWNERSHIP_NOT_PROVEN`

The configured zhongshu route proves only configuration presence. It does not prove that a Feishu long connection is open, identify its owner, or count consumers. The Project offline runtime process count is 0. Generic Node processes are intentionally not treated as Feishu evidence because process presence, HTTPS traffic, model traffic, and Gateway WebSocket traffic cannot establish a TLS Feishu consumer owner.

| Required fact | Result |
| --- | --- |
| Binding owner | `unknown` |
| Consumer count | `null` — no explicit runtime evidence, never coerced to zero |
| Feishu connection count | `null` — no authenticated connection evidence |
| Owner PID / start time | `null` |
| Last heartbeat / event | `null` |
| Project Gateway process | 0 observed for the offline runtime only |
| Configured Binding | Present, but configuration is not connection proof |

`scripts/migration/inspect_zhongshu_consumer.py` is intentionally offline: it accepts only an operator-collected, sanitized evidence snapshot. In the absence of such evidence it returns `unknown`, not a guessed Core or Project owner. `ZERO_CONSUMER_NOT_PROVEN` and `SINGLE_CONSUMER_NOT_PROVEN` are therefore the only safe current conclusions.
