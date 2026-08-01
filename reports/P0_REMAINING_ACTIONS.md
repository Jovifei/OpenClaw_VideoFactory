# P0 Remaining Actions

## Next user action

Follow `reports/READY_FOR_FEISHU_MEDIA_TEST.md` and upload the three generated attachments separately to the dedicated **OpenClaw VideoFactory** group:

1. `p0-file-test.txt`
2. `p0-image-test.png`
3. `p0-video-test.mp4`

Do not add an `@`, explanatory text or rich-text wrapper.

## Remaining operator/implementation work

1. Capture native TXT, PNG and MP4 inbound events and ingest receipts without polling or reading media content as instructions.
2. Create a separate approved code-change request for the disclosed PNG MIME mismatch gap before changing `scripts/07_ingest_inbound_media.ps1`.
3. Retry lark-cli dry-runs individually with bounded execution. Do not perform actual sends until all four have complete exit-0 results.
4. Keep the Codex CLI upgrade and both direct CLI smokes deferred until Jovi sends `开始Codex CLI维护窗口`.
5. Run the final P0 Gate only after all required evidence is complete.

P0_READY, `PROJECT_STATUS.yaml`, commit/tag creation and P1 entry remain prohibited.
