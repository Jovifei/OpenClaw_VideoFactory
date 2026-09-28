# Phase 1 Audio and Closure Handoff — 2026-09-28

## Ownership and current baseline

- Remote GPT is the long-stage plan owner and independent reviewer.
- Local Codex owns local edits, commands, tests, runtime evidence, commits and pushes.
- Local workspace: `E:\project\OpenClaw_VideoFactory`.
- Continuation branch: `codex/phase1-audio-closure-20260928`.
- Reviewed source baseline: `4136265b45dc4895f5b62e432933bc4c1121b155`.
- Previous source branch: `codex/phase1-audio-contract-20260927`.
- Current continuation commits must not modify Owner `main` or historical evidence branches.

Implemented continuation commits:

- `6e4ce51` — canonical closure docs, handoff, objective PCM contract and no-render integration test;
- `cf02b37` — scene identity/transition fail-closed checks and review-package artifact/hash binding;
- `5e74b6a` — v7 objective/secondary evidence and bounded test summary.
- `54cb42e` — close explicit transition, persisted-segment and script-hash fail-closed gaps found by independent review.
- `5eace26` — update handoff with the pushed lineage.
- `ff02100` — refresh closure status and bounded test counts.
- `8bcab34` — seal the evidence lineage metadata.
- `825c924` — record the final lineage seal hash.
- `7d08cdc` — add the parallel Phase 1 closure audit and provisional inventory.
- `f603da5` — repair the closure audit script newline handling.
- `8456862` — add the no-render CAN live-topic preflight.
- `c1776f6` — repair the CAN preflight script newline handling.
- `3671da5` — harden CAN asset decode, dimensions and safe-area evidence.
- `9cae148` — bind CAN assets to deterministic generator provenance.
- `ef84f28` — repair the CAN asset generator newline handling.
- `80aa85b` — complete the five-scene CAN visual preflight still set.
- `420dd83` — sanitize parallel closure lifecycle paths.
- `9f95d3f` — compute CAN visual/transition evidence and remove the remaining I2C private path.
- `386b3c0` — record the remote WP-H2 one-candidate authorization and local task boundary.
- `7045ca6` — record the bounded CAN outer-candidate change request.
- `feb95e1` — record the single CAN candidate machine review and adjacent-frame audit.
- `59bc37d` — update the candidate handoff and task ledger for remote review.
- `b4d28d5` — record the remote iteration-27 acceptance change request.
- `79eb0db` — record remote machine acceptance, provisional inventory refresh and I2C discovery.
- `a8caedd` — record the WP-J human-gate readiness change request.
- `8a80f53` — prepare human-gate binding, prereview dry-contract and next-candidate readiness evidence.
- `2e12423` — document the readiness package in the current handoff.

GitHub branch: `https://github.com/Jovifei/OpenClaw_VideoFactory/tree/codex/phase1-audio-closure-20260928`.

## Active scope

`topic_only_v1` requires Flash/watchdog, FreeRTOS, I2C and one distinct live topic,
each with hash-bound machine evidence, human review and Prereview. Reference
reconstruction is optional in this scope. Phase 2, Feishu, Cron and automatic
publication remain prohibited.

## Historical candidate boundary

The previous Flash and FreeRTOS outer candidates are permanently excluded because
the old `_align_audio()` path truncated TTS segments:

- Flash historical job: `job-3643de66b508bacc03474cbd`;
- FreeRTOS historical job: `job-2da2a3ae112bac2ceaacb5d7`.

Their reports remain immutable `CHANGES_REQUIRED_AUDIO_TRUNCATION` evidence. A good
visual frame review cannot promote either candidate.

## Current v7 audio artifacts

These are complete audio-only artifacts. Do not regenerate or substitute v4/v5 files.

| Topic | Duration | SHA-256 | Human gate |
|---|---:|---|---|
| Flash/watchdog | 48.466 s | `d32e7332763c503ca4568bb55a4d3c61cb47d1b157a4d0a41f79209810a373df` | `PENDING_HUMAN_AUDIO_REVIEW` |
| FreeRTOS mutex | 46.067 s | `313cad7ac3c4fa55678b819a57dc29d7cc8eea858c9204761b10670d2ae8fed0` | `PENDING_HUMAN_AUDIO_REVIEW` |

Runtime root: `E:\OpenClaw_VideoFactory_Runtime\phase1_audio_contract_20260927_v7`.

The 2026-09-28 objective integrity evidence is
`reports/phase1/stage_20260928/audio_integrity_evidence.json`.
It proves both v7 files retain each complete raw PCM segment, add only silence,
preserve segment order, and match their declared endpoint/hash. This evidence does
not approve pronunciation, pacing or engineering meaning.

