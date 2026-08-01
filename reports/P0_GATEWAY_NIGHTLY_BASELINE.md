# P0 Gateway Nightly Baseline (020)

Date: 2026-07-21. Scope is offline only; no production mutation occurred.

- Config SHA-256: `D6A97F1025698C08F086C1EE565E1AAC1AD30116037E4F135688EDBB1171BE8C`.
- Project manifest: 1,144 files, SHA-256 `0D20A2BD015DB8E298DC7A285FBF775902863D0676571FECADA303F504A28A65` (excludes `.git`, venvs, caches, vendor research).
- Git: branch `phase/p0-gate-correction`; all project entries are untracked; no remote printed.
- Existing reports were present and hashed before 020 work.
- Local query: 17 agents, 14 bindings, Gateway running loopback-only. `cron list` returned 1 item, not the requested 4; this is recorded as drift only.
- Feishu channels remain the pre-existing core consumers; no project Gateway process or socket was started.
