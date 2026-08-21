# AI-DIRECTOR-PHASE2-IMPLEMENTATION-REMEDIATION-004

Date: 2026-08-10  
Branch: `codex/ai-director-video-factory-phase2-001`  
Base HEAD: `76180a59ea662bdf168d88baaeb777d3e8eb59ef`

## 1. Current stage

Formal status remains P0 `not_started`, P1 `blocked_by_P0`, and P2
`blocked_by_P1`. Product capability is Phase 1.5 READY plus a locally
remediated Phase 2 candidate. This report does not promote a formal Phase 2
Gate or claim real-provider acceptance.

## 2. Completed remediation

- Added sanitized execution-error normalization and atomic
  `VideoJobStateMachine.fail()` snapshots with monotonic revisions.
- Wrapped context, storyboard, validation, rendering, and quality failures so
  ordinary exceptions cannot leave `rendering` or `storyboard_ready` behind.
- Cleared reused Director outputs; current-topic failure reports are checked
  and sanitized before persistence.
- Aligned verified factual brief state and Director report to
  `factual_review_required=false`; topic-only jobs remain review-required.
- Retired historical Candidate render/TTS/captions/quality/benchmark modules;
  database, state, inventory, and cancellation controls remain.
- Candidate `create`, `retry`, `run`, `verify`, and `benchmark` fail closed with
  `legacy_candidate_pipeline_retired` and exit code 2. `doctor` reports
  `legacy_control_only` and canonical `generate_video.py`.

## 3. Public contracts and changed files

Key files:

- `generate_video.py`
- `video_factory/pipeline/failure_contract.py`
- `video_factory/pipeline/job_state.py`
- `schemas/video/director_run_report.schema.json`
- `src/factory/director/ai_director.py`
- `src/factory/legacy_candidate_control.py`
- `src/factory/cli.py`
- deleted `src/factory/pipeline.py`, `render.py`, `tts.py`, `captions.py`,
  `quality.py`, and `benchmark.py`
- `tests/director/test_failure_contract.py` and updated legacy retirement tests

Canonical video chain:

```text
generate_video.py -> video_factory.pipeline -> FFmpeg Renderer
```

## 4. Tests and reviews

Executed with the fixed workspace Python:

```text
python -m pytest tests/director -q
python -m pytest tests/video -q
python -m pytest video_factory/tests -q
python -m pytest tests/test_p1_candidate_cli.py tests/test_p1_candidate_pipeline.py tests/test_p1_candidate_media.py tests/test_p1_candidate_render.py tests/test_p1_candidate_delivery.py tests/test_p1_candidate_inventory.py tests/test_p1_candidate_state.py tests/test_p1_final_audit.py -q
```

Results:

- `tests/director`: **47 passed**.
- `tests/video`: **273 passed**.
- `video_factory/tests`: **5 passed**.
- Legacy group: **56 passed, 1 skipped**, 13 subtests; the skip is the
  existing Windows symbolic-link capability test. All 57 legacy test methods
  remain present.
- JSON Schema parse and `git diff --check`: passed.
- Final independent reviewer: **APPROVED**.

## 5. Media evidence

Non-Provider entrypoints all exited 0:

```text
generate_video.py --job tests/video/fixtures/job_offline.yaml
generate_video.py --config examples/pink_pig_demo/config.yaml
generate_video.py --job examples/pink_pig_modbus_demo/job.yaml
```

FFmpeg full decode and independent ffprobe both passed:

| Artifact | Resolution | FPS | Video | Audio | Duration |
|---|---:|---:|---|---|---:|
| `dist/pink_pig_story_demo_offline.mp4` | 1080x1920 | 30 | H.264 | AAC | 12.5s |
| `dist/pink_pig_demo.mp4` | 1080x1920 | 30 | H.264 | AAC | 5.9s |
| `dist/pink_pig_modbus_demo.mp4` | 1080x1920 | 30 | H.264 | AAC | 27.8s |
| `dist/director/director_ec229e6efe2c340d/output.mp4` | 1080x1920 | 30 | H.264 | AAC | 38.4s |

Render reports matched independent ffprobe for the Modbus, offline story, and
fake-provider Director artifacts. Reports retain subtitle safe-region, asset
order, audio, Composition, and Pink Pig style evidence.

## 6. Independent reviews

- Lifecycle specialist: failure normalization, atomic writes, stale-report
  reset, factual consistency, sandbox boundary, and path redaction accepted.
- Legacy specialist: old execution modules deleted, controls preserved, and
  structured retirement responses verified.
- Lifecycle code-quality review: accepted after unknown-stage fallback,
  Windows-path redaction, accepted-report sanitization, and protected sandbox
  cleanup were added.
- Final independent reviewer: **APPROVED**.

## 7. Git and forbidden-surface audit

The index is empty; no commit, push, reset, clean, merge, or rebase was done.
The six pre-existing dirty-file SHA-256 values are unchanged:

```text
PROJECT_STATUS.yaml cd0dc97280ed86abac748dceaff73a45587a92656d4481e782b37aa33002785d
reports/P0_ACCEPTANCE_MATRIX_V2.yaml acccf9e9440776583857c67ba15094ef461f1b61dfe0ebd436fa68b4e3b6905e
scripts/analysis_request.py 68bdd12ebc45d92fff17ae01dec7f6c4efcd0cef3e89aeb68434ec9ebed9ea1d
scripts/analyzer_mcp.py bcf09db631eed87316c4d2b0664abc159470860b0d3e84c7e8c3460071e09d90
scripts/mcp_ingest_attachment.py 313f00b8f855faaf2ad22cd01a61d987670d0ff02ff4c9de3d57970039a7d52b
scripts/media_action_ticket.py 794b0ed4dea1fb18eb52371d1fcddc4724d8d781b141b09214545e5af19699e5
```

No new changes were made to OpenClaw, Feishu, Gateway, Binding, OAuth, Cron,
`PROJECT_STATUS.yaml`, Provider cache/config/Profile/model, or formal Gate
state. No `codex exec` was run.

The plan, report, and Change Request are explicitly trackable; each
`git check-ignore -q` check returned exit 1.

## 8. Obsidian

Updated UTF-8 pages:

- `04-落地状态与执行计划.md` appended 004 status and links.
- `05-AI-Director与素材智能.md` appended the remediation correction.
- Added `06-AI-Director-Phase2资格修复.md` with the three 003 findings,
  contracts, evidence, branch/HEAD, isolation boundary, and next task.

## 9. Remaining debt and next task

- Real Codex Provider remains blocked by its separate local prerequisite;
  Provider recovery was not attempted in 004.
- No VideoJob database, cancellation/recovery persistence, or long-running
  retry engine exists.
- No VideoClaw/multi-agent orchestration, Feishu entrypoint, Cron, or automatic
  operations exists.
- AI hot topics still require event-date/source contracts and human factual
  review; style quality checks are not pixel-level AI review.
- Three SVG-only poses may still fallback; no second production Provider.

The next task is only `005 Provider Recovery + Real AI Qualification`.

AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED
