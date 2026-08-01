# P0 Core Consumer Observability Final 036

## Final status

`CORE_CONSUMER_OBSERVABILITY_LIMITED`

OpenClaw 2026.7.1 can expose authenticated account-scoped Core runtime state,
but does not expose a global consumer count, cross-process owner, or lease.
`running=true`/`connected=true` is therefore not converted into one consumer.

| Priority | Source | Can establish | Limitation |
|---:|---|---|---|
| 1 | authenticated `channels.status` | Core account lifecycle | no global count/owner |
| 2 | structured plugin runtime | Core connection timestamps | process-local only |
| 3 | process/socket evidence | one local connection | cannot prove absence of another |
| 4 | sanitized logs | lifecycle corroboration | historical/non-exclusive |

The project probe uses priority 1 and returns healthy only for explicit
`consumerCount=1`. Current read-only result is owner unknown/count unavailable
because the maintenance environment has no RPC credential.

Before T0 an authorized operator must retain sanitized authenticated status for
exactly `feishu/zhongshu` and make a time-bounded manual uniqueness
confirmation, repeated at T+1 and T+5. Missing or conflicting evidence blocks
the cutover. The independent audit is supporting review, not runtime proof.
