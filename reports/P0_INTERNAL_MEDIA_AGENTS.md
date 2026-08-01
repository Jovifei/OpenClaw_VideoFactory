# P0 Internal Media Agents (007)

Status: **3 binding-less agents applied; verified no binding; topology 14->17 agents, 14 bindings, 4 cron, 1 consumer**.

## Reuse check

All 14 existing agents have feishu route bindings. None is a binding-less internal agent. 3 new agents required (none reused).

## The 3 agents

| id | model | role | GPU lock | failure codes |
| --- | --- | --- | --- | --- |
| `video-factory-image-analyzer` | `mimo-v2.5` (multimodal, fallbacks []) | read stored image copy -> analysis.json | yes (VLM) | `multimodal_model_unavailable` |
| `video-factory-audio-analyzer` | `mimo-v2.5-pro` (text; structures whisper output) | faster-whisper CUDA transcription | yes (CUDA) | `local_audio_analyzer_unavailable`, `gpu_lock_unavailable` |
| `video-factory-video-analyzer` | `mimo-v2.5` (multimodal for keyframes) | ffprobe -> CPU frame extraction -> VLM | yes (VLM stage only) | `video_probe_failed`, `video_frame_extract_failed`, `gpu_lock_unavailable`, `multimodal_model_unavailable` |

Each: isolated `workspace` + `agentDir`; `subagents.allowAgents: []`; `tools: {exec:{mode:"deny"}, allow:["read","write"], deny:[exec,process,browser,image,image_generate,video_generate,music_generate,pdf,web,gateway,nodes,cron,feishu,sessions_spawn,sessions_send]}`; `contextInjection: "continuation-skip"`; `skills: []`; no identity; no heartbeat.

## Data flow (router -> analyzer)

Allowed payload: `receipt_path`, `stored_path`, `job_id`, `analysis_policy`. Forbidden: `MediaPath`, URL, base64, `file_key`, raw message_id, group_id, secrets.

Analyzer output: `jobs/<job_id>/analysis.json` + `analysis.txt`. Analyzer does NOT reply to the group; the router replies via `message`.

## Multimodal fallback rule

image/video vision: `mimo-v2.5` -> (no approved local VLM this round) -> `multimodal_model_unavailable`. NEVER falls back to `mimo-v2.5-pro` (text-only, cannot see images). The router stays text-only.

## Local runtime (from Haiku E)

- faster-whisper 1.2.1 + PyTorch 2.11+cu128 + `torch.cuda.is_available()=True` -> audio analyzer can use CUDA. Default model: `medium` (fp16, ~3.5GB).
- ffmpeg/ffprobe 8.1.1 at `C:\ffmpeg\bin\` (NOT on system PATH) -> analyzer wrapper uses absolute path.
- No local VLM immediately callable (Ollama CLI not installed; Qwen2.5-VL weights exist but not audited) -> image/video vision uses cloud `mimo-v2.5`; `multimodal_model_unavailable` if cloud down.
- ComfyUI not actually installed.

## GPU lock

`scripts/gpu_media_lock.py` (zero-dependency). Single concurrency for faster-whisper CUDA / VLM / ComfyUI. ffprobe and CPU frame extraction do NOT take the lock. Lock record: job_id, message_id, attachment_index, pid, heartbeat, timeout, stale_after. Stale recovery via ctypes OpenProcess (Windows).

## Topology invariants (verified)

- agents.list: 17 (<=17 limit)
- bindings: 14 (3 new agents NOT in bindings; `has_binding=False`)
- cron: 4
- target-group consumer: 1 (zhongshu -> video-factory route)
- other 13 agents: config hash unchanged

## Tests

`Test-SingleGroupMediaRouter.ps1` internal-analyzer block (11 tests): PNG->image-analyzer only, audio->audio-analyzer only, MP4->video-analyzer only, 4-field payload, no raw MediaPath, no pro fallback, GPU lock single concurrency, stale recovery, other agents unaffected, no binding, single consumer, reply to original group.
