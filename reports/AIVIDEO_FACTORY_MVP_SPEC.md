# AI Video Factory MVP Specification

Status: `TARGET_SPEC_NOT_A_GATE`

## Product promise

For one manually approved engineering or AI topic, create one Chinese vertical
short-video review package locally and deliver it once to the approved Feishu target.
Jovi reviews it and publishes to Douyin manually.

## Inputs

Required: topic, factual brief with source/date for claims, chosen visual template,
and a factory idempotency key. Optional: safe-ingested media, style brief and mascot mode.
Attachments remain untrusted data and use only the P0 receipt plus reply/Ticket protocol.

## Outputs

One 1080x1920, 30 FPS short-video format with a 60-second maximum.
The initial fixture target is 40 seconds, matching `config/topic_rules.yaml`;
an MVP output must never exceed 60 seconds.

```text
script.json            factual script and sources
storyboard.json        scenes and template
voice.wav              narration
captions.srt           monotonic captions
final_master.mp4       local master
feishu_preview.mp4     review preview
cover.png              cover
quality_report.json    automated checks
publish_info.md        manual review notes
delivery_manifest.json idempotent delivery record
```

The terminal state is `PENDING_REVIEW`, never `PUBLISHED`.

## Mandatory MVP

| Area | Requirement |
| --- | --- |
| State | SQLite state; idempotent create, cancel, retry and restart recovery |
| Story | Source-traceable script and scene boundaries |
| Voice/subtitles | Stable Chinese TTS, manifest, WAV/SRT failure classification and safe timing |
| Visuals | Protocol frame, code explainer, flow diagram or engineering case |
| Mascot | Deterministic Pink Pig action; signature/absence fallback on conflict |
| Render | Remotion/FFmpeg; NVENC preferred, CPU fallback verified |
| Quality | Decode, dimensions, FPS, duration, audio, captions, containment and visual review |
| Delivery | One real factory-driven Feishu delivery with stable idempotency key |
| Human control | Visual/listening review before manual publishing |

## Acceptance fixtures

Modbus/protocol-frame, Flash/watchdog and FreeRTOS/flow-diagram each prove clean run,
same-key rerun, cancel, classified retry, restart recovery and one idempotent delivery.
The offline candidate is a starting point, not the acceptance result.

## Deferred

Daily scheduling/selection, new ComfyUI models/nodes, long AI video, reference recreation,
Jianying draft and automatic Douyin publishing are out of MVP.

## Done definition

P0 is formally ready; all three fixtures have review packages; automated and human
acceptance pass; P1 Gate writes `P1_READY.json`.
