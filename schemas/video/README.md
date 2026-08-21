# Video Technical Contract Schemas (`schemas/video/`)

## Purpose

This directory contains **JSON Schemas for a single video synthesis pipeline** — the technical contract between:
- **Storyboard** (director semantics layer) → AI Director's output format
- **Timeline** (render execution layer) → Renderer's input format
- **VideoRenderJob** (job entry point) → Complete synthesis job definition
- **Composition** (safe-region layout layer) → Knowledge illustration renderer/subtitle layout

## Responsibility Boundary (CRITICAL)

| Location | Semantic | Consumer |
|---|---|---|
| `schemas/video_job.schema.json` (**existing, DO NOT MODIFY**) | **Task state machine**: `job_id`, `state`, `selection_mode`, `retry_count`, `artifacts` | Scheduler & state storage |
| `schemas/video_workflow/*` (**existing 17 schemas, DO NOT MODIFY**) | End-to-end content production business flow: topic selection, script, style, publishing, postmortem | Upper-layer business orchestration |
| `schemas/video/*` (**THIS DIRECTORY, new in Phase 1**) | **Single video synthesis technical contract**: job input, director storyboard, render timeline, and lifecycle snapshot | `video_factory/` pipeline |

### One-line distinction

- `video_workflow/` manages **"what content to produce"**
- `video/` manages **"how to synthesize this specific video"**
- Root-level `video_job.schema.json` tracks **"which step is this task at"**

`video_job_state.schema.json` is the local video-factory lifecycle snapshot. It
is linked by `job_id` to a `VideoRenderJob`, but it does not implement
persistence, transitions, retries, or a scheduler. Its states are `draft`,
`validated`, `compiled`, `rendering`, `completed`, and `failed`.

`director_draft.schema.json` is the constrained provider-facing draft produced
by the Phase 2 AI Director. It contains only title, content scope, and 5–9
scene intents; Python deterministically injects registry identity, scene IDs,
render globals, and asset resolution before validating the final Storyboard.

`director_run_report.schema.json` is a sanitized generation evidence contract.
It records provider/version, prompt version, digests, bounded attempt count,
validation statuses, compiled duration, and structured error metadata. It must
not contain raw prompts, model output, credentials, or absolute paths.

The new schemas deliberately avoid the name `VideoJob` (already occupied by the state machine). Their titles are:
- `VideoRenderJob` — in `video_job.schema.json`
- `Storyboard` — in `storyboard.schema.json`
- `Timeline` — in `timeline.schema.json`
- `DirectorDraft` — in `director_draft.schema.json`
- `DirectorRunReport` — in `director_run_report.schema.json`
- `KnowledgeIllustrationComposition` — in `composition.schema.json`

`composition.schema.json` is the shared optional composition contract referenced
by Storyboard and Timeline. The shipped
`video_factory/configs/compositions/knowledge_illustration.json` reserves a
central content area, a non-overlapping subtitle safe band, and a lower
signature area. Geometry is contract data; pixel-level overlap/occlusion review
remains a render-quality check.

The Pink Pig Registry also records the five repository-owned Modbus RTU
knowledge illustrations. They are content assets (`asset_role:
knowledge_illustration`), not replacements for the eight character poses. The
transparent signature entry is a repository-owned 400×400 RGBA PNG with a
recorded SHA-256 and the existing normal SVG as provenance.

## Schema Conventions

- `$schema`: `https://json-schema.org/draft/2020-12/schema`
- `$id`: `https://openclaw.local/schemas/video/<name>.schema.json`
- Every document instance carries `schema_version` (string `"MAJOR.MINOR"`, currently `"1.0"`)
- All schemas use `additionalProperties: false` unless explicitly extended
- Failed `video_job_state` snapshots carry a structured `error` object with
  `code`, `message`, and `context`.

## Composition scene metadata

Storyboard scenes may carry `asset_id`, `layout_mode`, `subtitle_layout`,
`character_position`, and `content_region`. These fields are optional for
legacy storyboards and are copied deterministically to Timeline scenes when
present. The shipped `knowledge_illustration` contract remains the single
source for the 1080×1920 safe regions; it does not create a second renderer.
## Phase 2 Director contracts

- `director_script.schema.json`: provider-facing semantic script (5–9 beats;
  no asset IDs, paths, registry data, scene IDs, or render parameters).
- `director_factual_brief.schema.json`: source-linked claims and metadata;
  verified status requires at least two sources in the loader policy.
- `asset_selection_report.schema.json`: deterministic Registry asset decisions,
  hashes, rights basis, classification, and fallback evidence.
- `director_quality_report.schema.json`: pre/post-render checks and factual
  review status.
- `video_job_state.schema.json` version `1.0` retains the original six-state
  contract; version `2.0` adds the Director lifecycle and script/quality refs.

These schemas validate snapshots and artifacts only. They do not implement a
database, transition executor, retry engine, or external orchestration.

`director_run_report.schema.json` permits `factual_review_required` to be a
boolean: verified factual briefs use `false`, while topic-only reports use
`true`. The same flag is carried by `video_job_state` so lifecycle and Director
evidence cannot disagree. Remediation 004 errors remain limited to stable,
non-sensitive `code`, `message`, and `context` fields.
