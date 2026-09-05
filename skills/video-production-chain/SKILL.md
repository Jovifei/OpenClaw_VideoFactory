---
name: video-production-chain
description: "Route one technical video job from verified input to an auditable local MP4, with optional Jianying editable delivery, without duplicating renderers or state ownership."
version: 0.2.0
metadata:
  openclaw:
    emoji: "🧭"
---

# Video production chain

This is the orchestration contract for a single video job. It composes workspace-owned Skills and the existing pipeline; it does not create a second renderer or a second state database.

Before using this Skill, read:

- `PROJECT_STATUS.yaml`
- `docs/CURRENT_ARCHITECTURE.md`
- `docs/PRODUCT_PHASES.md`

## Phase 1 canonical route

```text
topic-intelligence / reference-video-analyzer
        ↓ verified factual brief / rights / originality boundary
script-storyboard-director
        ↓ script.json + storyboard.json + style/render profile
media-asset-curator
        ↓ approved asset manifest
        ├─ deterministic technical SVG/HTML/Remotion
        └─ approved creative assets when allowed
audio-subtitle-engine
        ↓ local narration + subtitle/timing/speech cues
remotion-layout-engine + existing FFmpeg pipeline
        ↓
video-quality-gate
        ↓
final local MP4 + quality report + review package
        ↓
Jovi human review
        └─ optional: jianying-draft-exporter → manual editable delivery
```

**Phase 1 success is not defined as “Jianying exported”.** The mandatory result is the local auditable MP4 and evidence package. Jianying is an optional editing/review branch.

## Reference route

```text
reference-video-analyzer
        ↓ safe receipt + abstract report
reference-video-recreator / original brief
        ↓ new script/storyboard
media-asset-curator
        ↓ new deterministic/approved visuals
audio-subtitle-engine
        ↓ new narration + measured timing
remotion-layout-engine
        ↓ new visual
existing FFmpeg pipeline
        ↓ new MP4
difference report + video-quality-gate
        ↓ Jovi originality review
```

Never pass source frames/audio directly into the final renderer as production assets.

## Stage ownership

| Stage | Owner | Required handoff | Hard stop |
|---|---|---|---|
| Topic/reference | `topic-intelligence`, `reference-video-analyzer` | verified facts; for reference: rights, digest, abstract structure | raw source reuse, unverified facts, unsafe input |
| Text/structure | `script-storyboard-director` | script, scene intent, narration, on-screen text | generic filler, unsupported claims, renderer paths in model output |
| Assets | `media-asset-curator` | approved Registry/technical asset IDs and provenance | unlicensed, cross-topic or source-video assets |
| Audio/timing | `audio-subtitle-engine` | new narration, timing/speech cues, subtitle contract | silence, clipping, duplicate subtitle authority |
| Visual | `remotion-layout-engine` + existing renderer | profile-specific deterministic visual | incorrect aspect ratio, C-drive private output, source-shot reuse |
| Media | existing FFmpeg pipeline | H.264/AAC local MP4 + decode/probe evidence | broken decode, mismatched report, hidden fallback |
| Quality | `video-quality-gate` | quality report + review package | claim of Phase-ready without human review |
| Optional editing | `jianying-draft-exporter` using pinned `jianying-editor-skill` | visual-only input, VoiceOver, native Subtitles | automatic export, second editor backend |

## Aspect ratio policy

Aspect ratio is job-scoped:

- vertical/Douyin knowledge profile: 1080×1920 (9:16);
- landscape/reference-edit profile: 1920×1080 (16:9) when the brief requests it.

Never infer Phase 1 quality from one global resolution constant.

## Pink Pig policy

Personal IP is off by default. When Jovi explicitly opts in:

- require the Jovi-owned original asset pack and receipt;
- do not substitute repository-created mascot PNG/SVG, AI temporary art or upstream samples;
- do not cover technical content or subtitles;
- mascot failure must not block a normal mascot-off technical video.

Read `docs/PINK_PIG_CURRENT_POLICY.md` and `config/mascot_usage.yaml`.

## Jianying policy

The currently reviewed optional editor backend is `luoluoluo22/jianying-editor-skill` at a pinned revision.

For an optional draft:

- use a separate visual-only render;
- no audio and no burned-in subtitles in the visual input;
- exactly one VoiceOver authority and one native Subtitles authority;
- E-drive runtime;
- automatic UI export/publication disabled;
- Jovi manually listens, reviews and exports.

A Jianying failure does not invalidate an already-qualified core MP4.

## External repository policy

- `HITsz-TMG/VideoClaw`: architecture/method inspiration only; do not import its second backend/state DB.
- `Agents365-ai/video-podcast-maker`: method inspiration; current CC BY-NC 4.0 means no unreviewed code/template copying into a future commercial path.
- `Jovifei/ian-fenzhu-illustrations`: style/persona source, not proof of final original mascot assets.
- `Hommy-master/capcut-mate`: isolated future adapter; not enabled with Jianying in one Job.
- `hey-jian-wei/jianying-mcp`: research candidate only.

## Completion meaning

### `local_review_package_ready`

The system produced a qualified local MP4 and machine evidence. It still needs Jovi human review.

### `draft_ready_for_manual_jianying_review`

An optional editable draft exists. It does not mean Jovi listened, exported or published it.

### `PHASE1_LOCAL_VIDEO_FACTORY_READY`

Only the formal Phase 1 Gate can assign this meaning after all fixed fixtures, lifecycle evidence, reference review, acceptance manifest and independent audit pass.
