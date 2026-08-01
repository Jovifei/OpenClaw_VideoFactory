# P0 Test Results (007)

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Runner: Pester 3.4.0 (PowerShell) + Python unittest (stdlib)
Total: **94/94 passed, 0 failed**

## Suites

| Suite | Passed | Total | Notes |
| --- | --- | --- | --- |
| `tests/Test-SingleGroupMediaRouter.ps1` | 45 | 45 | 15 original + 5 scope + 10 router-policy + 11 internal-analyzer + 4 GPU-lock |
| `tests/Test-IngestInboundMedia.ps1` | 32 | 32 | legacy regression; unchanged by multi-attachment extension |
| `tests/test_ingest_attachment_core.py` | 17 | 17 | ingest tool contract (TXT/PNG/MP4/multi/idempotency/path-traversal/unauthorized/MIME/signature/oversize/unsafe-filename/missing-source/log-masking) |

## Task-plan coverage (section 十五)

### Scope (5) - in Test-SingleGroupMediaRouter.ps1
1. target group image pre-understanding=0 (scope deny)
2. target group audio pre-understanding=0
3. target group video pre-understanding=0
4. other groups keep default behavior (default allow)
5. keyPrefix sibling (similar but not matching) unaffected

### Router (10)
6. durable model = mimo-v2.5-pro
7. no multimodal model in fallbacks
8. text model call = 1 (verified live in text smoke)
9. ordinary text session continuous
10. attachment calls ingest_attachment first (pre-dispatch count 0)
11. ingest failure -> no dispatch
12. receipt success -> dispatch exactly one analyzer
13. analyzer never receives raw MediaPath
14. router denies media tools (image/video_generate)
15. router denies exec

### Ingest Tool (16) - in test_ingest_attachment_core.py + Test-IngestInboundMedia.ps1
16-31: TXT, PNG, MP4, multi-attachment, Chinese filename (32-test), MIME conflict, signature error, path traversal, reparse (32-test), oversize, message_id idempotent, attachment_index idempotent, same-name-diff-hash, same-hash-diff-message, receipt failure, log masking.

### Internal Agents (11) - in Test-SingleGroupMediaRouter.ps1
32-42: PNG->image-analyzer only, audio->audio-analyzer only, MP4->video-analyzer only, analyzer input 4 fields only, image fail no pro fallback, GPU lock single concurrency, stale GPU lock recovery, other agents unaffected, internal agents no binding, target group 1 consumer, final reply to original group.

## Metrics recorded

`pre_ingest_media_understanding_count`, `router_model_call_count`, `ingest_tool_call_count`, `analysis_agent_call_count`, `image_analysis_count`, `audio_transcription_count`, `video_analysis_count`, `raw_media_path_forwarded`, `stored_path_forwarded`, `gpu_lock_acquired`, `binding_count`, `consumer_count`.

## Reproduction

```powershell
Invoke-Pester -Path tests/Test-SingleGroupMediaRouter.ps1 -PassThru -Quiet  # 45/45
Invoke-Pester -Path tests/Test-IngestInboundMedia.ps1 -PassThru -Quiet      # 32/32
python tests/test_ingest_attachment_core.py                                  # 17/17
```
