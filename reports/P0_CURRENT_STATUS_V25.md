# P0 current status V25

`GATEWAY_AUTH_RESYNC_NOT_STARTED:SAFE_RESTART_REJECTED`

043B proved that a user-scope credential can be injected into a one-use
maintenance child without changing the parent environment or exposing the
credential. The single safe restart command was rejected with exit code `1`;
the old healthy Gateway, Core Feishu zhongshu, and zero Project Gateway state
were preserved. The health-only Adapter probe observed `AUTH_TOKEN_MISMATCH` on
that unchanged runtime.

No migration, P0 Gate, R0-R5, configuration, Binding, Agent, Cron, OAuth,
model, Git, or real Feishu action occurred.
