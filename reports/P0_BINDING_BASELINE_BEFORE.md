# Plugin-owned Binding migration baseline

- OpenClaw configuration SHA-256: `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`.
- Agents: 14; Bindings: 14; Cron jobs: 4.
- The dedicated group has one masked Feishu route owned by `video-factory`; the other 13 Binding hashes were recorded separately without identifiers.
- Gateway port 18789 is reachable.
- No barrier plugin directory, allowlist entry, or plugin entry exists.
- The VideoFactory session store exists with 19 files; session keys are deliberately not recorded.
- No media-ingest process was running at baseline. A fresh pre-migration activity check is mandatory before any production Binding change.
