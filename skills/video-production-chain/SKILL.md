---
name: video-production-chain
description: "Route one Chinese technical video job from verified text to an auditable Jianying draft without duplicating renderers, audio, or subtitle authority."
version: 0.1.0
metadata:
  openclaw:
    emoji: "🧭"
---

# Video production chain

This is the orchestration contract for a single video job. It composes the
workspace-owned Skills; it does not replace them with an all-in-one generator.

## Canonical route

```text
topic-intelligence / reference-video-analyzer
        ↓ verified factual_brief + originality gate
script-storyboard-director
        ↓ script.json + storyboard.json + style_tokens.json
media-asset-curator
        ↓ Registry-only asset_manifest
audio-subtitle-engine
        ↓ local narration + captions/timing
remotion-layout-engine + existing FFmpeg pipeline
        ↓ visual-only Jianying input (no audio, no burned subtitles)
jianying-draft-exporter → jianying-editor-skill
        ↓ one VoiceOver track + one native Subtitles track
video-quality-gate
        ↓ review package; manual Jianying listening/export gate
```

## Stage ownership and handoffs

| Stage | Owner | Required handoff | Hard stop |
|---|---|---|---|
| Topic/reference | `topic-intelligence`, `reference-video-analyzer` | verified facts, source/rights receipt, abstract style only | reference audio, frames, full transcript, or unverified facts |
| Text/structure | `script-storyboard-director` | five beats, 25–60s target, narration, on-screen text, visual intent | generic filler, unsupported claims, topic/asset mismatch |
| Assets | `media-asset-curator` | Registry asset IDs, hashes, license basis, fallback | source paths, watermarks, unlicensed or cross-topic assets |
| Audio/captions | `audio-subtitle-engine` | local WAV/SAMI or SRT timing, pronunciation decisions | silent audio, clipped audio, duplicated caption authority |
| Visual | `remotion-layout-engine` and existing local renderer | 16:9 by default, neutral theme palette, H.264 visual-only input | C-drive output, portrait by accident, baked captions for Jianying |
| Editing | `jianying-draft-exporter` using pinned `jianying-editor-skill` | new E-drive draft, track map, manual-open instructions | automatic UI export, muting VoiceOver, second editor backend |
| Quality | `video-quality-gate` | ffprobe/decode/hash/report/review package | claim of publish-ready without human listening and visual review |

## Default media policy

- Default canvas is 1920×1080, 30 FPS. Use 1080×1920 only when the brief
  explicitly sets `aspect_ratio: "9:16"`.
- Palette is selected from the topic's style tokens; Pink Pig pink is not a
  global background. Pink Pig is off unless Jovi explicitly opts in and the
  original-asset receipt is verified.
- The deterministic local MP4 may contain an audio/subtitle variant for
  technical quality evidence. The Jianying input is a separate visual-only
  render with no audio and no burned-in subtitles.
- Jianying is the only editing backend for a given job. Generate a new draft,
  keep automatic export disabled, and require Jovi to listen and export.
- All runtime, draft, report, and review outputs use the configured E-drive
  roots. C-drive paths fail closed.

## External repository policy

- `luoluoluo22/jianying-editor-skill` is the selected, pinned MIT backend.
- `Hommy-master/capcut-mate` (Apache-2.0) is an isolated future adapter; do
  not enable it in a job that uses Jianying.
- `hey-jian-wei/jianying-mcp` is a research candidate only. Its project
  generation path is not part of the production chain until a separate
  license, version, permission, and recovery review is approved.
- `video-podcast-maker` methods may inform script/timing contracts, but it
  does not own job state or rendering.

## Completion meaning

`draft_ready_for_manual_jianying_review` means the chain produced a
reviewable draft. It does not mean the audio was heard by Jovi, the draft was
exported, or the video was published.
