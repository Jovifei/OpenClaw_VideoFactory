# Feishu Gateway Maintenance Runbook V4 (032 draft)

This command-level draft is not authorization to execute a production cutover.
The account-runtime method remains Shadow-blocked.

## Targeted control contract

```text
T-10  record Gateway health and every Feishu account runtime status
T0    gateway call channels.stop {channel:feishu, accountId:zhongshu}
T+1   poll channels.status until zhongshu running=false and lastStopAt is fresh
T+2   independently prove consumer owner=none/zero before any Project Gateway
T+3   (future, only after Shadow qualification) start Project Gateway
rollback: stop Project Gateway -> prove consumer=zero -> gateway call channels.start
          {channel:feishu, accountId:zhongshu} -> verify Core owner restored
```

Stop/start is account-scoped and does not mutate configuration. Manual stop
persists until explicit start or Gateway restart. `channels remove`,
`plugins disable`, and a whole Gateway stop are prohibited substitutes.

## Fail-closed checks

Do not proceed if plugin/account status is unavailable, consumer ownership is
not independently observable, another Feishu account changes, the target does
not stop, WebSocket cleanup is not logged, or restore does not return the
original Core owner. Static config or `running=true` alone is not a WebSocket or
consumer proof.

## Current blocker

The no-network Shadow Gateway starts, but Feishu is not loaded (`0 plugins`), so
T0/T+1/rollback have not been run even in Shadow. Production remains untouched.
