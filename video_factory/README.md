# Pink Pig Local Video Factory MVP

## Phase 1.5 knowledge composition

Knowledge videos opt into `knowledge_illustration` with `mascot.mode: required`.
The existing job path then loads `schemas/video/composition.schema.json`, keeps
the illustration inside `content_area` (`y=240..1040`), burns subtitles only in
`subtitle_area` (`y=1120..1580`), and places the small Pink Pig signature in
`signature_area` (`y=1760..1860`). `SubtitleLayoutEngine` rejects overlapping
regions before FFmpeg. Composition style values are authoritative over legacy
job subtitle overrides, so the old oversized 44px style cannot reappear in a
knowledge render.

The registry contains five local Modbus RTU knowledge illustrations plus the
transparent `pink_pig.signature.v1`. The upstream
[`ian-fenzhu-illustrations`](https://github.com/Jovifei/ian-fenzhu-illustrations)
repository is used for style DNA, persona and composition rules, not as the
image library. See `examples/pink_pig_modbus_demo/` for the four-scene example.

This module is a local FFmpeg pipeline: image directory → manifest → timeline
→ SRT subtitles → playable portrait MP4. It has no OpenClaw, Feishu, network,
agent-orchestration or model dependency.

## Two Modes

### Legacy Mode (unchanged)

```powershell
python generate_video.py --config examples/pink_pig_demo/config.yaml
```

The demo writes `dist/pink_pig_demo.mp4`, `dist/asset_manifest.json`,
`dist/video_timeline.json` and `dist/subtitle.srt`.

### Phase 1 Job Mode (new)

```powershell
python generate_video.py --job examples/pink_pig_story_demo/job.yaml
```

Uses a **storyboard-driven** pipeline:
1. Load `PinkPigRegistry` (IP asset single source of truth)
2. Validate & compile `Storyboard` → `Timeline` (deterministic pure function)
3. Plan audio (TTS → BGM → silent fallback chain)
4. Render with `ffmpeg`

Outputs to `dist/pink_pig_story_demo.mp4` plus intermediate artifacts in
`dist/story_demo/`.

### AI Director Topic Mode (003)

```powershell
python generate_video.py --topic "介绍 Modbus RTU" --director-provider codex-cli
```

The read-only Direct Codex CLI provider produces a constrained DirectorDraft;
Python injects the registry/IP/render fields, validates the Storyboard, and
then calls the same `run_job()` path. Artifacts are written under
`dist/director/<stable_job_id>/`, including `storyboard.json`,
`director_report.json`, `render_report.json`, and `output.mp4`. This mode is
for manually approved evergreen engineering topics and requires human factual
review; it is not Feishu or automated topic operation.

## Key Components

| Component | Path | Role |
|---|---|---|
| Asset Registry | `src/factory/assets/pink_pig/` | IP asset catalog + resolver |
| Video Schemas | `schemas/video/` | Storyboard / Timeline / VideoRenderJob JSON Schema |
| Storyboard Compiler | `video_factory/pipeline/storyboard.py` | Director semantics → render instructions |
| Audio Planner | `video_factory/pipeline/audio_planner.py` | TTS + offline fallback |
| Validation | `video_factory/pipeline/validation.py` | jsonschema thin wrapper |
| Render report | `video_factory/pipeline/render_report.py` | Stable ffprobe/SRT/timeline quality evidence |
| Director contract | `src/factory/director/` | Provider-neutral topic-to-storyboard contract, constrained Draft, and read-only Codex CLI adapter |

## Supported Input

Legacy mode: PNG, JPG, JPEG, WebP still images in a directory.
Job mode: storyboard-defined scenes referencing registry assets by pose/mood/id.

Transitions: `fade`, `zoom`, `slide`. Audio is optional; when present it is
encoded as AAC. `pipeline/voice_generator.py` is a deliberately optional
edge-tts adapter, not a demo requirement.

Video job lifecycle snapshots use `schemas/video/video_job_state.schema.json`.
The lifecycle schema is a contract only; it does not add a state store or
implement lifecycle transitions. Successful job renders also write
`render_report.json` next to the existing `run_report.json`.

## Pink Pig and subtitle safety controls

Knowledge videos load the local `pink-pig-mascot-director` skill and the
externalized style profile through the `mascot` contract.  Set
`mascot.mode` to `required` (fail closed if the IP contract is unavailable),
`optional` (continue with a recorded fallback), or `off` for a non-mascot
video.  The upstream illustration repository supplies style DNA and
composition guidance; repository-local images remain the actual render
assets.  See [the upstream illustration skill](https://github.com/Jovifei/ian-fenzhu-illustrations).

Knowledge subtitles use `subtitle.style.layout: bottom_safe_band`.  The
configured font and margins are final-video pixel values; the renderer maps
them to FFmpeg/libass coordinates, wraps captions to at most two lines, and
clips cross-fade overlaps so captions never cover the central illustration.
For narration, use `audio_mode: tts_with_offline_fallback`; a failed TTS
provider records the fallback and uses the configured BGM instead of silently
producing a near-zero-volume track.
