# P0 Core Control Contract Final 036

## Current state

`PRODUCTION_CONTROL_CONTRACT_DOCUMENTED_NOT_EXECUTABLE`

| Item | `channels.stop` | `channels.start` |
|---|---|---|
| Entry | `openclaw gateway call channels.stop` | `openclaw gateway call channels.start` |
| Target parameters | `channel=feishu`, `accountId=zhongshu` | same |
| Scope | `operator.admin` | `operator.admin` |
| Authentication | valid Gateway token or approved operator-device credential | same |
| Expected result | target-scoped stopped result | target-scoped started result |
| Verification | authenticated status + manual uniqueness confirmation | same |

Installed OpenClaw 2026.7.1 descriptors map `channels.status` to
`operator.read` and both lifecycle methods to `operator.admin`.

Failure handling is fail-closed: failed authentication/scope, unknown target
state, or non-zero Core count stops the procedure before Project start. A future
Project failure requires Project zero -> Core restore -> text, attachment, and
Session verification.

No control call was made. The reviewed 033 wrappers still return
`PRODUCTION_EXECUTION_DISABLED_033` for `--execute`; a separately authorized
execution task is required before this contract becomes executable.
