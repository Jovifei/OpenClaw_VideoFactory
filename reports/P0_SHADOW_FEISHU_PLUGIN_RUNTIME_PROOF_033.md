# P0 Shadow Feishu Plugin Runtime Proof 033

Status: `PASS` — `SHADOW_FEISHU_PLUGIN_LIFECYCLE_READY`.

The byte-for-byte copy of the installed production-source Feishu plugin was
loaded by an isolated OpenClaw Shadow Gateway. The manifest and runtime entry
hashes are recorded in the origin audit. The Gateway log reports `1 plugin:
feishu` followed by `ready`, and the plugin list contains `feishu`.

The final run (00:40:16 Asia/Shanghai) is the bound evidence run. Its process
exit code was 1 because the probe intentionally terminates the Gateway after
the checks; `process_shutdown=true` and the loopback port was released.

The real Shadow Gateway RPC path exercised account-level `channels.start` and
`channels.stop` for `feishu/zhongshu`, including repeated start, repeated stop,
restart after stop, final stop, and controlled process shutdown. The disabled
`shadow-secondary` account remained stopped throughout. Shutdown preflight
reported zero active tasks.

The shutdown preflight returned `safe=true` with queue, pending replies,
embedded runs, cron runs, active tasks, and total active all zero. A per-PID
network guard produced 34 records, including both Gateway processes; the
Gateway aggregate recorded zero unexpected network access.

This proves the installed plugin and account-level lifecycle contract in
Shadow only. It does not prove authenticated Feishu delivery or authorize a
production cutover.

Evidence: `reports/P0_FEISHU_PLUGIN_ORIGIN_AUDIT_033.json`,
`reports/P0_SHADOW_FEISHU_PLUGIN_LIFECYCLE_033.json`, and the redacted Shadow
probe artifacts under `experiments/core_feishu_control_contract/shadow/`.
