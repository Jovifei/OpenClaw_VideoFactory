# P0 Remaining Actions V10

1. Jovi must verify in the existing zhongshu Feishu App that `card.action.trigger` is subscribed and published over the current WebSocket mode; do not add a second `im.message.receive_v1` subscription or switch transports yet.
2. Resolve a supported direct deterministic project handler. The current OpenClaw core path is synthetic-command/Router based and is prohibited for this task; do not modify OpenClaw core or add a competing consumer.
3. After an approved handler path exists, authorize the exact project code directories before implementing card builder, ticket store, callback verifier, worker, updater, and tests.
4. Run the complete offline/fake card suite, then a controlled fake smoke. Do not send a real attachment until the fake path proves callback, ticket, Analyzer, card update, and idempotency behavior.
5. Preserve R3 FAIL, keep R4/R5 and final P0 Gate blocked, and do not enter P1.
