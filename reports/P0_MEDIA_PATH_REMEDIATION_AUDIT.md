# P0 Media Path Remediation Audit

Status: **superseded by [P0 Media Path Remediation Audit V2](P0_MEDIA_PATH_REMEDIATION_AUDIT_V2.md)**

The original discovery and evidence below are retained. `P0-MEDIA-MIME-001` repaired and verified the PNG MIME-policy gap; see the V2 audit and `P0_MEDIA_MIME_FIX.md` for the corrected conclusion.

No production code was changed. Only the generated N1 fixtures were used, and no real DOCX body was read or deleted.

## Existing tests

`Invoke-Pester -Script tests/Test-IngestInboundMedia.ps1 -PassThru` completed with **8 passed, 0 failed** and exit code 0.

## N2 required checks

All 14 requested checks produced passing evidence:

- Chinese filename, TXT, PNG and MP4 positive ingestion
- Missing path, oversize input, outside-root/path traversal and reparse escape rejection
- Duplicate `message_id` idempotency
- Source and quarantined-copy SHA-256 equality for all four positive cases
- All 18 receipt fields present
- `content_parsed=false` and `quarantined=true`
- Both stored originals and receipts ignored by Git, with zero tracked files

Stored paths were limited to `input/feishu/<generated-message-id>/` and are recorded only in redacted form. Fixture hashes match `fixture_manifest.json`.

## Additional safety finding

An extra negative probe supplied `text/plain` for `p0-image-test.png`. The script exited 0 and accepted it. The existing extension policy has explicit MIME checks for PDF, DOCX, TXT and MP4, but `.png` falls through the default branch.

This is reported as a known gap. It was not repaired or redesigned in this audit because the authorized N2 scope is review-only.

## Harness boundary

Two earlier supplemental harness attempts stopped on parent-side Windows PowerShell compatibility/error-capture issues after writing only ignored test evidence. No files were deleted. A final bounded continuation reused the four successful receipts and completed the remaining checks.
