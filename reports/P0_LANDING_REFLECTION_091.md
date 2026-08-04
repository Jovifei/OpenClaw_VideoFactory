# P0 Landing Reflection — 091

Date: 2026-08-04
Status: `PLAN_READY_NO_RUNTIME_ACTION`

## Product goal

Deliver a Windows-native, OpenClaw-orchestrated short-video factory for the
embedded-engineering main line and AI-hot-topic side line. It must receive and
deliver through Feishu, produce a reviewable portrait MP4 with TTS, subtitles,
programmatic visuals and the Pink Pig mascot, remain idempotent/recoverable,
and leave Douyin publication to Jovi. P2—not P0 or P1—adds the 08:30 candidate
message, 12:00 fallback production and seven-day automation trial.

## Truthful current state

| Layer | Status | Evidence |
| --- | --- | --- |
| Official phase | `P0 not passed`; P1 is formally blocked | `PROJECT_STATUS.yaml`; no `reports/gates/P0_READY.json` |
| Feishu/media capability | Real TXT, image, audio and MP4 ingress/analysis paths and controlled egress have been qualified in prior P0 evidence | P0 media and Feishu reports |
| P0 remaining issue | `BLOCKED`: the existing single-consumer gate demands an observable same-event redelivery, but Feishu offers automatic retry rather than a supported manual replay; P0-090's one allowed fault injection reached the seam but observed no retry | `reports/P0_FEISHU_AUTO_RETRY_090.json` |
| Offline video candidate | `PASS_OFFLINE_ONLY`, not a phase promotion | `reports/P1_060H_FULL_REQUALIFICATION.json` |
| Candidate contents | SQLite state/events, TTS + captions, four 1080x1920 templates, mascot assets, five candidate jobs, NVENC/CPU artifacts, quality reports and dry-run delivery adapter | `reports/P1_060_FINAL_INDEPENDENT_REVIEW.json` |
| Automation/production | Not started | P2–P5 and production Gate remain blocked by phase order |

## What went wrong in execution

1. The P0 safety objective (one active Feishu consumer and no duplicate
   processing) was conflated with one unrepeatable proof method (forcing a
   platform retry). When the platform did not expose that behaviour, repeated
   testing was no longer advancing the product.
2. Offline P1 candidate work and official P0/P1 phase status were not presented
   as two separate tracks. This made the project appear less complete than it
   is, while also obscuring which steps are actually required for release.
3. The work queue was driven by the newest failed subtest instead of a
   dependency map from product outcome to formal gates. A failed auxiliary
   experiment should have triggered a gate-design decision, not another live
   experiment.

## Corrected execution rules

- A live P0 experiment may run once per approved evidence design. If it cannot
  produce the required observable, stop and decide whether the acceptance
  contract—not the runtime—must change.
- Every status report must separate `implemented candidate`, `real integration
  evidence`, `formal gate`, and `production automation`.
- No P0 gate is retried until its inputs are achievable and each required input
  has fresh, attributable evidence.
- No P1/P2 runtime promotion is inferred from offline artifacts.

## Shortest path to a usable MVP

### Step 1 — P0 acceptance rebaseline (next decision)

Replace the infeasible requirement for a manually reproducible platform retry
with a supported, safety-equivalent evidence contract: one configured
`video-factory` consumer, zero secondary consumer processes/bindings, an active
plugin deduplication contract, one real normal-user ingress correlation, and
one real idempotent egress correlation. The report must explicitly state that
platform retry delivery itself is not proven. This is a gate/acceptance change,
so it requires a separate authorization and fresh Change Request; it must not
be silently weakened.

### Step 2 — Close P0 once, not repeatedly

After the amended contract is approved: refresh the fixed evidence set, run
full project regression, `openclaw skills check`, P0 prereview, then the P0
Gate exactly once. Only a zero exit and `reports/gates/P0_READY.json` may update
`PROJECT_STATUS.yaml` and unlock P1.

### Step 3 — Promote the existing P1 candidate to a real MVP

Do not rebuild the offline candidate. Revalidate it on the accepted P0 baseline
with three fixed fixtures, then perform the missing live boundaries: real
factory-driven Feishu delivery with a stable idempotency key, restart recovery,
cancel/retry, and a human visual/listening review. Run the formal P1 Gate and
create `P1_READY.json` only if all evidence is green.

### Step 4 — Add daily operation in P2

Implement source-backed topic research, quota/dedup scoring, 08:30 3–5-card
delivery, selection parsing, and the 12:00 fallback. Register Cron only after
these paths pass dry-run and live idempotency checks; then perform the seven-day
trial.

### Later, deliberately separate

P3 adds GPU queue/ComfyUI production work; P4 adds reference-video originality
workflow; P5 is optional Jianying draft export. None is needed to prove the
first deterministic MP4 MVP.

## Immediate next action

Obtain a single explicit authorization for **P0 acceptance rebaseline only**.
It should name the gate/prereview/report files permitted to change and prohibit
Gateway, OAuth, Binding, Runtime, Cron and media-routing changes. Until that
decision, no further retry injection or live Feishu test is useful.
