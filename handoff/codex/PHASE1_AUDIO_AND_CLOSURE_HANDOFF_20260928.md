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

## WP-L2 Candidate002 execution result — remote iteration 33 authorization

The single authorized Candidate002 job was `job-b1a186b7b265c2ed46b7c3cb`,
attempt 0, created from the repaired brief. Its one `run` advanced through
`ASSETS` and `RENDERING`, then failed with
`phase1_local_execution_failed:value_error` before media output.

The plan artifacts also expose a route defect: the current executable local
brief selected generic Modbus/Flash knowledge registry assets and emitted no
I2C `visual_spec` for any scene. It did not select the accepted I2C 9:16
source-bound lineage. This is recorded in
`reports/phase1/stage_20260928/i2c_requalification_candidate002_review.json`.
No MP4, review package, audio-integrity artifact or human decision exists;
Candidate001 remains terminal and Candidate003 is forbidden. Do not retry
Candidate002 until remote review authorizes the exact route repair.

## WP-LR2 subject-route integration — remote iteration 34

Remote iteration 34 independently accepted Candidate002's terminal failure as
a route mismatch. The local-brief deterministic fallback selected generic
Modbus/Flash registry assets and emitted no I2C visual specs. Candidate001
(`job-b4a2e8e851268bc14e5e4a15`) and Candidate002
(`job-b1a186b7b265c2ed46b7c3cb`) remain immutable terminal failures;
Candidate003, full media, prereview and Formal Gate remain unauthorized.

The canonical route is now explicitly:

```text
create-subject
→ attach-research (examples/phase1_subject_i2c/research_brief.json)
→ run --plan-only
→ source-bound director script / scene plan
→ TechnicalExplainer i2c_bus_v1
```

No-render route evidence is in
`reports/phase1/stage_20260928/i2c_subject_route_preflight.json`:

- isolated non-candidate plan-only job `job-d0ad2349f3a61c8250603737` reached
  `ASSETS` without TTS, MP4, WAV, MP3 or AAC output;
- canonical research SHA remains
  `fd6abe8ff5a5af821d8291f483f2dd22006dea251f34b5152077df9f4f5cbd21`;
- three fact-bound scenes emit `i2c_bus_v1` for
  `open_drain`, `rise_time`, and `sink_current`;
- labels are exactly `SDA/SCL/START/ADDRESS/ACK/NACK/DATA/STOP`;
- bounded Remotion still evidence is `PASS_BOUNDED_STILL_ONLY` at 1080x1920,
  30fps; no `renderMedia` or MP4 was created;
- technical-cut boundaries are contiguous in the still timing contract only.

Verification on the current worktree: the focused subject/I2C/audio/video set
passes `102`; `tests/phase1_acceptance` passes `24`; compileall, diff check,
Remotion typecheck and Remotion contracts pass. The broader schema test was
not counted because its ignored `dist/story_demo/timeline.json` fixture is
absent in this isolated worktree (93 passed plus 7 fixture setup errors when
that file-dependent module is included).

The smallest source-aligned audio adapter is
`src/factory/phase1_subject_audio.py`. It reuses
`plan_source_aligned_narration()` and maps subject research facts into the
shared validator; I2C anchors were added to that shared validation table. The
subject media path now receives `research_brief`, uses the adapter before any
media stage, emits runtime `audio_integrity.json`, and binds the optional
integrity artifact into the subject receipt/package when a media candidate is
later authorized. Adapter and route regressions are in
`tests/phase1_local/test_phase1_subject_audio.py`,
`tests/video/test_phase1_subject_media.py` and
`tests/video/test_i2c_semantic_visual.py`. The current preflight intentionally
does not claim production PCM evidence because full media is not authorized.

### Current NEXT_EXPECTED_STEP

Return exact pushed HEAD and the WP-LR2 reports/tests to remote GPT for
independent review. Candidate003 may be considered only after remote accepts
the route proof and explicitly authorizes one new subject-path candidate. Keep
CAN exact-SHA human review, Flash/FreeRTOS audio approvals, all prereviews,
final contracts and Formal Gate unchanged and pending.

## WP-LR3 subject-audio production wiring — remote iteration 35

Remote iteration 35 accepted the LR2 visual/planning evidence but found one
remaining production boundary before Candidate003: subject delivery must
resolve the exact SQLite-registered research artifact, verify its path/SHA/topic
identity, and pass that artifact into the shared source-aligned audio adapter.
Candidate001/002 remain terminal; Candidate003 and all media remain
unauthorized.

The bounded repair must:

- resolve the single `research_brief` artifact registered for the job;
- require `subject_root/research_brief.json` inside the subject root, regular
  and non-symlink;
- recompute and compare its SHA to the SQLite artifact record;
- verify topic and digest identity against `topic_request.json` and job metadata;
- pass the exact path as `SubjectMediaRequest.research_brief`;
- map subject source `id` to shared factual `source_id` and verify all fact
  references resolve.

