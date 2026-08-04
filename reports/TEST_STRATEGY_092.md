# Test Strategy — 092

Status: `PROPOSED_NOT_APPLIED`

## Principle

Tests prove only their own layer. A unit pass is not a real Feishu pass; a valid
offline MP4 is not a P1 delivery; a quality improvement is not automatically phase-blocking.

| Layer | Purpose | Evidence | Phase blocking |
| --- | --- | --- | --- |
| Unit | Deterministic behavior | Versioned test result | Yes, for its implementation increment |
| Integration | Local components plus persistence | Structured local report | Yes, for P0/P1 contract rows |
| Real Feishu | Actual user/channel/egress behavior | Redacted correlation report | Yes, where a phase claims Channel capability |
| MVP acceptance | Usable product outcome | Fixture package, human review, formal Gate | Yes, for P1/P2 |
| Quality enhancement | Better experience | Benchmark or review note | No, unless accepted as later P3/P4 requirement |

## P0 blocking suite

1. Binding/process topology: one consumer and zero unintended consumers.
2. Fresh ordinary-user text ingress with one redacted route/reply correlation.
3. Event-ID idempotency and duplicate-effect protection integration tests.
4. TXT/PNG/MP4 receipt/hash/quarantine safety regression.
5. Existing real image/audio/video qualification plus analyzer regressions.
6. Managed restart recovery: pre/post topology and next fresh text event.
7. Project regression, `openclaw skills check`, prereview and one formal Gate.

`NOT_PROVEN_PLATFORM_RETRY` is recorded but non-blocking. Manual replay, ACK injection,
bot loopback and a second event listener are forbidden test methods.

## P1 blocking suite

- SQLite create/cancel/retry/restart transitions and artifact binding;
- script/source, TTS, WAV/SRT timing and caption safety;
- Remotion contracts/typecheck, FFmpeg decode, portrait media checks, NVENC/CPU fallback;
- manifest containment, quality integrity and secret scan;
- clean/rerun/cancel/retry/restart for three fixtures;
- one real factory-driven Feishu delivery and same-key idempotency; and
- human visual/contact-sheet plus listening review.

## P2 blocking suite

Source allowlist/date/count, quota/dedup, selection/cancel/recovery, dry-run 08:30/12:00,
scheduler duplicate/late recovery, then seven-day reliability metrics.

## Quality-only suite

Alternative mascot/visual style, advanced alignment, AI inserts, upscale, speed tuning and
reference-style experiments block only their optional enhancement increment.

## Reporting

Every result names phase, evidence class, provenance, version, redaction, status, artifact,
risk and rollback. Only a formal Gate writes `*_READY.json`.
