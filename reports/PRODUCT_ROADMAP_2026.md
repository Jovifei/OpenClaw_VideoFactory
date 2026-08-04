# OpenClaw VideoFactory Product Roadmap — 2026

Status: `PROPOSED_PRODUCT_SEQUENCE`
This roadmap replaces no code or formal gate. It defines the order for future
authorized work.

## P0 — Stable AI media entry

| Item | Definition |
| --- | --- |
| Goal | A secure, observable Feishu media entry with explicit analysis intent and no duplicate application effects |
| Inputs | Ordinary-user text, TXT/PNG/audio/MP4 attachments, explicit reply/Ticket analysis request |
| Outputs | Quarantined receipts, classified image/audio/video analysis, redacted ingress/egress/topology evidence |
| Technology | OpenClaw Feishu Channel, `larksuite/cli` egress, receipt isolation, analyzers, GPU lock, event-ID/delivery idempotency contract |
| Acceptance | All rows of the proposed P0 matrix, zero-exit P0 Gate and `P0_READY.json` |
| Risks | Platform retry is not externally controllable; raw identifiers/attachments are sensitive; second consumers cause duplicate effects |

P0 explicitly excludes Project Gateway replacement, Device Auth experiments,
RPC provenance hardening, daily Cron and automatic publishing.

## P1 — AI video factory MVP

| Item | Definition |
| --- | --- |
| Goal | From one manually approved topic to one reviewable 25–60 second vertical MP4 delivered once through Feishu |
| Inputs | Topic plus minimum source context, selected template, optional approved media, stable job key |
| Outputs | Script, storyboard, WAV, SRT, master MP4, Feishu preview, cover, quality report and delivery record |
| Technology | SQLite state/events, Edge TTS with fallback policy, Remotion/FFmpeg, NVENC with CPU fallback, mascot SVG, factory delivery adapter |
| Acceptance | Three fixed fixtures; clean run/rerun/cancel/retry/restart recovery; human visual/listening review; real idempotent factory delivery; P1 Gate |
| Risks | Candidate artifacts are offline only; renderer/browser drift, voice quality and delivery integration can fail |

P1 reuses the existing candidate rather than rebuilding it. No automated topic
selection, production Cron, new model download, reference-video recreation or
Jianying dependency is required.

## P2 — Automated operation

| Item | Definition |
| --- | --- |
| Goal | Safely operate one daily candidate-to-review package cycle while preserving user control |
| Inputs | Allowed sources, account history, quota rules, user selection or time-based fallback |
| Outputs | At least 10 raw topics, 3–5 scored cards at 08:30, one selected job or a 12:00 qualified fallback, run history |
| Technology | Source adapters, citations, scoring/dedup store, OpenClaw commands, idempotent scheduler and cancellation state machine |
| Acceptance | Source/date/engineering-impact rules, 28-video quota, duplicate/cancel/retry tests, one scheduled dry-run, seven-day trial >=90% completion and zero duplicate jobs |
| Risks | Weak source quality, stale trends, schedule duplication and unbounded provider/model costs |

Cron registration begins only after the P2 paths pass their non-scheduled tests.

## P3 — Advanced video production

| Item | Definition |
| --- | --- |
| Goal | Improve visual/audio quality and local GPU efficiency without making stable delivery fragile |
| Inputs | Approved workflow manifest, model budget, benchmark corpus and explicit asset rights |
| Outputs | Versioned ComfyUI workflows, GPU queue telemetry, optional 2–4 second AI inserts, advanced subtitle alignment and fallback reports |
| Technology | RTX 4070 SUPER queue, faster-whisper improvements, ComfyUI API, optional WhisperX evaluation, NVENC telemetry, static/SVG fallback |
| Acceptance | Model/workflow hashes, serialized heavy jobs, OOM/timeout fallback, no unapproved download, measured quality/latency improvement |
| Risks | VRAM exhaustion, model licenses, unstable custom nodes and nondeterministic visuals |

## P4 — Publishing assistance

| Item | Definition |
| --- | --- |
| Goal | Make human review and manual Douyin publishing easier without automating the final publish action |
| Inputs | P1/P2 delivery package and optional approved reference material |
| Outputs | Publish checklist, cover/caption bundle, optional editable Jianying draft, originality/copyright report |
| Technology | Artifact manifest, optional Jianying exporter, reference-video analysis/recreation controls |
| Acceptance | Draft opens locally when enabled; source/rights checks pass; failure never changes MP4 delivery status; Jovi remains final publisher |
| Risks | Copyright leakage, watermarks, fragile editor integrations and accidental publication |

## Sequencing rule

`P0_READY → P1_READY → P2_READY` is the only path to daily operation. P3 and
P4 enhance a working base; neither may become an excuse to delay the first
deterministic MP4.
