# P0 Production Control Requirements 035

## Result

`PRODUCTION_CONTROL_BLOCKED`

OpenClaw 2026.7.1 implements target-scoped RPC handlers for
`channels.start` and `channels.stop`, including `channel` and `accountId`.
However, the current project control scripts still reject production
`--execute`, and the Project Gateway production transport is guarded.

## Current installed contract

| Operation | Required Gateway scope | Target |
|---|---|---|
| `channels.status` | `operator.read` | `feishu/zhongshu` |
| `channels.start` | `operator.admin` | `feishu/zhongshu` |
| `channels.stop` | `operator.admin` | `feishu/zhongshu` |

Installed source evidence:

- `dist/core-descriptors-DRUtdasO.js`: method-to-scope descriptors.
- `dist/channels-hpSo8J3l.js`: account-scoped start/stop handlers.
- `dist/call-dBhJbczL.js`: environment/shared-secret and stored operator-device
  authentication behavior.

## Requirements

1. RPC authentication: a valid token or approved stored operator-device
   credential; the project forbids command-line credentials.
2. Gateway authorization: an approved operator identity with
   `operator.admin`; a pending scope upgrade is not sufficient.
3. Local permission: standard-user permission to execute the installed
   OpenClaw CLI and connect to the loopback Gateway. Windows administrator
   rights are not required by the reviewed code path.
4. Special confirmation: an exact maintenance-window T0 confirmation, exact
   target `feishu/zhongshu`, fresh no-running-task proof, known Core owner, and
   rollback readiness.
5. Executable controls: reviewed project wrappers must allow one target-scoped
   stop and restore. The current 033 wrappers deliberately return
   `PRODUCTION_EXECUTION_DISABLED_033`.

No start/stop RPC was invoked during this audit.
