# Migration Gap Analysis 021

Status: `FEISHU_GATEWAY_MIGRATION_BLOCKED`.

1. **Project Gateway launcher:** no production launcher, service definition, PID ownership, log destination, readiness probe, or graceful shutdown command exists under `services/feishu_gateway`. The offline classes are not an executable long-running service.
2. **OpenClaw RPC:** the project has a fail-closed abstract contract (session key `feishu:group:<chat>` and bounded retries), but no verified endpoint, authentication transport, cancellation contract, or streaming/final-response adapter. This cannot be inferred safely from an offline contract.
3. **Feishu connection:** the existing core `zhongshu` channel is running. The application identity is deliberately redacted; a maintenance operator must confirm it. Local status cannot prove a remote WebSocket has exited, so old-consumer exit requires process plus Feishu-admin/operator evidence.
4. **Rollback:** the Runbook describes order only. There is no approved command-level restoration procedure or recovery-time objective. The maximum safe recovery time is therefore unknown, not “instant”.

Blocking resolution requires a separately authorized launcher/RPC implementation package and an operator-approved command-level maintenance procedure. Do not stop the existing Binding until both exist and the authorization checklist is complete.
