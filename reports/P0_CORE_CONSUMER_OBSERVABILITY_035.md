# P0 Core Consumer Observability 035

## Result

`CORE_CONSUMER_OBSERVABILITY_BLOCKED`

The read-only probe is implemented at
`scripts/migration/inspect_core_feishu_runtime.py`. Its only Gateway method is
`channels.status`; it cannot stop, start, or modify a channel or configuration.

## Output contract

The probe emits exactly:

```json
{
  "owner": "unknown",
  "consumer_count": null,
  "runtime_state": "unknown",
  "evidence_source": "CORE_CONSUMER_RUNTIME_OBSERVABILITY_UNAVAILABLE",
  "confidence": "low"
}
```

Known results are restricted to:

- `healthy`: account is running and the runtime supplies an explicit
  `consumerCount` of exactly one;
- `stopped`: account explicitly reports `running=false`, producing count zero;
- `unknown`: the RPC is unavailable, output is invalid/ambiguous, the target is
  absent/duplicated, or a running account does not expose an explicit consumer
  count.

A `running=true` flag alone is not converted into `consumer_count=1`.

## Live read-only evidence

- OpenClaw: `2026.7.1 (2d2ddc4)`.
- Probe exit: 2.
- Owner: unknown.
- Consumer count: unavailable.
- Runtime state: unknown.
- Evidence source:
  `CORE_CONSUMER_RUNTIME_OBSERVABILITY_UNAVAILABLE`.
- Project Gateway: stopped.

The maintenance process has no RPC credential, so the current Core owner and
consumer count remain unproven. No raw CLI error or protected value was
persisted.
