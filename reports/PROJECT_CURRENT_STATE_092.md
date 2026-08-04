# Project Current State — 092

Date: 2026-08-04
Status: `AUDITED_DOCUMENTATION_ONLY`

## Authoritative phase state

`PROJECT_STATUS.yaml` remains authoritative: PACKAGE is passed, P0 is
`not_started`, and P1–P5 are blocked by phase order. No `P0_READY.json` exists.
Nothing in this report changes that state.

The working tree is intentionally not clean: it contains prior P0 planning and
evidence records plus this task's documentation Change Request. HEAD is
`72196d7` on `codex/p0-feishu-single-consumer-086`; `origin` points to the
project's GitHub repository. No commit, push, branch, or source edit is part of
092.

## A. Completed production capabilities (component-level, not full production)

“Completed” here means a capability has real, retained evidence. It does **not**
mean the full video factory is in production.

| Capability | Current evidence | Boundary |
| --- | --- | --- |
| Feishu Core entry topology | One `video-factory` agent and one exact group Binding; analyzer agents have no Binding | Existing topology evidence; no phase promotion |
| Single ingress safety | TXT/PNG/MP4 receipts are quarantined, unparsed, retained and SHA-256 verified | Safe ingress is not duplicate-event proof |
| Two-message Ticket protocol | Attachment ingress is separated from later reply-based analysis intent | User intent and media type must match before analysis |
| Image, audio and video analysis | Real qualification artifacts exist for image, CUDA audio transcription and MP4 analysis | Results are media-analysis capability, not video-production output |
| GPU safety | Media GPU lock and CUDA/CPU fallback rules exist; RTX 4070 SUPER has been used by media tasks | P3 production GPU queue is not yet qualified |
| Feishu egress | Markdown, PNG, TXT and MP4 visible delivery plus same-key idempotency have retained P0 evidence | This is controlled bot egress, not factory-driven P1 delivery |
| Router safety | `/status` fixed-path policy is verified and attachment ingestion is isolated from analysis | Does not prove every future workflow command |

## B. Completed but not real-production validated

| Candidate capability | Current evidence | What remains unproven |
| --- | --- | --- |
| SQLite state/event/artifact control plane | `src/factory/{db,state,cli}.py` and offline candidate tests | Real factory process recovery and live delivery |
| Script, TTS and captions | `edge-tts` candidate, WAV/SRT artifacts and caption checks | Production voice policy and human listening acceptance |
| Portrait rendering | Remotion 4 candidate has four template modes and FFmpeg/NVENC plus CPU artifacts | A fresh production job from approved input |
| Mascot | Eight deterministic SVG poses and visual review contact sheet | Human brand acceptance across real topics |
| Quality package | 5 offline candidate jobs, each with media/quality artifacts | Product-level acceptance and regression after integration |
| Delivery adapter | Dry-run idempotency and local self-attestation | One factory-driven Feishu delivery with idempotency and restart recovery |

The latest offline requalification is `P1_060_OFFLINE_REQUALIFICATION_PASS`:
382 Python passed (1 Windows symlink privilege skip), 127 Pester passed, 88
schema checks passed, and 10 portrait MP4s passed bounded decode. It explicitly
states `offline_only: true` and `p1_promotion: false`.

The five candidate jobs account for multiple encoded/video artifacts, which is
why the requalification decodes ten MP4 outputs. Neither count is a claim of
five or ten production deliveries.

## C. Current blockers

1. **P0 acceptance contract is not yet applied.** The existing final Gate still
   requires `FEISHU_SINGLE_CONSUMER_TEST.json` with an observed same-event
   retry/deduplication witness. P0-090 hit a one-shot ACK-failure seam but did
   not observe a retry; it was rolled back and is terminal `FAIL`.
2. **The old proof method is infeasible.** Feishu documents automatic retry,
   not an operator-controlled generic replay. Repeating fault injection cannot
   advance the product without a new evidence design.
3. **The formal P0 Gate has not been run successfully.** Therefore phase status
   cannot move and the formal P1 Gate cannot begin.
4. **P1 live boundaries are deliberately absent.** Real factory-driven delivery,
   restart recovery of factory state, cancel/retry, and human visual/listening
   review are not evidenced.

Gateway provenance/RPC authentication, Project Gateway replacement, Device
Auth, and manual retry reproduction are **not MVP blockers** under the proposed
roadmap. They remain deferred hardening unless they are required by a later
accepted contract.

## D. Deferred to P1/P2 and later

| Stage | Deferred work |
| --- | --- |
| P1 | Integrate the already-qualified candidate with actual factory-driven Feishu delivery, real state recovery, cancel/retry and human review |
| P2 | Source-backed topic research, quota/dedup scoring, 08:30 candidate cards, 12:00 fallback, Cron and seven-day reliability trial |
| P3 | Approved ComfyUI workflows/models, serialized GPU production queue, advanced subtitle alignment, short AI-video inserts and GPU fault testing |
| P4 | Reference-video originality workflow and optional Jianying/editable-draft assistance; no automatic Douyin publication |

## Repository audit summary

- The project contains a concrete Python factory package (`db`, `state`, `tts`,
  `captions`, `render`, `quality`, `delivery`) and a local Remotion project.
- The four template modes are `protocol-frame`, `code-explainer`,
  `flow-diagram`, and `engineering-case`; they are implemented in the unified
  Remotion composition rather than separate template folders.
- The candidate dependency footprint is intentionally small: Python bootstrap
  validation dependencies, `edge-tts`, and pinned Remotion/React tooling.
- Existing non-blocking warnings must remain visible: the Agent/Binding report
  records two official plugin-version drifts and makes no Cron-health claim.

## Decision from this audit

The product path is viable. The next work is a **controlled acceptance-contract
implementation**, followed by one P0 closure attempt and promotion of the
existing P1 candidate. It is not another Feishu retry experiment and not a
rewrite of the video pipeline.