The optional cached-model probe is
`reports/phase1/stage_20260928/audio_asr_secondary_evidence.json` and is
`NOT_RELIABLE_ENOUGH`: the small model garbled Flash technical Chinese and
missed required FreeRTOS anchors. It used an already-cached snapshot, performed
no download, and has no Phase 1 Gate authority.

## Source-aligned narration architecture

```text
source-bound script
→ local TTS raw segments + SHA/duration
→ overflow fail closed
→ at most one deterministic fact-preserving fixture rewrite
→ re-synthesize and measure
→ frame-aligned scene allocation
→ complete raw segment + silence padding only
→ SRT/timeline/renderer from that allocation
```

`plan_source_aligned_narration()` is the shared production/proof helper.
`align_complete_segments()` now proves, using a stable PCM representation:

1. aligned duration is not shorter than raw duration;
2. aligned PCM starts with the complete raw PCM;
3. the remaining PCM is silence only;
4. aligned segments concatenate in scene order;
5. final audio endpoint matches the allocated timeline within tolerance.

The review package must reject source-aligned evidence that lacks these objective
fields. ASR is not required for this contract.

## Human audio-quality gate

The gate remains non-delegable only for subjective quality:

- pronunciation and technical-term intelligibility;
- natural pacing and scene pauses;
- whether the concise rewrite communicates the engineering idea;
- audible TTS artifacts, duplication or unexplained silence.

It no longer proves waveform completeness. Engineering work continues while the
gate is pending. Record a separate SHA-bound `AUDIO_APPROVED` or
`CHANGES_REQUIRED` decision per topic.

## Accepted visual and lifecycle evidence

- Flash geometry repairs are accepted at bounded still level from `a641482`.
- FreeRTOS scene 2/3/4/5 geometry repairs are accepted at bounded still level from
  the preserved repair lineage; old full candidates remain invalid for audio reasons.
- The 2026-09-06 cancel, failed-retry, restart-recovery and encoder-fallback
  lifecycle evidence is complete. Revalidate hashes/schema before manifest binding;
  do not rerun without a concrete incompatibility.
- CAN visual preflight is now reproducible from `scripts/phase1_can_visual_preflight.py`:
  each registry SHA is compared to the PNG, Pillow and FFmpeg decode are checked,
  dimensions and safe-area bounds are measured, generator provenance is hashed,
  scene/asset/tag mapping is checked, five real subtitle stills are emitted, and
  the technical-cut command is inspected for concat/no-xfade behavior. The report
  is `PASS_BOUNDED_STILL_ONLY` with transition probe
  `PASS_BOUNDED_TIMELINE_ONLY`; it does not create an MP4 or grant outer render
  authorization.
- I2C candidate and its human review remain unresolved and must be bound to its exact
  final SHA before Prereview.

## Live-topic boundary

The live topic must use the same source-aligned production contract. The current
hard-coded concise rewrite is fixture-specific to Flash and FreeRTOS. A live topic
whose original narration exceeds the 25–60 second budget must fail closed; it must
not reuse those fixture rewrites, apply `atempo`, or silently trim speech.

## Ordered work packages

### WP-A — canonical truth synchronization

Synchronize `START_HERE_CODEX.md`, `PROJECT_STATUS.yaml`,
`docs/CURRENT_ARCHITECTURE.md`, `runbook/11_PHASE1_COMPLETION.md`, `tasks/todo.md`
and current evidence. Mark stale “FreeRTOS has no render” and “fresh lifecycle
evidence required” statements as superseded without rewriting history.

### WP-B — objective narration-preservation contract

Add RED tests for a truncated aligned segment and GREEN tests for complete prefix plus
silence. Persist raw/aligned hashes, PCM comparison, segment order and endpoint
evidence in `narration_alignment` and review packages. No ASR or new model download.

### WP-C — optional cached ASR probe

Only if an already-cached faster-whisper model is immediately usable: compare the
known rewritten text with normalized transcripts for both v7 WAVs. Mark the result
`USE_AS_SECONDARY_WARNING` or `NOT_RELIABLE_ENOUGH`; never make it a Phase 1 gate.
Do not install WhisperX, MFA or Piper.

### WP-D — human audio-quality gate

Present the exact v7 WAVs and record separate SHA-bound decisions. This may run in
parallel with WP-A, WP-B, WP-C and non-dependent evidence work.

### WP-E — no-render outer-path integration audit

