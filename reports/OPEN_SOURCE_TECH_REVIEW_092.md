# Open Source Technology Review — 092

Status: `RESEARCH_ONLY_NO_INSTALL_OR_IMPORT`

## Git and audit boundary

Read-only audit covered the current repository at `72196d7` on
`codex/p0-feishu-single-consumer-086`, its configured `origin`, the pinned
factory/Remotion dependencies and local source inventory. No separately vendored
or new independent open-source video project was found in the repository.
The review compared upstream project repositories only; it did not clone,
install, import or execute any candidate.

## Current fit

The repository already has Python factory state/control, local Remotion rendering,
FFmpeg/NVENC artifacts, `edge-tts`, faster-whisper media analysis and OpenClaw orchestration.
Adding another full video, agent or workflow product would duplicate state, scheduler and delivery ownership.

| Technology | Decision | Reason |
| --- | --- | --- |
| [Remotion](https://github.com/remotion-dev/remotion) | Retain | Already pinned at v4.0.500; deterministic technical 9:16 visuals |
| [Remotion TikTok template](https://github.com/remotion-dev/template-tiktok) | Study in P3 only | Caption-layout reference; no code copy before license/version/design review |
| [edge-tts](https://github.com/rany2/edge-tts) | Retain for MVP | Pinned candidate dependency; retain provider/fallback classification |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Retain | Existing CUDA/CPU transcription base fits current RTX media path |
| [WhisperX](https://github.com/m-bain/whisperX) | Evaluate only in P3 | Word alignment is useful but adds CUDA, alignment models and optional token-bound diarization |
| [ComfyUI](https://github.com/comfy-org/ComfyUI) | P3 only | Installed engine can run approved workflows; no node/model install before budget/license approval |
| [n8n](https://github.com/n8n-io/n8n) | Do not adopt | Fair-code external scheduler/orchestrator duplicates OpenClaw plus SQLite ownership |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Do not adopt for MVP | Creates a second stateful agent runtime without a proven P2 need |

## Implications

- Keep Remotion + FFmpeg as the deterministic rendering main line.
- Keep faster-whisper and current captions for P1. WhisperX is a later benchmark.
- Keep `edge-tts` for MVP; local voice cloning requires separate rights/model review.
- ComfyUI may add approved images or 2–4 second inserts only in P3.
- OpenClaw owns orchestration and factory SQLite owns job truth.

Any later adoption needs source/license/version/model/GPU/Windows compatibility/rollback review
and a measurable isolated benchmark. This task installed and downloaded nothing.
