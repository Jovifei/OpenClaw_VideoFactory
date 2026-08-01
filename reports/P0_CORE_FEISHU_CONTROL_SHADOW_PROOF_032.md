# P0 Core Feishu Control Shadow Proof 032

Status: `CORE_FEISHU_SHADOW_VALIDATION_BLOCKED`

## Passed

1. A structured Shadow fixture with disabled Feishu transport and fake-token
   markers passed `openclaw config validate` (exit 0).
2. An isolated Gateway used loopback port `19432`; the port became reachable and
   `gateway health --json` exited 0.
3. Shadow state was separate from production state selection; no real
   credentials or Feishu network was enabled.
4. Installed source proves the target-account stop/start path: Core aborts the
   selected task, and Feishu cleanup closes/removes the WebSocket client.

## Blocked

The isolated Gateway reported `0 plugins`. `plugins list` and `channels status`
did not expose a Feishu channel/account. The following are therefore not proven
and were not executed: Feishu plugin load/unload, zhongshu stop, WebSocket
cleanup, restore, and non-target account invariance.

The plugin-entry experiment was discarded because it emitted an automatic
missing-plugin installation diagnostic. The entry was removed and Shadow state
was cleared before the final probe.

## Fail closed

Static source evidence is not runtime/consumer evidence. Do not create or run
production cutover scripts, call real `channels.stop/start`, or claim migration
readiness until a no-network Shadow loads the Feishu plugin and demonstrates
account stop/restore.
