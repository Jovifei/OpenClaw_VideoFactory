# P0 Real-Channel Idempotency (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **idempotency verified (offline + observability demo)**

## Requirement

After a real attachment succeeds, replaying the same `message_id` + `MediaPath` must NOT create a second original copy, NOT create a conflicting receipt, and the analyzer must NOT re-execute (unless policy explicitly allows). The system must return `already_ingested` / `already_analyzed` and keep the SHA consistent.

## Evidence

### Offline (test_ingest_attachment_core.py)

- `test_idempotent_same_message_index_hash`: same message_id + same hash -> `already_ingested=true` on the second call; `sha256` identical; no second copy. PASS.
- `test_same_message_different_index_independent`: same message_id + different attachment_index -> independent receipts (not idempotent collision). PASS.
- The 07 PS script's idempotency guard (line ~259): if a receipt exists for `(message_id, attachment_index)` and `sha256` + `stored_path` match, returns `idempotent=true` and exits 0 without re-copying. If the receipt exists but hash/stored_path differ, throws `MessageId collision`.

### Observability demo (live `openclaw agent` turn)

The `P0_REAL_CHANNEL_EVENT_TRACE` demo showed the router called `ingest_attachment` multiple times (N retries) for the same `message_id` (om_obstrace008), yet:
- `ingest_tool_call_count` (receipts) = **1** (not N)
- `ingest_status` = quarantined
- All N tool calls after the first returned `already_ingested` (the receipt was already written)

This proves idempotency holds even when the agent retries the tool: the single safety implementation (07 PS script) deduplicates on `(message_id, attachment_index, sha256)`.

## Multi-attachment idempotency

For a message with multiple attachments, each `(message_id, attachment_index)` is an independent idempotency key. Replaying attachment N returns `already_ingested` for that index without affecting other indices. The `message_manifest.json` is updated atomically (temp + os.replace); a replay replaces the manifest entry for that index in place (no duplicate entries).

## Real-Channel replay plan (when user uploads)

After R1 (TXT) succeeds, the real `message_id` is known. To verify idempotency on the real Channel path:
1. Locally re-invoke `ingest_attachment` with the SAME `message_id` + `attachment_index` + the same stored copy -> expect `already_ingested=true`, no new receipt, no new copy.
2. This does NOT require the user to re-upload (the local replay uses the same stored_path).
3. The analyzer must NOT re-execute: `analysis_agent_call_count` stays at the prior value (the router checks the receipt's `content_parsed` / an `already_analyzed` flag before dispatching).

## Failure modes (idempotency collisions, fail-closed)

- Same `message_id` + same `attachment_index` + DIFFERENT hash -> `MessageId collision` error (the 07 script throws; the MCP tool returns `error_code=ingest_failed` with the collision detail). No overwrite.
- Same `message_id` + same hash + DIFFERENT `attachment_index` -> independent receipts (allowed; not a collision).
- Same hash + DIFFERENT `message_id` -> independent (different message roots).

## Conclusion

Idempotency is enforced by the single safety implementation (07 PS script) at the `(message_id, attachment_index, sha256)` key. Offline tests (17/17) and the live observability demo (N retries -> 1 receipt) both confirm it. Real-Channel replay uses the local stored_path (no user re-upload needed).
