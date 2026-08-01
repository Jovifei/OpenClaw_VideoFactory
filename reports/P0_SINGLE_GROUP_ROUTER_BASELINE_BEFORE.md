# P0 Single-Group Media Router — BASELINE BEFORE (007)

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Captured: 2026-07-18
Status: **BASELINE_CAPTURED_BEFORE_ANY_PRODUCTION_CHANGE**

This baseline was captured by reading the real `C:\Users\Admin\.openclaw\openclaw.json`, the video-factory agent `models.json`, the live `sessions.json`, the OpenClaw 2026.7.1 docs, and the installed runtime. No production change has been made. All secrets and the real target-group id are masked (`<target-id>`); the real id is used only inside the actual config scope write.

## 1. OpenClaw config

| Field | Value |
| --- | --- |
| Path | `C:\Users\Admin\.openclaw\openclaw.json` |
| SHA-256 | `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d` (verified by `Get-FileHash`) |
| `meta.lastTouchedAt` | `2026-07-14T15:47:55.282Z` |
| `meta.lastTouchedVersion` | `2026.7.1` |
| OpenClaw build | `2026.7.1 (2d2ddc4)` |

## 2. Gateway

| Field | Value |
| --- | --- |
| Mode / bind | `local` / `loopback` |
| URL | `ws://127.0.0.1:18789` (dashboard `http://127.0.0.1:18789/`) |
| Auth | `token` |
| Reachable | yes, port probe HTTP 200 |
| Process | running, pid 79912 (Scheduled Task) |
| Tailscale | off |

## 3. Model registry (verified)

| Model | Input | Capability |
| --- | --- | --- |
| `xiaomimimo/mimo-v2.5` | `text, image` | **multimodal** |
| `xiaomimimo/mimo-v2.5-pro` | `text` | **text_only** |
| `deepseek/deepseek-chat` | `text` | text_only |
| `deepseek/deepseek-reasoner` | `text` | text_only |
| `deepseek/deepseek-v4-pro` | `text` | text_only |

`agents.defaults.model` = `{primary: xiaomimimo/mimo-v2.5, fallbacks:[xiaomimimo/mimo-v2.5-pro]}`.
`agents.defaults.imageModel` = **NOT SET**.

## 4. video-factory durable agent (the router to change)

| Field | Current |
| --- | --- |
| `agentId` | `video-factory` |
| `workspace` | `E:\project\OpenClaw_VideoFactory` |
| `agentDir` | `C:\Users\Admin\.openclaw\agents\video-factory\agent` |
| `model.primary` | `xiaomimimo/mimo-v2.5` (**multimodal — must change to pro**) |
| `model.fallbacks` | `[xiaomimimo/mimo-v2.5-pro]` |
| `tools.exec.mode` | `full` (**must be removed/restricted**) |
| `tools.allow` / `tools.deny` / `tools.profile` | NOT SET (open surface, ~52 tools) |
| `subagents.allowAgents` | inherited (same-agent only) |
| sandbox | inherited off |

## 5. Target-group session override (must be cleared)

Verified from live `sessions.json` for session key `agent:video-factory:feishu:group:<target-id>`:

- `modelOverride`: `mimo-v2.5-pro`
- `modelOverrideSource`: `auto`
- `fallbackNoticeSelectedModel`: `xiaomimimo/mimo-v2.5`
- `fallbackNoticeActiveModel`: `xiaomimimo/mimo-v2.5-pro`
- `fallbackNoticeReason`: `timeout`

Interpretation: the durable model is multimodal `mimo-v2.5`; on timeout the session auto-overrode to text-only `pro`. This is exactly the durable/session inconsistency the 007 task must remove: make durable `pro` and clear the auto override so the entry is consistently text-only.

## 6. `tools.media` (must be added)

- `tools.media.image/audio/video` = **NOT SET**.
- `image/audio/video.scope` = **absent**.
- `enabled` for each capability = `auto` (auto-detect may therefore try a configured image-capable provider, e.g. `mimo-v2.5`, for the target group — this is the risk the scope deny removes).

## 7. Topology invariants

| Invariant | Value |
| --- | --- |
| Agents | 14 (main, taizi, zhongshu, menxia, shangshu, hubu, libu, bingbu, xingbu, gongbu, libu_hr, zaochao, douyin, video-factory) |
| Bindings | 14 (one route per agent account; last is video-factory → dedicated group via zhongshu) |
| Cron | 4 (openclaw-backup, 杭州每日天气, 每日早朝天气播报×taizi, 每日早朝天气播报×main[error 21x preexisting]) |
| Target-group consumers | 1 (zhongshu account → video-factory binding, peer group `<target-id>`) |
| `requireMention` (target group) | false |
| zhongshu groupPolicy | allowlist |

Next cron run ≈ 22–23 h away (morning); the "no cron within 15 min" production gate is satisfiable.

## 8. Plugins / skills

- `plugins.allow`: memory-core, clawd-on-desk, feishu, deepseek, codex-supervisor, codex, tavily.
- Enabled skills: find-skills, agent-browser, api-calls, content-summary, security-audit, self-evolution, clawhub.
- `mcp.servers` = **NOT SET** (no custom MCP servers configured currently).

## 9. Project manifest

| Field | Value |
| --- | --- |
| Root | `E:\project\OpenClaw_VideoFactory` |
| VERSION | 2.4.0 |
| git branch | `phase/p0-gate-correction` (no commits yet; untracked tree) |
| Manifest files | `FILE_MANIFEST.txt`, `SHA256SUMS.txt` present |
| `PROJECT_STATUS.yaml` | phase P0, `not_started` (must not modify per task) |

File hashes (SHA-256) of files this task may touch:

| File | SHA-256 |
| --- | --- |
| `scripts/07_ingest_inbound_media.ps1` | `10302de702e6c957133c1dbe19404d9ef5d273f289438ea92c049158b57d0afe` |
| `tests/Test-SingleGroupMediaRouter.ps1` | `df02e974c393607a5eba72483c11dcddb69ab805ad9a6d9943376abb4f9f2547` |
| `tests/Test-IngestInboundMedia.ps1` | `99f35e3f77dbd55b0e1e0f77998d41d3d4cc1d90cdbc8a46a6517a936fffa9c7` |
| `AGENTS.md` | `179330034a7e15659792b45097cc0e30613a91f4afe190afdc81b9e9ca5d2951` |

## 10. Prior test results (must continue to pass)

- Single-group router offline contract: **15/15** (Pester 3.4.0).
- Inbound media regression: **32/32** (Pester 3.4.0).

## 11. Local runtime (to be confirmed by Haiku E)

- Python 3.14.2 (WindowsApps); Node 24.18.0.
- `mcp` Python SDK not reliable (import resolves but no `__version__`) → `ingest_attachment` will be a **zero-dependency stdlib MCP server**.
- ffmpeg/ffprobe, NVIDIA/CUDA, faster-whisper: pending Haiku E inventory.

## Secrets policy

All apiKeys, appSecrets, the gateway token, the real target-group id, and any file_keys are masked or omitted from this baseline and every report. The real target id is held only in live config/session state and is used solely for the actual `tools.media.*.scope` keyPrefix write.
