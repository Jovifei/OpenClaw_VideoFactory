# PHASE1-LOCAL-VIDEO-MINIMUM-SLICE-001

## Goal

Deliver the first current-product Phase 1 slice without Provider, Feishu, OpenClaw,
Cron, model downloads, or publication:

```text
local_brief.json
  -> deterministic DirectorScript/Storyboard
  -> existing generate_video.py -> video_factory pipeline
  -> local Windows SAPI narration + subtitles
  -> final_master.mp4 + local human-review package
```

This is an implementation increment, not a Phase 1 pass.

## Tasks

1. Freeze the dirty worktree and create a narrow Change Request.
2. Add a closed local-brief contract and deterministic assembler; no asset path,
   render command, Provider prompt, or remote call may enter the brief.
3. Add Windows SAPI as an explicitly local TTS adapter while preserving the
   existing edge-tts and offline fallback behavior.
4. Add a job-scoped review-package builder and quality contract.
5. Add `generate_video.py --local-brief` by composing the existing storyboard,
   asset-selector, lifecycle, and `run_job()` implementation.
6. Add a Phase 1 local SQLite/CLI control surface that calls the same entrypoint;
   keep the retired Candidate render commands retired.
7. Run unit/regression tests, render the Modbus fixture, decode/ffprobe it, and
   record the exact result.

## Stop boundaries

- No Provider, Codex exec, cache recovery, Worker, Desktop interlock, Feishu,
  OpenClaw, Gateway, Binding, Cron, ComfyUI/model download, or publication.
- Do not modify `PROJECT_STATUS.yaml` phase status.
- Do not restore the deleted legacy Candidate render modules.
- Do not stage, commit, push, reset, or clean.