Add a real CLI orchestration regression that stops before TTS/render/media while
proving the bound request argument and artifact hash. The current isolated
adapter test is not sufficient by itself; this boundary test is the remaining
gate.

### LR3 NEXT_EXPECTED_STEP

Execute only the no-media wiring repair, create
`reports/phase1/stage_20260928/i2c_subject_audio_wiring_repair.json` with
RED/GREEN evidence, rerun focused suites and Phase 1 acceptance, push the
bounded commit, and return for independent remote review. Do not create
Candidate003, run create-topic, or enter any human/prereview/Gate state.

## WP-L3 Candidate003 execution result — remote iteration 36

Remote iteration 36 authorized exactly one fresh I2C subject-path Candidate003.
The exact create-subject, attach-research and run boundaries were consumed once
for control job `job-d0ad2349f3a61c8250603737`, attempt 0, idempotency key
`phase1-i2c-requalification-candidate003-20260929`. The control plane reached
`NEW -> RESEARCHING -> SCRIPTING -> FAILED` during subject planning.

Evidence: `reports/phase1/stage_20260929/i2c_requalification_candidate003_review.json`.
No director script, scene plan, TTS, audio-integrity file, MP4, review package,
human decision, prereview or Gate artifact was created. The failure is
`phase1_subject_planning_failed`; the isolated worktree lacks the pinned
`external/MoneyPrinterTurbo` runtime/venv required by the script-drafter before
planning can produce candidates. Candidate001/002 remain immutable terminal
failures. Candidate004 is not authorized and Candidate003 must not be retried.

### Current NEXT_EXPECTED_STEP

Return the terminal Candidate003 planning failure and exact dependency evidence
to remote GPT. Await an explicit dependency-restoration/new-candidate plan;
do not retry this job or create Candidate004. CAN human review and Flash/
FreeRTOS audio gates remain pending; prereview, final contracts and Formal Gate
remain prohibited.

## WP-M0-M3 dependency restoration — remote iteration 37

Remote iteration 37 authorized dependency restoration and identity verification
only. MoneyPrinterTurbo was restored from the existing local Owner cache at
approved revision `eb8c23757e098a07bbcd93b3b50e252fc8d1869a`, with its CLI and
venv present and checkout clean. The exact pinned `jianying-editor-skill`
revision `f421c8a036f4fda888a83b38fc90bb9c00d6faa9` has no local clone/archive;
the network fetch failed at GitHub connectivity. Evidence:
`reports/phase1/stage_20260929/i2c_subject_dependency_restoration.json`.

Per the remote stop condition, M2/M3 planning and Jianying dry readiness were
not run. Candidate003 remains terminal, no retry/Candidate004 is authorized,
and no media or Gate action occurred. Await remote decision on an approved
offline Jianying dependency source before further work.

## WP-M2 MPT planning-only diagnostic — remote iteration 38

Remote iteration 38 accepted the exact restored MoneyPrinterTurbo pin and
authorized one fresh non-candidate diagnostic. The job must use an isolated
runtime/database and execute exactly `create-subject -> attach-research ->
run --plan-only` for `I2C总线为什么要上拉电阻`, then stop at `ASSETS`.

Required proof is actual MPT `eb8c23757e098a07bbcd93b3b50e252fc8d1869a`
CLI/venv invocation, selected/director/scene-plan artifacts, source-bound
`open_drain`, `rise_time`, `sink_current` facts, three `i2c_bus_v1` scenes and
the required SDA/SCL/START/ADDRESS/ACK-NACK/DATA/STOP labels. The diagnostic
must create no TTS/WAV/PCM/audio-integrity/MP4/Jianying output and cannot be
promoted into Candidate004. Candidate003 remains permanently terminal.

Jianying exact pin `f421c8a036f4fda888a83b38fc90bb9c00d6faa9` remains blocked;
only an exact local clone/archive or exact-pin network fetch may unblock M3.

### WP-M2 result — terminal planning failure

The separately authorized non-candidate diagnostic used runtime
`i2c-mpt-plan-probe-20260929` and isolated SQLite. `create-subject`,
`attach-research` and `run --plan-only` each ran exactly once for the
canonical I2C subject. The restored MPT revision
`eb8c23757e098a07bbcd93b3b50e252fc8d1869a` and its Python 3.12.10 venv were
actually used; `cli.py --stop-at script` ran three candidate processes, all
exited 1, and produced no parseable script JSON. The adapter wrote a failure
summary and the control job ended `FAILED` at the planning boundary.

Evidence: `reports/phase1/stage_20260929/i2c_subject_mpt_planning_probe.json`.
The job has only the attached research artifact; no selected/director/scene
plan, TTS, WAV, PCM integrity, MP4, Jianying call, review package, human
decision, prereview or Gate artifact exists. The diagnostic is non-candidate
and cannot become Candidate004. Candidate003 remains permanently terminal;
the same deterministic job id is isolated in a separate diagnostic database
and is not a retry of the production Candidate003 database.

