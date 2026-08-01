# P0 Media MIME Fix

Status: **fixed and verified** for `P0-MEDIA-MIME-001`.

The ingestion script now requires agreement between the supplied filename extension, normalized Channel `ContentType`, and a minimal safe signature probe for P0 TXT, PNG, and MP4. It still uses the Channel-provided `MediaPath` and validates before creating an `original/` copy or successful receipt.

## Evidence

- Script and test PowerShell parsing: passed.
- Existing ingestion coverage: **8/8 passed**.
- New MIME/safe-filename coverage: **20/20 passed**.
- Complete suite: **28/28 passed**, 0 failed.
- OpenClaw configuration SHA-256 remained `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`.

## PNG wrong-MIME regression proof

A valid PNG fixture declared as `text/plain` returned the following safe failure object:

```json
{"error_code":"mime_conflict","extension":".png","normalized_content_type":"text/plain","detected_kind":"png","expected_kind":"png","message_id":"om_pngwrongmime123"}
```

Neither `original/` nor `receipt.json` was created for that failed ingest.

## Scope boundary

Only `scripts/07_ingest_inbound_media.ps1`, `tests/Test-IngestInboundMedia.ps1`, the change request, backups, and this remediation's reports changed. No real Feishu call, P0 Gate, Codex CLI command, or OpenClaw configuration/runtime/OAuth/Cron operation was performed.
