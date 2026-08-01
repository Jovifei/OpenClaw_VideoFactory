# P0 Current Status V20

## Final state

`CORE_FEISHU_SHADOW_VALIDATION_BLOCKED`

The static control contract is resolved as target-scoped account runtime
stop/start, but Shadow Feishu plugin loading is not proven. The existing
zhongshu/Core path remains unchanged and no maintenance window was entered.

## Evidence summary

- OpenClaw CLI: `2026.7.1`.
- Feishu package: `2026.6.6` (drift advisory; no upgrade).
- Shadow config validation: PASS.
- Shadow Gateway loopback/RPC substrate: PASS.
- Shadow Feishu plugin/account runtime: BLOCKED (`0 plugins`).
- Production stop/restart/config/message/card: NOT RUN.
- Existing 17 Agents / 14 Bindings / 4 Cron topology: preserved; no status file update.

## Gate boundary

Do not start a Project Gateway or perform a real `channels.stop/start` until the
installed Feishu plugin can be loaded in a no-network Shadow and the account
stop/restore evidence is complete.
