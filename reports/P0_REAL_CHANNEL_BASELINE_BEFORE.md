# P0 Real-Channel Qualification - BASELINE BEFORE (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Captured: 2026-07-18
Status: **BASELINE_CAPTURED_008_INDEPENDENT_REVIEW_PASSED**

This baseline was captured by independently re-verifying the live production config (not relying on the 007 summary). The 007 production state is intact; no drift since 007.

## 1. OpenClaw config (live, independently verified)

| Field | Value |
| --- | --- |
| Path | `C:\Users\Admin\.openclaw\openclaw.json` |
| Current SHA-256 | `3001ec3b85a882deb382cb08f5ebdb1c6b285964ea9933f5f0d5c99bc7d89810` |
| 007 final SHA | `3001ec3b...` (matches - no drift) |
| 007 baseline SHA | `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d` |
| `openclaw config validate` | exit 0, "Config valid" |
| OpenClaw build | `2026.7.1 (2d2ddc4)` |
| openclaw package mtime | 2026-07-14 (pre-007; core source NOT modified) |

## 2. Gateway

| Field | Value |
| --- | --- |
| URL | `ws://127.0.0.1:18789` |
| Port probe | HTTP 200 (reachable) |
| Auth | token |
| `openclaw status` | 17 agents, sessions 30 |

## 3. Independent 20-item review (section 四)

| # | Item | Result |
| --- | --- | --- |
| 1 | durable video-factory model = mimo-v2.5-pro | PASS |
| 2 | no session override covering (override is pro, consistent with durable pro) | PASS |
| 3 | tools.media scope only denies target group | PASS |
| 4 | other groups default allow | PASS |
| 5 | Router tool policy is real technical allowlist | PASS |
| 6 | Router cannot use exec/shell/file/OCR/image/STT/video/web | PASS (deny group:runtime/fs/media/web/ui) |
| 7 | ingest_attachment visible in Gateway | PASS (mcp probe: 1 tool) |
| 8 | ingest_attachment not generic exec wrapper | PASS |
| 9 | source_media_path cannot be freely specified | PASS (MCP validates inbound root + authorized chat/sender) |
| 10 | 3 internal agents no binding | PASS (has_binding=False all 3) |
| 11 | image/video analyzer no pro fallback | PASS (fallbacks=[]) |
| 12 | faster-whisper + CUDA available | PASS (1.2.1, torch 2.11+cu128, cuda True, RTX4070S) |
| 13 | GPU lock available | PASS (4/4 tests in 007) |
| 14 | multi-attachment backward compatible | PASS (32/32 unchanged) |
| 15 | other 13 agents config hash unchanged | PASS (only video-factory model changed) |
| 16 | 14 bindings unchanged | PASS |
| 17 | 4 cron unchanged | PASS |
| 18 | target group single consumer | PASS |
| 19 | openclaw core source unmodified | PASS (pkg mtime pre-007) |
| 20 | no new network dependencies | PASS (Python stdlib only) |

**Result: ALL 20 PASSED. No critical defect. No corrective change request needed.**

## 4. Topology invariants (re-verified)

| Invariant | Value |
| --- | --- |
| Agents | 17 (14 original + 3 analyzers) |
| Bindings | 14 |
| Cron | 4 |
| Target-group consumer | 1 |
| 3 analyzers in bindings | False (all 3) |
| Other 13 agents mismatches | 1 (only video-factory model, intended) |

## 5. Test results (re-run, no regression)

| Suite | Passed | Total |
| --- | --- | --- |
| `tests/Test-SingleGroupMediaRouter.ps1` | 45 | 45 |
| `tests/Test-IngestInboundMedia.ps1` | 32 | 32 |
| `tests/test_ingest_attachment_core.py` | 17 | 17 |
| **Total** | **94** | **94** |

## 6. Current fixtures

`tests/fixtures/feishu_delivery/`: `p0-file-test.txt`, `p0-image-test.png`, `p0-video-test.mp4`, `p0-video-cover.png`, `fixture_manifest.json`. (Audio fixture `p0-audio-test.wav` to be added this round.)

## 7. Local runtime (re-confirmed)

- Python 3.14.2; Node 24.18.0.
- PyTorch 2.11.0+cu128; `torch.cuda.is_available()=True`; RTX 4070 SUPER.
- faster-whisper 1.2.1; ctranslate2 4.8.0.
- ffmpeg/ffprobe 8.1.1 at `C:\ffmpeg\bin\` (NOT on system PATH).
- No local VLM (Ollama CLI missing; Qwen2.5-VL weights not audited).

## 8. Git state

Branch `phase/p0-gate-correction`; no commits (untracked tree). No commit/tag/push this round.

## 9. Project manifest

`FILE_MANIFEST.txt` + `SHA256SUMS.txt` present. VERSION 2.4.0. `PROJECT_STATUS.yaml` phase P0, `not_started` (must not modify).

## Secrets policy

All apiKeys, appSecrets, gateway token, real target-group id, file_keys are masked in every report. Real identifiers live only in the live config and MCP server env.
