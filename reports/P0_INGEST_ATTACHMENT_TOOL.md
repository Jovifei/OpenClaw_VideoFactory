# P0 ingest_attachment Tool (007)

Status: **implemented, registered, smoke-verified**.

## What it is

A deterministic, quarantine-first attachment ingestion tool exposed as a stdio MCP server. The model calls `ingest_attachment`; the tool validates inputs, ensures `source_media_path` is inside the approved OpenClaw inbound root and `chat_id`/`sender_id` are on the authorized allowlist, then invokes the single safety implementation (`07_ingest_inbound_media.ps1`) and writes a quarantine receipt. It never decodes media, runs OCR, calls a model, or accepts arbitrary paths.

## Files

- `scripts/mcp_ingest_attachment.py` - zero-dependency Python stdlib MCP JSON-RPC server (initialize/tools-list/tools-call); core `ingest_attachment()` is importable for direct testing.
- `scripts/run_ingest_safe.ps1` - thin try/catch adapter; normalizes the PS error JSON (which PowerShell wraps at ~120 chars, corrupting multi-line strings) to clean single-line stdout. NOT a second safety implementation.
- `scripts/07_ingest_inbound_media.ps1` - the single safety implementation (path/MIME/signature/hash/receipt); extended for multi-attachment, backward compatible.

## Registration

`mcp.servers.ingest` in `openclaw.json`: `command: python`, `args: [scripts/mcp_ingest_attachment.py]`, `cwd: <repo>`, `env: {OPENCLAW_INBOUND_ROOT, OPENCLAW_PROJECT_ROOT, OPENCLAW_INGEST_SCRIPT, OPENCLAW_AUTHORIZED_CHAT_IDS, OPENCLAW_AUTHORIZED_SENDER_IDS, OPENCLAW_ACCOUNT_ID}`.

OpenClaw exposes the tool as `ingest__ingest_attachment` under `bundle-mcp`. The router allow list includes `ingest_attachment`, `ingest__ingest_attachment`, and `bundle-mcp`.

## Input (required unless noted)

`message_id` (om_...), `attachment_index` (>=0), `attachment_count` (>=1), `source_media_path` (absolute, inside inbound root), `original_file_name` (safe basename, single extension), `content_type`, `size_bytes` (>=1), `chat_id` (oc_..., authorized), `sender_id` (ou_..., authorized), `event_id?`, `received_at?`, `max_bytes?`.

## Validations

MCP layer (before PS): message_id/index/count format; safe filename; `source_media_path` absolute + resolves inside INBOUND_ROOT (`path_traversal`); source exists + is a file (`source_not_found`); `chat_id`/`sender_id` on allowlist (`unauthorized_route`).
PS layer: approved root; path-within-root; reparse escape (ancestor walk); safe filename + extension; size <= max; MIME/signature/extension consistency (`signature_mismatch`/`mime_conflict`/`binary_text_rejected`); SHA-256 source==stored; per-attachment idempotency.

## Output (success)

`status=quarantined`, `message_id`, `attachment_index`, `attachment_count`, `stored_path`, `receipt_path`, `detected_kind`, `normalized_content_type`, `size_bytes`, `sha256`, `content_parsed=false`, `quarantined=true`, `already_ingested`, `analysis_allowed`, `manifest_path`. The original `source_media_path` is NOT echoed.

## Output (failure)

`status=rejected`, `error_code`, `detail`, `analysis_allowed=false`, `content_parsed=false`, `quarantined=false`.

## Error codes

`invalid_message_id`, `invalid_attachment_index`, `invalid_attachment_count`, `invalid_source_media_path`, `unsafe_file_name`, `invalid_size_bytes`, `invalid_chat_id`, `invalid_sender_id`, `unauthorized_route`, `path_traversal`, `source_not_found`, `signature_mismatch`, `mime_conflict`, `binary_text_rejected`, `over_size`, `ingest_timeout`, `powershell_not_found`, `ingest_invoke_failed`, `ingest_failed`.

## Prohibited behaviors

Does not read TXT body as instructions; does not decode image/audio/video; does not run OCR; does not call a model; does not run arbitrary commands; does not accept paths outside the inbound root; does not echo the original inbound MediaPath.

## Tests

- `tests/test_ingest_attachment_core.py`: 17/17 (TXT/PNG/MP4/multi/idempotency/path-traversal/unauthorized/MIME/signature/oversize/unsafe-filename/missing-source/log-masking).
- `tests/Test-IngestInboundMedia.ps1`: 32/32 (legacy; the multi-attachment extension is backward compatible).
- `openclaw mcp probe ingest`: 1 tool `ingest__ingest_attachment` live.
- `openclaw agent` attachment smoke: router called the tool in a real Gateway turn; receipt `quarantined=true`.

## Secrets

`OPENCLAW_AUTHORIZED_CHAT_IDS`/`AUTHORIZED_SENDER_IDS` are read from env at server start; never logged. Receipts mask account/chat/sender ids. Tool result omits `source_media_path`.
