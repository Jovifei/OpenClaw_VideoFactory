# P0 Multi-Attachment Contract

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Implementation: `scripts/07_ingest_inbound_media.ps1` (extended), `scripts/mcp_ingest_attachment.py` (manifest), `scripts/run_ingest_safe.ps1` (adapter)
Status: **implemented; 32/32 legacy regression still passes; 17/17 ingest-attachment core tests pass**

## Goal

A single Feishu message may carry multiple attachments. Each attachment must be ingested, receipted, and analyzed independently, with a message-level manifest tying them together. The legacy single-attachment layout must remain byte-compatible so the existing 32-test regression is not broken.

## Directory layout

### Legacy single-attachment (unchanged, `AttachmentIndex` absent)

```
input/feishu/<message-id>/
├── original/<original-file-name>
└── receipt.json
```

### Multi-attachment (`AttachmentIndex` provided, 0-based)

```
input/feishu/<message-id>/
├── message_manifest.json
├── attachment-000/
│   ├── original/<original-file-name>
│   └── receipt.json
├── attachment-001/
│   ├── original/<original-file-name>
│   └── receipt.json
└── ...
```

`attachment-NNN` uses 3-digit zero-padded index (`attachment-{0:D3}`).

## Per-attachment receipt

Each `attachment-NNN/receipt.json` is independent and carries: `message_id`, `attachment_index`, `attachment_count`, `event_id`, `original_name`, `source_path`, `stored_path`, `content_type`, `extension`, `size_bytes`, `sha256`, `received_at`, `quarantined=true`, `content_parsed=false`, `processing_policy`, plus masked `account_id`/`chat_id`/`sender_id`.

## Message manifest

`input/feishu/<message-id>/message_manifest.json`:

```json
{
  "message_id": "om_...",
  "attachment_count": 2,
  "account_id": "zhongshu",
  "chat_id_masked": "oc_***...1555",
  "sender_id_masked": "ou_***...ada9",
  "last_updated": "2026-07-18T...Z",
  "attachments": [
    {
      "attachment_index": 0,
      "original_name": "a.txt",
      "stored_path": ".../attachment-000/original/a.txt",
      "receipt_path": ".../attachment-000/receipt.json",
      "sha256": "...",
      "size_bytes": 123,
      "detected_kind": "txt",
      "normalized_content_type": "text/plain",
      "content_parsed": false,
      "quarantined": true,
      "idempotent": false,
      "status": "quarantined",
      "ingested_at": "2026-07-18T...Z"
    }
  ]
}
```

The manifest is updated atomically (temp + `os.replace`) by `mcp_ingest_attachment.py` after each successful attachment ingest.

## Idempotency and ordering

| Scenario | Behavior |
| --- | --- |
| Same `message_id` + same `attachment_index` + same hash (re-delivery) | idempotent; returns existing `stored_path`/`receipt_path`; `already_ingested=true`; no new copy |
| Same `message_id` + same `attachment_index` + different hash | rejected as a collision (the PS script's existing `MessageId collision` guard, now scoped to the per-attachment receipt path) |
| Same `message_id` + different `attachment_index` | independent receipts; both kept |
| Same hash, different `message_id` | independent (different message root) |
| Same `original_file_name` within a message, different index | allowed (different `attachment-NNN` dirs) |
| Attachment events arrive out of order | the manifest sorts entries by `attachment_index`; `attachment_count` is taken from the last successful ingest |
| Partial success (one attachment fails MIME/signature) | that attachment is `rejected`; the others are still ingested; the manifest records only successful attachments |
| Duplicate event for an already-ingested attachment | idempotent; manifest entry replaced in place |

## Backward compatibility

- The 32-test regression (`tests/Test-IngestInboundMedia.ps1`) calls `07_ingest_inbound_media.ps1` without `AttachmentIndex`, so it hits the legacy branch: `input/feishu/<message-id>/original/<name>` + `input/feishu/<message-id>/receipt.json`. Verified **32/32 pass** after the extension.
- The new fields added to the receipt (`attachment_index`, `attachment_count`, `event_id`) are `null`/defaults in legacy mode; existing receipt-field assertions are unaffected.
- The stdout JSON adds `detected_kind`, `normalized_content_type`, `attachment_index`, `content_parsed`, `quarantined`; these are additive and do not break existing assertions on `success`/`idempotent`/`sha256`/`stored_path`/`receipt_path`/`size_bytes`.

## Migration

No migration is required for existing single-attachment receipts: they remain at `<message-id>/receipt.json` and are readable as before. A message-level manifest is only written when at least one attachment is ingested through the MCP tool (the manifest writer lives in the MCP server, not in the PS script, so direct PS invocations are unaffected).

## Tests

- `tests/test_ingest_attachment_core.py::test_multi_attachment_manifest` - two attachments, manifest has 2 sorted entries.
- `tests/test_ingest_attachment_core.py::test_same_message_different_index_independent` - same message, different index -> independent stored paths.
- `tests/test_ingest_attachment_core.py::test_idempotent_same_message_index_hash` - re-delivery is idempotent.
- `tests/Test-IngestInboundMedia.ps1` - 32/32 legacy unchanged.
