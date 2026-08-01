# P0 Feishu Gateway Maintenance Runbook V6

This Runbook is an execution contract, not execution authorization. Task 035
must stop before T0.

## T-60 — RPC credential injection

1. Inject the OpenClaw RPC credential through an approved inherited environment,
   Windows Credential Manager adapter, or Secret provider.
2. Confirm the token is absent from process command lines, logs, reports, Git,
   and plaintext configuration.
3. Start only `production-preflight`.
4. Require authenticated RPC `health` and `ready=true`.
5. On missing/rejected credentials, stop preparation with
   `ZHONGSHU_RPC_CREDENTIAL_BLOCKED`.

## T-30 — Core consumer observability

1. Run `inspect_core_feishu_runtime.py`.
2. Require owner `openclaw_core_feishu`, `consumer_count=1`,
   `runtime_state=healthy`, and high-confidence runtime evidence.
3. A running flag without an explicit consumer count is insufficient.
4. On unknown output, stop with `CORE_CONSUMER_OBSERVABILITY_BLOCKED`.

## T-10 — Final maintenance gate

Require all of the following:

- RPC preflight remains ready.
- Core owner and count are known.
- Project production Gateway is stopped.
- No task or media operation is running.
- Rollback file and target-scoped restore control are available.
- `channels.stop/start` authentication has approved `operator.admin`.
- The exact `feishu/zhongshu` target and one-consumer invariant are confirmed.

Any failure stops before T0.

## T0 — Stop Core

Only in a separately authorized execution task:

1. Invoke one target-scoped `channels.stop` for `feishu/zhongshu`.
2. Record a sanitized timestamp and result.
3. Prove owner `none` and consumer count zero.
4. If zero is not proven, do not start Project Gateway; restore Core if needed.

## T+ — Start Project

Only after zero-consumer proof:

1. Start the real `production` Project Gateway.
2. Require PID, health, ready, authenticated RPC, and one real Feishu consumer.
3. Run text, TXT, PNG, and card verification in the approved order.
4. Roll back immediately on any configured failure condition.

## Rollback

Stop Project Gateway, prove its consumer count is zero, restore Core
`feishu/zhongshu`, and verify text, attachment, and Session continuity. Never
run both consumers concurrently and never auto-fallback while Project remains
connected.