Prove `source_aligned_narration=true` causes the real outer path to use the shared
planner, rewritten script, measured timeline, SRT and complete aligned audio. Capture
hashes for original/revised scripts, raw/aligned segments, timeline and SRT. Stop on
a second rewrite or a total over 60 seconds.

### WP-F — fresh fixed-fixture candidates

After WP-B passes and that topic's WP-D is `AUDIO_APPROVED`, run exactly one fresh
Flash or FreeRTOS `create-topic → run` in an isolated runtime. Require genuine
SQLite `PENDING_REVIEW`, attempt 0, complete narration, endpoint agreement, package
hash integrity, full decode, technical-cut and whole-video semantic review. A clean
machine result is `FLASH_WATCHDOG_MACHINE_REVIEW_READY` or
`FREE_RTOS_MACHINE_REVIEW_READY`.

### WP-G — non-dependent closure work

Revalidate I2C package/hash, audit and preflight the live-topic path, revalidate the
four lifecycle files, prepare the boundary-audit inventory, and build a provisional
manifest with unresolved human-review slots explicitly marked unresolved. Never call
that provisional manifest passing.

### WP-H — live-topic qualification

Qualify one distinct live topic through factual brief, source-bound script, technical
visuals, source-aligned audio, MP4, machine review, human review and Prereview.

### WP-I — final closure

After Flash, FreeRTOS, I2C and live-topic Prereviews are ready: revalidate lifecycle
evidence, create the boundary audit, run bounded regression, assemble `topic_only_v1`,
run an independent read-only audit, then run the Formal Gate exactly once. PASS may
promote Phase 1 and stop. FAIL remains evidence and starts remediation.

## Stop conditions and prohibitions

- Any overflow, truncation, non-silent tail, segment-order mismatch or endpoint drift;
- second rewrite attempt or allocation over 60 seconds;
- missing source/fact binding or unsupported rewrite claim;
- reuse of historical truncated candidates;
- fabricated human approval or passing manifest with unresolved slots;
- `atempo`, hidden `-t` trimming, unapproved model/node download, Phase 2/Cron,
  automatic publication, Owner-main retrofit, force push or historical evidence mutation.

## NEXT_EXPECTED_STEP

Remote iteration 27 independently accepted Candidate001 at reviewed HEAD
`29b8031a2afda4bde746fa9864392262d847bc8a`:

- `RESULT: LIVE_CAN_MACHINE_REVIEW_READY_CONFIRMED`;
- `SECOND_CAN_CANDIDATE: NOT_AUTHORIZED`;
- `FORMAL_GATE: NOT_AUTHORIZED`;
- Candidate001 is frozen and must not be rerendered, transcoded, overwritten or replaced.

Remote acceptance is recorded separately in
`reports/phase1/stage_20260928/can_candidate001_remote_review.json`; the original
local audit remains unchanged with `PASS_READ_ONLY_LOCAL`. Candidate001 remains:
control job `job-eb356764914b0d9f5ccb94ff`, video job `phase1_91c2a7cd2b692884`, MP4
SHA `e50308e53a60f557085b07b58d02827dd7fc52583abe9b3041c0b86415c320af`, review
package SHA `cef8dc5ab243f468c7aee69b0b628f9aba25d3ca85bb7d7ba5222b1ebbd0248f`.

### WP-H3 — exact-SHA human review

Jovi must watch/listen to the complete 51.033008 s MP4 and record a structured
decision bound to the exact control job, video job and MP4 SHA. Review dimensions:
audio intelligibility/quality, subtitle readability/timing, technical correctness,
visual composition, transition acceptability and overall acceptability. Machine
evidence cannot fill this decision. If `CHANGES_REQUIRED`, freeze Candidate001 and
return for a new remote remediation plan. If explicitly `APPROVED`, persist the
exact-SHA human-review artifact and run only the existing read-only CAN prereview;
do not rerender.

### Parallel work

- `reports/phase1/stage_20260928/i2c_restoration_discovery.json` records a read-only
  search for expected I2C SHA `cf1c022...`; no exact MP4 match was found, so the
  status remains `I2C_BLOCKED:FINAL_RUNTIME_MEDIA_MISSING_FOR_REVALIDATION`.
- The provisional inventory now records
  `LIVE_CAN_MACHINE_REVIEW_READY/HUMAN_REVIEW_PENDING` while keeping the final
  manifest and Formal Gate blocked.
- Flash and FreeRTOS exact v7 audio gates remain independent and unresolved.

