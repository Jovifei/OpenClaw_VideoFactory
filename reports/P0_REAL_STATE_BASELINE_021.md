# Real State Baseline 021

Captured locally on 2026-07-21 without changing production state.

- Agents: 17; `video-factory` remains `mimo-v2.5-pro`.
- Bindings: 14; `video-factory` has one binding.
- Cron: 4 enabled jobs, 0 reported running.
- Gateway: loopback `127.0.0.1:18789`, runtime running, CLI/Gateway `2026.7.1`.
- Configuration SHA-256: `D6A97F1025698C08F086C1EE565E1AAC1AD30116037E4F135688EDBB1171BE8C`.
- Git: `phase/p0-gate-correction`, no remote output, and all project entries remain untracked.
- Plugins: 72 discovered, 7 enabled; Gateway reports two active official-plugin version drifts.
- Feishu: the existing `zhongshu` account is configured/running with the core Binding. It remains the current consumer; project Gateway is not running.

## Cron correction

The prior 020 value of 1 was a counting defect: `openclaw cron list --json` returns one pagination envelope containing `jobs: [4]`. The correct count is the `jobs` array length, four. No Cron was deleted, added, enabled, disabled, or otherwise modified.
