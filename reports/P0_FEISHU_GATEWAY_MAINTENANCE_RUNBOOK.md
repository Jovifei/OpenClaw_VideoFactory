# Project Feishu Gateway Maintenance Runbook

## Before

1. Take a redacted backup and record configuration hash; confirm approved environment secrets are available without printing them.
2. Confirm Gateway health, no scheduled/active workload, current message volume, and the exact existing Binding.
3. Confirm the old Binding is the only active consumer and the project Gateway is stopped.

## Migration

1. Stop the old Feishu Binding through the approved operator procedure.
2. Prove its consumer and WebSocket are absent.
3. Start the project Gateway with environment-only secrets.
4. Prove exactly one consumer/WebSocket and its project identity.
5. Send one controlled text, one attachment, and one card action.
6. Verify session key, ingress receipt, card ticket binding, one reply per message, and no duplicate event.
7. Resume normal service only after the evidence is retained.

## Rollback

1. Stop the project Gateway.
2. Restore the old Binding and its Gateway service.
3. Prove one old consumer, text/attachment/session health, and no duplicate reply.
4. Record timestamps, hashes, sanitized event identifiers, and the rollback reason.
