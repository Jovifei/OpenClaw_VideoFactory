# P0 Core Feishu Account Control Contract 033

Status: `CORE_FEISHU_HOT_DISABLE_CONTRACT_READY` in Shadow.

The qualified control surface is the real OpenClaw Gateway RPC method pair:

```text
channels.stop({channel: "feishu", accountId: "zhongshu"})
channels.start({channel: "feishu", accountId: "zhongshu"})
```

The Shadow RPC responses and channel status show that the selected account
changes running state while `shadow-secondary` remains disabled and stopped.
Repeated start and stop are idempotent. The control path does not rewrite
configuration. A whole-channel reload, plugin disable/remove, or Gateway stop
is broader than the requested account scope and is not part of this contract.

The contract is qualified only for a controlled maintenance window after an
explicit authorization, current consumer observation, backup, and rollback
check. The production control scripts remain fail-closed and read-only in this
task.
