# Trusted Command Envelope Contract 052

## Active status

**Not established.**  This is a required future contract shape, not an active
project implementation.  P0 cannot safely instantiate it because OpenClaw
2026.7.1 does not deliver a trusted current-message/current-turn capability to
the local stdio MCP server.

## Required future runtime-owned envelope

```json
{
  "schema_version": "1.0",
  "channel": "feishu",
  "event_id": "runtime-owned-event-id",
  "message_id": "runtime-owned-message-id",
  "session_id": "runtime-owned-session-id",
  "turn_id": "runtime-owned-turn-id",
  "run_id": "runtime-owned-run-id",
  "chat_id": "runtime-owned-chat-id",
  "sender_id": "runtime-owned-sender-id",
  "raw_command_sha256": "sha256-of-original-message-body",
  "normalized_command_sha256": "sha256-of-approved-normalization",
  "received_at": "runtime-issued-time",
  "issued_at": "runtime-issued-time",
  "expires_at": "runtime-issued-time-short-ttl",
  "consumed_at": null,
  "one_time": true
}
```

The envelope must be created by authenticated Channel/Core runtime while it
holds original message bytes and delivered through an authenticated per-call
implicit capability.  The consumer must ignore caller provenance, derive
identity from that capability, compare the normalized model command with the
envelope hash, reject `command_source_mismatch` before Analyzer dispatch, and
consume the envelope once before short expiry.  A model argument, Router prompt,
session lookup, latest message, timestamp, or Project Gateway state never meets
this contract.
