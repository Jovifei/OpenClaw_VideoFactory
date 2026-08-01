# P0 Final Cutover Command Reference 037

This is a reference to previously reviewed methods, not an execution grant.
Task 037 does not invoke any entry below.

| Purpose | Reviewed method | Required gate |
|---|---|---|
| Core stop | `channels.stop(feishu, zhongshu)` | authenticated `operator.admin`, exact target, T0 authority |
| Project preflight/start path | `scripts/feishu_gateway/start_gateway.ps1` | Token injected; preflight health; zero-consumer proof before a future production start |
| Core verification | `scripts/migration/inspect_core_feishu_runtime.py` | authenticated state plus manual uniqueness confirmation |
| Final cutover gate | `scripts/migration/final_cutover_precheck.py` | all six booleans true |
| Project stop | `scripts/feishu_gateway/stop_gateway.ps1` | rollback authority and Project target confirmation |
| Core restore | `channels.start(feishu, zhongshu)` | authenticated `operator.admin`, exact target, rollback authority |

The installed OpenClaw source documents target-scoped start/stop and
`operator.admin`. The current project production wrappers remain guarded and
the 033 control helpers reject `--execute`; no reference above claims a live
production command has been qualified. Do not add `--token` to any command.
