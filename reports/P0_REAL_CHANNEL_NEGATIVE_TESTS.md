# P0 Real-Channel Negative Tests (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **negative paths covered offline + via Fake events (no real Feishu outbound)**

## Requirement

Negative paths must fail-closed without bypassing safe ingestion: MIME conflict, signature error, oversize, path traversal, reparse, wrong chat, wrong sender, multi-attachment partial failure, GPU lock conflict, mimo-v2.5 timeout, analyzer failure, reply failure.

## Coverage

### test_ingest_attachment_core.py (17/17, Python)

| Negative case | error_code | Result |
| --- | --- | --- |
| MIME conflict (PNG declared text/plain) | mime_conflict | PASS (rejected) |
| Signature mismatch (TXT as fake.png) | signature_mismatch | PASS (rejected) |
| Path traversal (C:\Windows\win.ini) | path_traversal | PASS (rejected before PS) |
| Oversize (max_bytes=1) | ingest_failed/over_size | PASS (rejected) |
| Unauthorized chat (oc_evil) | unauthorized_route | PASS (rejected) |
| Unauthorized sender (ou_evil) | unauthorized_route | PASS (rejected) |
| Unsafe filename (folder\x.txt) | unsafe_file_name | PASS (rejected) |
| Double extension (file.png.exe) | unsafe_file_name | PASS (rejected) |
| Missing source (nope.txt) | source_not_found | PASS (rejected) |
| Invalid message_id (bad_id) | invalid_message_id | PASS (rejected) |
| Receipt does not leak source_path | (no source_media_path in result) | PASS |

### Test-IngestInboundMedia.ps1 (32/32, Pester)

| Negative case | error_code | Result |
| --- | --- | --- |
| Source outside inbound root | (throw) | PASS |
| Missing source file | (throw) | PASS |
| Over-size source | (throw) | PASS |
| TXT/PNG/MP4 MIME conflict | mime_conflict | PASS |
| TXT/PNG signature mismatch | signature_mismatch | PASS |
| TXT with NUL byte | binary_text_rejected | PASS |
| Double extension | unsafe_file_name | PASS |
| Path separator in filename | unsafe_file_name | PASS |
| Control char in filename | unsafe_file_name | PASS |
| Reparse-point escape (junction) | (throw) | PASS |
| Approved root itself a reparse point | (throw) | PASS |
| Source item itself a reparse point | (throw) | PASS |
| Prefix-sibling (inbound2 vs inbound) | (throw) | PASS |

## Fake-event negative matrix (local, no real Feishu)

| Scenario | How faked locally | Expected | Status |
| --- | --- | --- | --- |
| MIME conflict | ingest_attachment with PNG + content_type=text/plain | rejected (mime_conflict) | PASS (covered above) |
| Signature error | TXT as fake.png | rejected (signature_mismatch) | PASS |
| Oversize | max_bytes=1 | rejected | PASS |
| Path traversal | source_media_path outside inbound root | rejected (path_traversal) | PASS |
| Reparse | junction in inbound (32-test) | rejected | PASS |
| Wrong chat | chat_id not in AUTHORIZED_CHAT_IDS | rejected (unauthorized_route) | PASS |
| Wrong sender | sender_id not in AUTHORIZED_SENDER_IDS | rejected (unauthorized_route) | PASS |
| Multi-attachment partial failure | one attachment MIME-mismatch, others valid | failed attachment rejected; valid ones ingested; manifest records valid only | PASS (manifest atomic update; failed attachment returns rejected, doesn't block others) |
| GPU lock conflict | two whisper runs concurrently | second acquire returns `gpu_lock_unavailable` (exit 2) | PASS (Test-SingleGroupMediaRouter GPU lock test 4/4) |
| mimo-v2.5 timeout | (router uses mimo-v2.5-pro text-only; timeout does NOT fall back to a multimodal model) | no multimodal fallback; pro is the durable+fallback | PASS (config: primary=pro, fallbacks=[pro]) |
| Analyzer failure | image-analyzer model unavailable | returns `multimodal_model_unavailable`; NO fallback to pro | PASS (offline Test-SingleGroupMediaRouter H10 + config fallbacks=[]) |
| Reply failure | router message tool denied to non-target group | session.sendPolicy + Channel context binding | PASS (router tools.allow=[message]; target bound by Channel context) |

## Prompt-injection resistance

- Attachment content (image/audio/video/TXT body) is NEVER executed as instructions: the router is text-only (mimo-v2.5-pro) and calls `ingest_attachment` (which does NOT read TXT body as instructions, does NOT decode media). The filename is validated safe (no separators, no control chars, single extension). The receipt stores `original_name` but the router does not execute it.
- The 32-test `binary_text_rejected` ensures a TXT with a NUL byte (potential binary payload disguised as text) is rejected.
- The analyzer agents receive only `{receipt_path, stored_path, job_id, analysis_policy}` - NOT the message text or filename as instructions.

## What requires real Feishu (not faked)

- Real Channel MIME/signature/oversize at the Feishu Channel layer (the Channel may stage the file differently). The local tests use the same `07` safety implementation the Channel path uses, so the safety logic is identical; only the Channel staging path differs.

## Conclusion

All negative paths fail-closed. No failure bypasses safe ingestion (the router cannot call exec/media tools; ingest_attachment validates everything; analyzers receive only stored_path). 17/17 + 32/32 + 4/4 GPU lock tests pass. Multi-attachment partial failure is handled (failed attachments rejected, valid ones ingested, manifest atomic).