The next evidence-only update must preserve Candidate001, record the remote review,
keep the provisional inventory explicit, and never run a second CAN candidate or
Formal Gate. Final topic closure remains blocked until all four topic slots have
exact-SHA human approvals and read-only prereviews.

### WP-J readiness evidence

Remote iteration 28 accepted the evidence continuation at `212b1bc`. The local
readiness package at `8a80f53` contains:

- `human_gate_binding_readiness.json`: `PASS_NO_HUMAN_DECISION_CREATED`;
- `can_prereview_contract_readiness.json`: `READY_PENDING_HUMAN_APPROVAL`;
- `flash_next_candidate_readiness.json` and `freertos_next_candidate_readiness.json`:
  `READY_PENDING_EXACT_AUDIO_APPROVAL`, with no create-topic or render;
- `i2c_requalification_dossier.json`:
  `I2C_RESTORATION_EXHAUSTED_REQUALIFICATION_NOT_YET_JUSTIFIED` because the old
  audio-contract compatibility cannot be proven from missing runtime media;
- the provisional inventory now exposes explicit CAN/Flash/FreeRTOS/I2C
  dependencies while remaining unresolved and Gate-blocked.

The focused acceptance binding suite passed 13 tests. No human decision, prereview,
new job, I2C requalification or media artifact was created. The next authorized
action is Jovi's exact-SHA CAN review; once an explicit approval arrives, only the
existing read-only CAN prereview may run for the frozen control job.

### WP-J review hardening follow-up

Remote iteration 29 identified one contract-test gap: the readiness evidence had
to exercise concrete wrong-SHA and wrong-control-job review inputs, not only
missing/malformed/unresolved inputs. The local script now creates both cases only
inside a temporary directory, evaluates them through the real prereview binding,
and discards them. Both report `human_review_not_approved`; no human decision file
is persisted. The refreshed report records
`wrong_sha_binding_blocks=true`, `wrong_job_binding_blocks=true`, and
`negative_fixture_scope=ephemeral_tempdir_only_discarded_not_a_human_decision`.

Verification: `PYTHONPATH=. python scripts/phase1_human_gate_readiness.py`,
`python -m pytest -q tests/phase1_acceptance/test_phase1_acceptance.py` (13
passed), `py_compile`, and `git diff --check` all pass. No new job, render,
prereview, human decision, or Formal Gate was run.

## WP-K closure-contract freeze — remote iteration 30

Remote iteration 30 independently accepted the J6 hardening at reviewed HEAD
`4028236a61a4a329427eaf27edb846d89a44f751` as `WP_J6_ACCEPTED`. It confirmed
that the real `evaluate_job_prereview()` path rejects both wrong-SHA and
wrong-control-job temporary fixtures. The limitation remains explicit: those
synthetic fixtures use `decision=changes_required`; the eventual final audit
must also confirm that `approved=true` cannot override a mismatched binding.
No persisted synthetic approval is allowed.

The no-media WP-K1 through WP-K5 package is now frozen in these reports:

- `topic_only_v1_manifest_contract_readiness.json`:
  `MANIFEST_CONTRACT_READY_FINAL_EVIDENCE_PENDING`. It enumerates the four
  topic slots (Flash, FreeRTOS, I2C and CAN Candidate001), required exact-SHA
  fields, lifecycle hashes, final-boundary requirement and negative blockers.
- `final_regression_contract.json`:
  `FINAL_REGRESSION_PLAN_FROZEN_NOT_RUN`. It records the exact Phase 1,
  local, bounded-video, director, reference, video-factory, Remotion and
  compile/diff commands. The four ignored-fixture video modules are explicitly
  excluded from the bounded run and cannot be silently aggregated into a final
  count.
- `final_boundary_contract.json`:
  `FINAL_BOUNDARY_CONTRACT_FROZEN_NOT_RUN`. `PASS_PRELIGHT` is recorded as a
  preflight limitation and cannot substitute for a manifest-bound final audit.
- `i2c_requalification_decision.json`:
  `I2C_RESTORATION_EXHAUSTED_FRESH_REQUALIFICATION_IS_ONLY_VERIFIABLE_PATH`.
  Existing runtime/worktree/owner scopes found no exact MP4/package/SQLite
  snapshot. The report lists the minimal future requalification package but
  does not authorize it.

The provisional inventory now records CAN machine-ready/human-pending,
independent Flash and FreeRTOS audio gates, I2C blocked, lifecycle revalidated,
boundary preflight-only, final regression not run, manifest not ready and Formal
Gate not run. Candidate001 remains frozen at control job
`job-eb356764914b0d9f5ccb94ff`, video job `phase1_91c2a7cd2b692884`, MP4 SHA
`e50308e53a60f557085b07b58d02827dd7fc52583abe9b3041c0b86415c320af`.

