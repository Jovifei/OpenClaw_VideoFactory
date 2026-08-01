# P0 Real Qualification Access Checklist

## Type-only requirements

The following approvals are required before the matrix can be executed. No values are requested or recorded in this report.

- [ ] Feishu test App permissions for long connection, message/file receipt and signed card callback.
- [ ] RPC access permission for an isolated OpenClaw endpoint using a non-production token provider.
- [ ] Dedicated test group permission for harmless TXT/PNG/card fixtures.
- [ ] Maintenance-window date/time, timezone, duration, observer and rollback owner.
- [ ] Explicit approval for a short stop of the approved test entry; production entry remains out of scope.

## Additional operator confirmations

- [ ] Test App/Bot/group are not production identities.
- [ ] The isolated Gateway config, PID, lease and logs do not share production paths.
- [ ] No token or secret will appear in shell history, logs, screenshots, reports or Git.
- [ ] No raw `chat_id`, `sender_id`, `message_id`, `file_key` or file content will appear in evidence.
- [ ] Rollback commands and recovery objective have been reviewed before T-10.

## Current state

All checklist items are unconfirmed in the current workspace. 027 is therefore preparation-only and cannot execute the real matrix.
