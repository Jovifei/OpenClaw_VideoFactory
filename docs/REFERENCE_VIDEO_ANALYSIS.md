# Local Reference Video Analysis and Original Reconstruction

Updated: 2026-09-05

## Purpose

Phase 1 must support a user-provided, owned/licensed local reference video without turning the project into a downloader, clip copier, or platform scraper.

The reference path exists for two reasons:

1. learn **topic / coarse structure / pace / generic expression clues**;
2. prove that the factory can then produce a **new, independently rendered video** with auditable originality evidence.

## Safe ingest

`src/factory/reference_video.py` accepts a local `.mp4` and rights record, then:

- rejects unsafe extension/path/reparse cases;
- validates the container with `ffprobe`;
- computes SHA-256;
- copies the media to the ignored private reference store;
- makes the stored copy read-only where supported;
- writes `reference_receipt.json` and `reference_rights.json`;
- keeps source media outside Git and outside the public review package.

The original file is never treated as a renderer asset.

## Phase 1 analysis

Current conservative analysis uses:

- FFmpeg/ffprobe for media facts;
- PySceneDetect 0.7.1 for scene boundaries;
- scene duration / shot density / pace abstraction;
- optional faster-whisper 1.2.1 `small` only when an already-approved local cache exists.

If the ASR cache is missing, the result is recorded as unavailable. Phase 1 does **not** automatically download a speech model.

`reference_report.json` contains abstract evidence. It must not contain source frames, source audio, local cache paths, provider prompts, or full source material.

## Original brief

`original_brief.json` binds:

- user topic;
- verified factual brief;
- source SHA-256;
- coarse reference abstraction such as pace, scene-count band and duration guidance.

It does not grant the renderer access to source footage.

## Reconstruction

The current branch has advanced beyond the first conservative adapter. The reconstruction path now also proves a bounded, original visual rebuild:

```text
reference report
  ↓
original brief
  ↓
new script + new storyboard
  ↓
new technical cards / Remotion visual
  ↓
new local narration
  ↓
measured speech timing / visual cues
  ↓
new MP4
  ↓
difference report + quality evidence
  ↓
Jovi human originality review
```

The RC high-pass work on this branch is the main recent example. It introduced:

- a dedicated technical Remotion composition;
- corrected circuit geometry and visible engineering equations;
- local TTS/SAMI subsegments;
- measured speech cues;
- knowledge-card animation driven by the actual narrated phrase start instead of a free-running loop;
- post-render and critical-frame checks;
- an optional Jianying editable-draft branch for human listening/visual review.

These improvements are reusable architecture, not permission to reuse the source video's shots.

## Originality rules

Forbidden:

- source audio;
- source watermark/logo reuse;
- continuous source shots;
- complete source transcript or copied script;
- identifying source packaging;
- a shot-by-shot reconstruction that merely changes colors/assets;
- source path or raw frame leakage into review artifacts.

Allowed in Phase 1:

- topic;
- generic structure labels;
- coarse pace;
- scene-count band;
- timing statistics;
- independently verified facts;
- newly drawn/re-rendered technical explanation visuals.

## Difference report

`difference_report.json` is an automatic prereview aid, not a copyright oracle. It currently verifies machine-checkable boundaries such as:

- source and output hashes differ;
- source path is absent;
- output assets come from approved Registry/technical sources;
- narration is newly produced;
- source audio is absent;
- text similarity stays within the configured conservative policy when evidence is available.

Human review remains required for:

- watermark/logo similarity;
- face/person similarity;
- perceptual-frame similarity;
- shot-sequence similarity;
- overall "does this feel like a near-copy?" judgment.

Advanced automated perceptual checks belong to Phase 4 and do not block the Phase 1 conservative path.

## CLI

```powershell
python scripts/factory.py phase1 create-reference `
  --video <local.mp4> `
  --brief <topic-brief.json> `
  --rights <rights.json>

python scripts/factory.py phase1 run --job-id <control-job-id>
python scripts/factory.py phase1 status --job-id <control-job-id>
```

`--brief` must already contain a verified factual brief. The command creates a hash-bound reference job and stores the raw reference outside Git.

## Current completion status

Implementation: mature / review-ready in multiple subprojects.

Phase 1 completion: **not yet passed**.

Remaining work for the final Gate:

- align the latest real reference reconstruction candidate with the standard Phase 1 Review/Prereview contract;
- obtain Jovi's actual visual/audio/originality review;
- if the acceptance manifest requires a private `local_reference` fixture distinct from historical public-reference experiments, use a Jovi-authorized local MP4 and rights record;
- include the resulting prereview in the final Acceptance Manifest;
- pass the one-shot Phase 1 Gate.