### Current NEXT_EXPECTED_STEP

Wait for the event-driven exact-SHA human decisions. CAN `APPROVED` permits only
the existing read-only CAN prereview; Flash or FreeRTOS `AUDIO_APPROVED` permits
exactly one candidate for that topic; approvals never cross topics. I2C remains
unrendered until a separate remote review authorizes the bounded requalification
package described in K4. Once all four topic prereviews exist, run the frozen
regression and final boundary contracts, assemble the actual manifest, perform
the independent audit, and only then request a Formal Gate. No new media,
prereview, human decision or Gate action is part of the current handoff.

## WP-L execution result — remote iteration 31 authorization

The single authorized I2C `create-topic` created control job
`job-b4a2e8e851268bc14e5e4a15` at attempt 0 from the frozen L0 input. The one
authorized `run` was invoked exactly once. The control plane advanced through
`NEW → RESEARCHING → SCRIPTING → VOICE → CAPTIONS → ASSETS → RENDERING` and
then failed closed before media output with
`phase1_local_brief_invalid / factual_brief.topic_digest / topic_digest_mismatch`.

Evidence: `reports/phase1/stage_20260928/i2c_requalification_candidate001_review.json`.
No MP4, review package, audio-integrity artifact or human decision was created;
attempt remains 0, no retry/resume occurred, and no second I2C candidate exists.
The provisional inventory keeps I2C blocked and records the exact failure.

The failure is terminal under the iteration-31 authorization. Do not retry this
job or silently edit the frozen brief. The next action is remote review of the
digest-contract defect and a new bounded remediation/authorization decision.

## WP-LR1 digest provenance repair — remote iteration 32

Remote iteration 32 accepted the failed I2C Candidate001 as terminal and
authorized no-media digest provenance repair only. The execution contract is
consistent: `build_local_plan()` hashes `normalize_topic(topic)` directly. The
failure came from carrying the historical research digest `ceda09b...` into the
new executable brief.

The historical research file remains byte-identical at SHA
`fd6abe8ff5a5af821d8291f483f2dd22006dea251f34b5152077df9f4f5cbd21`. A small
materializer, `scripts/phase1_i2c_brief_materializer.py`, now rebuilds the
current executable brief with digest
`dcc85f8913bc9bd6b1f3c049537745745f21b37a9fb4ff971bc91e1017948d00`, preserving
the three fact IDs and two source IDs. The repaired brief is
`examples/phase1_subject_i2c/phase1_local_brief_9x16_repaired.json` with SHA
`f355b5161be0783a89bde0ccf7c121ac7135491593b4d3b3270c90f3dba90926`.

RED/GREEN evidence is in
`reports/phase1/stage_20260928/i2c_digest_contract_repair.json`:

- the stale brief is rejected with `topic_digest_mismatch`;
- the repaired brief passes `load_local_brief()` and `build_local_plan()`;
- the plan retains `open_drain`, `rise_time`, `sink_current`, both source IDs,
  and the 1080×1920/30fps 9:16 profile;
- focused provenance tests pass 2/2; no create-topic, run, TTS or media ran.

The failed job `job-b4a2e8e851268bc14e5e4a15` remains terminal and must never be
retried or mutated. Candidate002/new I2C media remains unauthorized pending
remote review of this repair.

## WP-L2 Candidate002 authorization — remote iteration 33

Remote iteration 33 accepted the digest repair at reviewed HEAD `a9d43d0` and
authorized exactly one new unique I2C Candidate002. The repaired executable brief
is `examples/phase1_subject_i2c/phase1_local_brief_9x16_repaired.json` with SHA
`f355b5161be0783a89bde0ccf7c121ac7135491593b4d3b3270c90f3dba90926` and current
execution digest `dcc85f8913bc9bd6b1f3c049537745745f21b37a9fb4ff971bc91e1017948d00`.

Execution boundary: create one new unique I2C control job with idempotency key
`phase1-i2c-requalification-candidate002-20260928`, then run it exactly once.
No retry, resume or Candidate003. Candidate001
`job-b4a2e8e851268bc14e5e4a15` remains terminal and immutable. Machine acceptance
requires authentic SQLite `PENDING_REVIEW`, attempt 0, package/artifact hash
binding, source-aligned objective audio integrity, 1080×1920/30fps H.264/AAC
full decode, technical-cut frame proof, whole-video I2C semantic review and an
independent local audit. Human video review remains pending; prereview and all
final contracts remain unrun.
