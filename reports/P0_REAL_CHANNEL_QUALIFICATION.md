# P0 Real-Channel Qualification (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **READY_FOR_REAL_CHANNEL_SEQUENCE** (all no-user work complete; R0-R5 require user uploads)
Date: 2026-07-18

This is the production qualification + stabilization follow-up to `P0-SINGLE-GROUP-MEDIA-ROUTER-007`. It does NOT re-architect; it independently re-verifies 007, builds real-Channel observability, prepares fixtures, validates local analyzer runtimes, captures lark-cli dry-run evidence, and runs a P0 Gate prereview. Real Feishu TXT/PNG/audio/MP4 event qualification (R0-R5) requires user uploads and is NOT faked.

## 22 required items

### 1. 上一轮生产变更独立复核
**PASS.** Independent 20-item review (`P0_REAL_CHANNEL_BASELINE_BEFORE.md`): durable model=mimo-v2.5-pro, scope deny target group only, tool policy enforceable, ingest_attachment visible + not exec wrapper, source_media_path validated, 3 analyzers no binding, image/video no pro fallback, faster-whisper+CUDA available, GPU lock available, multi-attachment backward compatible, other 13 agents unchanged, 14 bindings/4 cron unchanged, single consumer, core source unmodified, no new dependencies. No critical defect; no corrective CR needed.

### 2. 配置隐藏漂移
**None.** Current openclaw.json SHA `3001ec3b...` == 007 final SHA. `openclaw config validate` exit 0. `verify_007_invariants.py`: 17 agents / 14 bindings / 3 analyzers no binding / other 13 unchanged. No drift across the 3 restarts or since 007.

### 3. 3 次重启的影响
**No drift.** The 3 restarts (007: initial apply + group:plugins fix + bundle-mcp allow) each validated before apply; SHA stable after the 3rd. 008 added no restart. The config is the same as 007 final.

### 4. Haiku A-F 结果
A-E completed (`REAL_CHANNEL_{CONFIG,OBSERVABILITY,ROUTER_SECURITY,ANALYZER,TEST_MATRIX}_REVIEW.md`); F (P0 Gate) pending - covered by main-agent `P0_GATE_PREREVIEW`. See `P0_HAIKU_REAL_CHANNEL_REVIEW_SUMMARY.md`. Findings incorporated; analyzer agent-exec gap noted (P1 refinement).

### 5. TXT 真实事件
**NOT YET (R1).** Requires user upload `p0-file-test.txt`. Offline: TXT ingest is covered (32-test + 17-test). The router does not read TXT body (text-only model + ingest_attachment does not parse body).

### 6. PNG 真实入库
**NOT YET (R2).** Requires user upload `p0-image-test.png`. Offline + agent-turn smoke (007): PNG ingested to quarantined receipt. pre-ingest image understanding = 0 (config-verified + observability demo).

### 7. PNG 真实后置分析
**NOT YET (R3).** Requires user upload PNG + "please analyze" caption. Offline: image-analyzer runtime validated (`openclaw infer image describe` with mimo-v2.5, exit 0, no pro fallback).

### 8. 音频真实分析
**NOT YET (R4).** Requires user upload `p0-audio-test.wav` + caption. Offline: faster-whisper CUDA transcribed the fixture correctly (RTX 4070 SUPER, ~2GB VRAM, GPU lock acquired+released).

### 9. MP4 真实分析
**NOT YET (R5).** Requires user upload `p0-video-analysis-test.mp4` + caption. Offline: ffprobe + 3 CPU frames + audio extraction + faster-whisper on extracted audio (full video NOT uploaded to model; GPU lock for whisper).

### 10. pre-ingest 理解调用数
**0 (config-verified + observability demo).** `pre_ingest_media_understanding_count=0` in the event trace (no [Image]/[Audio]/[Video] blocks). Real-Channel direct count pending R0-R5.

### 11. Router 模型调用
`mimo-v2.5-pro` (text-only), `router_model_call_count=1` per turn. Verified in 007 text smoke + 008 observability demo.

### 12. MCP 入库调用
`openclaw mcp probe ingest` -> 1 tool `ingest__ingest_attachment` live. Called in agent-turn smoke -> quarantined receipt. `ingest_tool_call_count=1` (idempotent across N retries).

