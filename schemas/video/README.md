# Video Technical Contract Schemas (`schemas/video/`)

## Purpose

This directory contains **JSON Schemas for a single video synthesis pipeline** — the technical contract between:
- **Storyboard** (director semantics layer) → AI Director's output format
- **Timeline** (render execution layer) → Renderer's input format
- **VideoRenderJob** (job entry point) → Complete synthesis job definition

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

## Schema Conventions

- `$schema`: `https://json-schema.org/draft/2020-12/schema`
- `$id`: `https://openclaw.local/schemas/video/<name>.schema.json`
- Every document instance carries `schema_version` (string `"MAJOR.MINOR"`, currently `"1.0"`)
- All schemas use `additionalProperties: false` unless explicitly extended
- Failed `video_job_state` snapshots carry a structured `error` object with
  `code`, `message`, and `context`.
