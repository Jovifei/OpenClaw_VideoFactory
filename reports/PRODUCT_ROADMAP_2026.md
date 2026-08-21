# OpenClaw VideoFactory Product Roadmap — 2026-08-14

Status: `USER_ALIGNED_PRODUCT_SEQUENCE`

This roadmap records Jovi's product decision. It is a planning document only:
it does not change runtime configuration, historical evidence, or any phase-pass result.

## Phase 1 — Local Codex Video Factory

| Item | Definition |
| --- | --- |
| Goal | Turn a Jovi-provided topic, a Jovi-provided local reference video, or explicitly authorized public-topic research into one reviewable original 25–60 second vertical MP4. |
| Inputs | Topic plus source context; local reference video; or a bounded approved public-research request. |
| Outputs | Topic/factual or reference report, original script, storyboard, assets, WAV, captions, master MP4, render manifest, quality report and local review checklist. |
| Technology | Local Codex workflow, `video_factory`, TTS, subtitles, deterministic SVG/HTML/Remotion/FFmpeg, optional approved local GPU, CPU fallback. |
| Acceptance | A topic fixture and a local-reference-video fixture each produce a decodable original MP4 with traceable inputs and human visual/listening review. |
| Excludes | Feishu, OpenClaw/Gateway, lark-cli, Cron, automatic topic choice, automatic upload/publication, cookies and restricted-platform scraping. |
| Risks | Factual errors, weak source rights, renderer drift, voice quality and weak originality boundaries. |

Reference input means theme/structure/general-expression analysis followed by new work. It never means reusing original audio, watermarks, continuous footage, full scripts or a platform account.

## Phase 2 — Feishu Topic Automation and Controlled Delivery

| Item | Definition |
| --- | --- |
| Goal | Safely operate one daily candidate-to-review-package cycle after local video creation is proven. |
| Inputs | Allowed sources, account history, quota rules, a Phase 1 renderer, user selection or a time-based qualified fallback. |
| Outputs | 10+ raw topics, 3–5 scored cards at 08:30, one selected job or a 12:00 qualified fallback, Feishu review delivery and run history. |
| Technology | Historical P0 Feishu safety work, OpenClaw commands/state, lark-cli controlled egress, source adapters, scoring/dedup, cancellation and idempotent scheduler. |
| Acceptance | Real Feishu safety/ingress/egress evidence, source/date/engineering-impact rules, 28-video quota, duplicate/cancel/retry tests, non-scheduled proof, then seven-day trial. |
| Excludes | Automatic Douyin publishing and uncontrolled third-party downloads/scraping. |
| Risks | Weak sources, stale trends, schedule duplication, credentials and unbounded provider/model costs. |

The former `P0` is retained as a Phase 2 technical prerequisite. It is no longer a reason to delay Phase 1 local video creation.

## Phase 3 — Advanced Video Production

Improve visual/audio quality and local GPU efficiency: serialized 4070S queue, approved ComfyUI workflows, optional 2–4 second inserts, word-level subtitle experiments and documented fallbacks. No model or node is downloaded without approval.

## Phase 4 — Advanced Reference-Video Original Re-creation

Phase 1 supports basic topic extraction from user-provided local reference video. Phase 4 adds richer transcript, cut, keyframe and style analysis under source-rights and originality checks. No raw audio, watermark or continuous source footage is reused.

## Phase 5 — Publishing Assistance

Provide a publish checklist, cover/caption bundle and optional editable Jianying draft. The MP4 remains primary, and Jovi remains the final Douyin publisher.

## Sequencing rule

`PHASE_1_LOCAL_VIDEO_FACTORY_READY → PHASE_2_FEISHU_AUTOMATION_READY → PRODUCTION` is the only route to scheduled operation. Phase 3–5 enhance a working base; they must not delay the first local, human-reviewable MP4.
