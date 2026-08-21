# PHASE1-REFERENCE-VIDEO-ANALYSIS-001

## Goal

Implement a conservative local MP4 reference path:

```text
local MP4 + rights record + verified local brief
  -> hash-bound private ingest
  -> ffprobe + PySceneDetect structure/pace report
  -> optional offline faster-whisper transcript
  -> original_brief
  -> existing Phase 1 run_local_brief/run_job pipeline
  -> difference report + local human review package
```

This is a Phase 1 increment. It does not promote `PROJECT_STATUS.yaml`, enable
Feishu/OpenClaw/Cron, call a remote provider, download models, or publish media.

## Execution gates

1. Audit and publish the existing dirty local baseline under
   `PHASE1-LOCAL-BASELINE-PUBLISH-001`.
2. Create `codex/phase1-reference-video-analysis-001` from the clean baseline.
3. Implement schemas, safe ingest, deterministic analysis, original brief,
   review evidence, and CLI integration.
4. Run targeted tests, local synthetic E2E, full regression, media checks, and
   remote fresh-clone smoke.
5. Push only the feature branch and record evidence; keep Obsidian read-only.

## Stop conditions

- Any untracked/unignored file cannot be attributed to an existing Change Request.
- Any reference source is not an MP4, changes while being copied, or fails the
  SHA-256/ffprobe/reparse gate.
- Any analyzer attempts network access, model download, OCR/VLM, or source-media
  reuse.
- Any regression, staged-diff review, fresh-clone smoke, or push fails.

## Review result

The only acceptable feature result is
`PHASE1_LOCAL_REFERENCE_REVIEW_PACKAGE_READY`; it is not the final Phase 1 gate.
