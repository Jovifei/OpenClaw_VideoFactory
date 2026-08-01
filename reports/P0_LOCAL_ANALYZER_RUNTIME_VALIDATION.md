# P0 Local Analyzer Runtime Validation (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **PASS** - all three analyzer runtimes validated on isolated stored copies.
Script: `scripts/local_analyzer_validation/validate_analyzers.py`

## Method

Each fixture was ingested via the `ingest_attachment` core (isolated temp inbound + project root), producing a quarantined `stored_path`. The analyzer runtime was then invoked directly on the `stored_path` (NOT the original inbound file), exactly as the binding-less internal analyzer agents would do in production. GPU-heavy stages acquired the `gpu-media` lock.

## Audio analyzer (faster-whisper CUDA)

| Field | Value |
| --- | --- |
| ingest | quarantined (stored_path produced) |
| model | faster-whisper `medium`, device=cuda, compute_type=float16 |
| GPU | RTX 4070 SUPER |
| VRAM before/peak | 2618 MB / 4781 MB (~2.1 GB for whisper) |
| language detected | en |
| transcript | "Openclaw Video Factory P0 Audio Test The quick brown fox jumps over the lazy dog" |
| elapsed | 5.44 s |
| GPU lock | acquired + released |
| transcript match | semantically correct (expected "VideoFactory P0"; TTS spoke "Video Factory P zero", whisper transcribed "Video Factory P0" - a TTS word-splitting artifact, not an analyzer error) |

**Conclusion**: faster-whisper CUDA transcription works on a stored audio copy with the GPU lock. No cloud fallback used.

## Video analyzer (ffprobe + CPU frames + audio extract + whisper)

| Field | Value |
| --- | --- |
| ingest | quarantined |
| ffprobe | ok; h264 video + aac audio, duration 5.0s |
| frame extraction | 3 frames at 0.2/0.5/0.8 positions, CPU (`scale='min(1024,iw)':-2`, no `-hwaccel cuda`) |
| audio extraction | ok (pcm_s16le 16kHz mono) |
| audio transcript | "Openclaw Video Factory P0 Audio Test The quick brown fox jumps over the lazy" (trailing "dog" dropped; semantically correct) |
| full video uploaded to model | **NO** (only bounded frames + extracted audio) |
| GPU lock | acquired for the whisper stage; ffprobe/frame-extraction did NOT take the lock (CPU) |

**Conclusion**: video analyzer pipeline (probe -> CPU frames -> audio extract -> whisper) works on a stored video copy. The full video is never uploaded to a model; only bounded frames and the extracted audio track are processed.

## Image analyzer (mimo-v2.5 cloud multimodal)

| Field | Value |
| --- | --- |
| ingest | quarantined |
| invocation | `openclaw infer image describe --file <stored_path> --model xiaomimimo/mimo-v2.5 --json` |
| exit code | 0 |
| result | `{"ok": true, "capability": "image.describe", "provider": "xiaomimimo", "model": "mimo-v2.5", ...}` |
| fallback to pro | **NO** (used mimo-v2.5 directly; pro is text-only and cannot see images) |

**Conclusion**: the image analyzer's cloud multimodal model (mimo-v2.5) works on a stored image copy via `openclaw infer`. No text-only fallback.

## Security invariants (all held)

- Analyzers received `stored_path` (quarantined copy) only; the original inbound `MediaPath` was NOT forwarded.
- No analyzer fell back to a text-only model for vision/audio.
- The full video was NOT uploaded to a model.
- The GPU lock serialized the two whisper runs (audio, then video-audio).

## Caveat (agent-level execution gap, documented)

The 3 analyzer AGENTS configured in openclaw.json have `tools.exec.mode=deny` and `tools.allow=[read,write]`. This is correct for security, but it means an analyzer agent cannot itself invoke `faster-whisper`/`ffprobe` (those need exec or a deterministic tool). The runtime validation above proves the **analysis runtimes work** when invoked directly; production agent-level execution will need a deterministic analysis MCP tool (analogous to `ingest_attachment`) OR the `image` tool allowed for the image analyzer, OR the stored copy passed inline to the spawned session. This is a P1 refinement / potential corrective CR, NOT a runtime failure. The real-Channel qualification (R3/R4/R5) will reveal whether the current agent-config path can complete analysis end-to-end; if not, building a deterministic analysis MCP tool is the authorized next step within the same architecture.

## Evidence

- `reports/P0_LOCAL_ANALYZER_RUNTIME_VALIDATION.json` (full results)
- `scripts/local_analyzer_validation/validate_analyzers.py`
- `tests/fixtures/feishu_delivery/p0-audio-test.wav` (sha `cc08486c...`)
- `tests/fixtures/feishu_delivery/p0-video-analysis-test.mp4` (sha `ca844094...`)