Bounded verification passed: 42 focused subject/audio/Phase1 acceptance tests,
Python compileall, Remotion typecheck, Remotion contracts and git diff check.
The pushed evidence commit is `5e551f1` on
`codex/phase1-audio-closure-20260928`.

Current next action: return the exact MPT CLI failure for remote independent
audit. Do not retry the diagnostic, change the MPT pin/provider, restore
Jianying from an unverified source, create Candidate004, or run media. M3 is
still blocked on exact Jianying pin `f421c8a...`.

## WP-M4 MPT provider/config diagnosis — remote iteration 39

Remote iteration 39 classified the M2 diagnostic as terminal with an opaque
provider execution failure. The exact MPT source/venv/CLI started and loaded
`config.toml`, but the three script subprocesses exited 1; the adapter did not
retain the underlying exception. The accepted architecture remains:
verified subject research → pinned MPT planning → source-bound I2C scenes →
shared measured narration/PCM → exact Jianying media path.

M4 is authorized without any Phase1 job, CandidateStore mutation, candidate,
TTS or media. Read only structural config metadata and record provider/model,
endpoint hostname, required credential-variable names and PRESENT/MISSING
status, config SHA, exact MPT revision and Python/CLI identity. Test only DNS,
TCP/TLS reachability for that configured endpoint. Then execute exactly one
direct pinned `cli.py --stop-at script` diagnostic outside the Phase1 path and
persist only sanitized exception class, safe message, HTTP status, host,
provider/model and traceback modules. Never persist raw config, keys, tokens or
auth headers; do not change provider/model/config/credentials.

Report: `reports/phase1/stage_20260929/mpt_provider_diagnostic.json` with one
of the remote-approved `MPT_PROVIDER_*` statuses. Only
`MPT_PROVIDER_READY` can return for separate M6 authorization of one new
non-candidate `create-subject -> attach-research -> run --plan-only` job.
Jianying exact pin `f421c8a...` remains independently blocked; Candidate003,
Candidate004, media and Formal Gate remain prohibited.

### WP-M4 execution result — direct invocation stopped before provider

The M4 structural inventory is complete without persisting raw config. The
effective `[app]` configuration is provider `openai`, model `mimo-v2.5`,
endpoint host `token-plan-cn.xiaomimimo.com`, and the active config credential
field is present. The approved `MIMO_API_KEY` environment input is present;
`MPT_LLM_API_KEY` is missing. The config SHA, exact MPT revision, Python 3.12.10
and CLI SHA are recorded in the report. DNS, TCP and TLS 1.3 to the configured
host all passed.

The one authorized direct CLI attempt was outside Phase1/CandidateStore and
created no media or job state, but MPT rejected the diagnostic `--task-id`
before provider execution because the value was not a UUID. Therefore the
report status remains `MPT_PROVIDER_BLOCKED:UNCLASSIFIED`; it does not prove
provider readiness or a provider/network/auth blocker. The corrected command
uses UUID `d7b3d8c2-35bd-4bd7-9bf9-0b00b2d1a4b6` but has not been run and
requires remote reauthorization.

Evidence: `reports/phase1/stage_20260929/mpt_provider_diagnostic.json` and
`reports/change_requests/PHASE1-WP-M4-MPT-PROVIDER-DIAGNOSTIC-20260929.json`.
Until remote reauthorization, do not run the corrected direct command, create
a Phase1 job, retry Candidate003, create Candidate004, invoke Jianying or run
media.

### WP-M4B corrected direct diagnostic — provider AUTH blocker

Remote iteration 40 separately authorized exactly one corrected direct call
using valid task UUID `d7b3d8c2-35bd-4bd7-9bf9-0b00b2d1a4b6`, unchanged exact
MPT pin/venv/config/provider/model and no Phase1 job. The call reached the
configured provider path and returned sanitized HTTP `401 Invalid API Key`.
The report status is now `MPT_PROVIDER_BLOCKED:AUTH`. No key, header, raw
config or generated script text was persisted; no media or CandidateStore
mutation occurred. The prior invalid-UUID attempt remains under
`prior_invalid_invocation` as historical evidence.

This proves the configured credential is rejected by the approved endpoint; it
does not authorize credential rotation, provider/model changes, or a new
plan-only job. Candidate003 remains terminal, Candidate004 and M6 remain
prohibited, and Jianying exact pin `f421c8a...` remains unavailable. Return
the AUTH evidence for remote review and await an approved existing credential
or config restoration source.

The diagnostic sanitizer/structural checks and the affected subject/audio/
Phase1 acceptance suite passed: 45 tests total. Python compile and diff checks
also passed. Evidence is pushed in commit `8fab3f8` on
`codex/phase1-audio-closure-20260928`; the corrected direct MPT call executed
exactly once and returned the AUTH blocker. The updated AUTH evidence commit is
`d81ff87`; M6 remains NOT_AUTHORIZED pending remote review.
