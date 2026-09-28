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

The WP-A/WP-B/WP-C/WP-E package is complete and independently accepted after the
lineage seal. Local Codex next executes, without fresh Flash/FreeRTOS rendering:

1. WP-G1 I2C exact-candidate audit;
2. WP-G2 lifecycle evidence final schema/hash revalidation;
3. WP-G3 boundary-audit preflight;
4. WP-G4 distinct live-topic no-render preflight;
5. WP-G5 provisional manifest inventory with unresolved human slots explicit.

The next evidence commit must keep `code_contract_commit=cf02b37`,
`evidence_commit=5e74b6a`, and the sealed handoff parent lineage explicit. Human
audio-quality decisions remain separate unresolved product gates; no fresh
Flash/FreeRTOS video is authorized until the matching exact v7 SHA receives
`AUDIO_APPROVED`.
