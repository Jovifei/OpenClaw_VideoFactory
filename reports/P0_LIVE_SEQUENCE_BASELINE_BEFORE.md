# P0 Live-Sequence Baseline Before (009)

Task: `P0-LIVE-SEQUENCE-ANALYZER-009`
Captured: 2026-07-18
Status: **BASELINE_CAPTURED_009**

## openclaw.json (unchanged from 008)

- SHA-256: `3001ec3b85a882deb382cb08f5ebdb1c6b285964ea9933f5f0d5c99bc7d89810`
- config valid; Gateway port 18789 reachable.
- 17 agents, 14 bindings, 4 cron, 1 target-group consumer.
- Router: mimo-v2.5-pro (text-only), tool allowlist (11 allow / 10 deny), scope deny target group.
- 3 analyzers: no binding, exec.mode=deny, allow=[read,write] (GAP: cannot invoke faster-whisper/ffprobe).
- MCP: ingest server live (1 tool); analyzer MCP tools NOT yet (009 phase C).

## R1 failure diagnosis (the trigger for this round)

- R1 TXT upload returned `path_traversal - 文件路径不在允许的入站根目录内`.
- Root cause: 007/008 set `mcp.servers.ingest.env.OPENCLAW_INBOUND_ROOT = C:\Users\Admin\.openclaw\media\inbound`, but the Feishu Channel stages video-factory attachments to the workspace `media/inbound` (`E:\project\OpenClaw_VideoFactory\media\inbound\openclaw-staged-<guid>\<file>`).
- The router passed the workspace-staged path; the MCP server's single-root check rejected it.
- Fix: code-only multi-root support in `mcp_ingest_attachment.py` (accept env root + OPENCLAW_INBOUND_ROOTS + CWD/media/inbound; forward matching root to the PS script). No config change. Verified: 17/17 tests pass + workspace-root ingestion returns quarantined.

## Fixtures (SHA-256)

- p0-file-test.txt: c8a155b4d5eccafd2b36758b9fa67af186174dfe6e99e184b56231bd8382663d
- p0-image-test.png: 624223e0f8d14374d40301574b721c9debd46d4168ad4c44d06767e5f74a4214
- p0-audio-test.wav: cc08486c989b5b6004f96ca6c5b102503852c76e709dee165d0e10408c287b6b
- p0-video-analysis-test.mp4: ca844094b316103d6084b59936685c1be8037174044cf4a2d4041db6acb689fc

## Tests (94/94)

Router 45, Ingest 32, IngestTool 17.

## Local runtime

faster-whisper 1.2.1 + torch 2.11+cu128 (CUDA True, RTX4070S); ffmpeg 8.1.1 at C:\ffmpeg\bin (not PATH); mimo-v2.5 cloud multimodal verified.

## Haiku sub-agents

FAILED (429 weekly quota exceeded, resets 2026-07-20). Main agent performs reviews inline per task rule.

## P0 status

`conditional_not_passed`. P0 Gate not run; PROJECT_STATUS not updated.

## Secrets policy

All masked.