### 13. Analyzer 调用
Offline-tested 11/11 (Test-SingleGroupMediaRouter internal-analyzer block). Local runtime validated (faster-whisper CUDA + ffprobe + mimo-v2.5). Real-Channel analyzer dispatch pending R3/R4/R5.

### 14. raw inbound 路径泄漏
**false.** `raw_media_path_forwarded=false` (observability demo). Analyzers receive `stored_path` only (4-field contract). The tool result omits `source_media_path`.

### 15. GPU 锁
Available + tested 4/4 (Test-SingleGroupMediaRouter). Used in local audio/video validation (acquired+released). Single concurrency enforced.

### 16. 幂等
Verified (17/17 tests + observability demo: N ingest retries -> 1 receipt, `already_ingested`). `(message_id, attachment_index, sha256)` key. See `P0_REAL_CHANNEL_IDEMPOTENCY.md`.

### 17. lark-cli dry-run 证据
4 dry-runs (markdown/png/txt/mp4+cover), all exit 0, no actual send. Full command + stdout (API request) + stderr ("=== Dry Run ===") captured. See `P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.md`.

### 18. P0 Gate 预审
**BLOCKED** (11 passed / 2 conditional / 2 deferred / 11 blocked). Actual Gate NOT run; P0_READY NOT created. Codex CLI = `DEFERRED_BY_USER_UNTIL_MAINTENANCE_WINDOW`. Real lark-cli outbound = `blocked_user_authorization_required`. Real Channel = `blocked_real_channel_qualification_incomplete`. See `P0_GATE_PREREVIEW.md` + `P0_GATE_REMAINING_BLOCKERS.md`.

### 19. 当前 P0 状态
`conditional_not_passed`. P0 Gate not run; PROJECT_STATUS not updated (both prohibited this round).

### 20. 剩余 blocker
- B1: real Channel R0-R5 (user uploads) - PRIMARY
- B2: Feishu V2.5 evidence files (depend on B1)
- B3: real lark-cli outbound (user authorization)
- B4: ffmpeg PATH (maintenance window)
- D1/D2: Codex CLI (deferred)

### 21. 用户唯一下一步
Send plain text `P0_TEXT_ROUTER_TEST` to the VideoFactory Feishu group (R0). Await `TEXT_ROUTER_OK` confirmation, then upload `p0-file-test.txt` (R1), and so on per the R0-R5 protocol (one upload at a time, await confirmation).

### 22. 证据路径
- `reports/P0_REAL_CHANNEL_QUALIFICATION.json/.md` (this)
- `reports/P0_REAL_CHANNEL_BASELINE_BEFORE.json/.md`
- `reports/P0_REAL_CHANNEL_EVENT_TRACE.json/.md` + `scripts/observability/trace_event.py`
- `reports/P0_REAL_CHANNEL_FIXTURE_PREPARATION.md`
- `reports/P0_LOCAL_ANALYZER_RUNTIME_VALIDATION.json/.md`
- `reports/P0_REAL_CHANNEL_IDEMPOTENCY.md`
- `reports/P0_REAL_CHANNEL_NEGATIVE_TESTS.md`
- `reports/P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.json/.md`
- `reports/P0_GATE_PREREVIEW.json/.md` + `P0_GATE_REMAINING_BLOCKERS.md`
- `reports/P0_POST_MIGRATION_AUDIT.json/.md`
- `reports/P0_HAIKU_REAL_CHANNEL_REVIEW_SUMMARY.md`
- `reports/P0_CURRENT_STATUS_V6.md/.json`, `P0_EVIDENCE_INDEX_V6.md`, `P0_REMAINING_ACTIONS_V6.md`, `NEXT_USER_ACTION.md`
- `reports/change_requests/P0-REAL-CHANNEL-QUALIFICATION-008.json`
- `reports/child_claude/REAL_CHANNEL_*.md` (5/6; F pending)
- `tests/fixtures/feishu_delivery/{p0-audio-test.wav,p0-video-analysis-test.mp4,fixture_manifest.json}`

## Prohibitions honored

No commit/tag/push; no PROJECT_STATUS update; no P0_READY; no P0 Gate run; no P1; no model download; no real Feishu outbound; no fake real Feishu event; no OAuth/Binding/Cron change; no core source change; no new dependency.

## Final status

**READY_FOR_REAL_CHANNEL_SEQUENCE** - all no-user work complete. The single next action is the user sending `P0_TEXT_ROUTER_TEST`.
