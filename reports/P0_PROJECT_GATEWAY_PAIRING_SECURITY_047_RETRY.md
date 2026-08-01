# P0 Project Gateway Pairing Security 047 Retry

| Control | Result |
|---|---|
| Project identity and pairing state | external private directory only |
| State ACL | protected; current Windows user plus SYSTEM only |
| Project repository private key/device token | absent |
| Transaction durability | atomic pre-connection record persisted; terminal status `blocked` |
| Gateway connection count | exactly `1` |
| Connect request count | exactly `1` |
| Shared Gateway token | not read, copied, supplied, or logged |
| Other device identity/token | not read or used |
| Requested authority | role `operator`, scope `operator.read` only |
| Pairing request / device token | absent / absent |
| Business Session, Agent, Tool, Analyzer | none |
| Project Gateway resident process | `0` |
| Core Feishu / Gateway restart / configuration | unchanged / none / none |
| Credential material in command line, child stderr, reports | absent / absent / 0 scoped candidates |
| Project-owned identity/device-token artifact in repository | absent; 047/048 state remains external |
| Broad repository filename scan | 4 pre-existing, unmodified Shadow-fixture paths under `experiments/core_feishu_control_contract/shadow`; contents not read and no remediation authorized |

The Project pairing child removed `OPENCLAW_GATEWAY_TOKEN` from its own environment before it launched. Its command line contained only the existing official pairing entrypoint. It stopped after the first Gateway response and did not retry or fall back to another credential path.

The broad filename check is reported separately from the Project-device check: it found only historical Shadow fixture paths, not the current Project Gateway identity or token. The current task neither read their contents nor modified them.
