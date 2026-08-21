# PHASE1-LOCAL-VIDEO-MINIMUM-SLICE-001

## Result

`PHASE1_LOCAL_MODBUS_REVIEW_PACKAGE_READY`

This result proves one current-product Phase 1 local topic slice. It does not
mark all of Phase 1 ready and does not authorize Phase 2, Provider recovery,
Feishu, Cron, or publication.

## Current phase boundary

- Current product phase: `PHASE_1_LOCAL_VIDEO_FACTORY`.
- Formal status remains `not_started`; this task did not edit
  `PROJECT_STATUS.yaml`.
- Historical 005V3 Provider diagnostics remain terminal at
  `PREFLIGHT_DIAGNOSTIC_BLOCKED:cache_snapshot:cache_unhealthy` and were not
  retried.
- The implemented path is entirely local:

```text
phase1_local_brief.json
  -> deterministic DirectorScript / Storyboard / Registry asset selection
  -> existing generate_video.py -> video_factory pipeline
  -> Windows SAPI narration + burned-in subtitles
  -> FFmpeg final_master.mp4
  -> quality report + human review package
```

## Implemented contracts and controls

- Closed local brief Schema with three declared input modes. The direct topic
  mode is executable; local-reference and authorized-public-research modes fail
  closed until their dedicated analyzers exist.
- Deterministic topic digest, script, five-scene storyboard, and registry-backed
  asset selection. The brief cannot provide asset IDs, paths, render controls,
  or Provider prompts.
- Local `windows-sapi` narration. Narration text is sent on stdin and is absent
  from the command line. A narration segment is required for every scene.
- Existing `run_job()` renderer only; no second video pipeline was created.
- Atomic Video Job lifecycle ending in `completed`, plus local SQLite/event
  control ending in `PENDING_REVIEW`.
- Human review package with relative paths and SHA-256 for MP4, cover, subtitle,
  quality report, checklist, and publish-information file.
- Local CLI controls: `doctor`, `init-db`, `create-topic`, `run`, `status`,
  `cancel`, and `retry`. A repeated completed `run` returned `idempotent=true`
  without rerendering.

## Real local media evidence

- Input: `examples/phase1_local_modbus/brief.json`
- Stable render job: `phase1_dee7aff68f9b03af`
- Local control job: `job-e8a5b31e9d835da1bc9110e0`
- Local control state: `PENDING_REVIEW`
- Video Job state: `completed`, revision 6
- Scene count: 5
- Distinct knowledge illustrations: master/slave, frame layout, serial
  parameters, troubleshooting, summary
- Narration: local Windows SAPI, mode `tts`, 5/5 segments
- Subtitle: 5 burned-in cues; region x=90, y=1120, width=900, height=460
- Pink Pig/style gate: pass
- Full decode: exit 0
- Media: 35.4 seconds, 1080x1920, 30 FPS, H.264 High, AAC mono 24 kHz
- Volume: mean -22.9 dB, max -1.4 dB

Artifact SHA-256:

| Artifact | SHA-256 |
|---|---|
| `final_master.mp4` | `d578bc3e8e837392c6b41dfa5756e8d43aecd646ac2134363ae9ca34bde08981` |
| `cover.png` | `09843eb4211ebf4e960d4ec4143219f617ef74da4e6c48623d27435bcc5d83ed` |
| `quality_report.json` | `0956597a071baaa7f255b61a5fc684564e9fc29e24c3830c5cdb975241c1f1e4` |
| `review_package.json` | `75dbf11764e6d7ecf0a7f1e6c41033563e033036aefda61c9eb1c986d06d6b8f` |

## Verification

Commands and results:

```text
python -m pytest tests/phase1_local -q
16 passed

python -m pytest tests/director -q
47 passed

python -m pytest tests/video -q
273 passed

python -m pytest video_factory/tests -q
5 passed

legacy fixed suite
56 passed, 1 skipped, 13 subtests passed

ffmpeg -v error -i final_master.mp4 -f null -
exit 0

ffprobe -v error -show_streams -show_format -of json final_master.mp4
exit 0; media values above
```

The Phase 1 quality report, review package, Video Job state, Storyboard, and
asset-selection report all passed their JSON Schemas. Every review-package
artifact hash was independently recomputed and matched.

## Corrected failures during implementation

1. The first local entrypoint attempt stopped before audio/render because the
   existing lifecycle Schema requires `timeline_ref` in `rendering`; the
   entrypoint now declares the expected `timeline.json` reference.
2. The initial SAPI adapter passed output arguments after `-Command`, which did
   not populate `$args` under Windows PowerShell. It now passes only output and
   voice metadata through task-specific child environment fields while keeping
   narration on stdin. The narration-required gate prevented BGM from being
   misrepresented as successful speech.

Neither failed attempt produced an MP4 or invoked a remote service.

## Git and forbidden-surface boundary

- Branch: `codex/ai-director-video-factory-phase2-001`
- HEAD: `76180a59ea662bdf168d88baaeb777d3e8eb59ef`
- Index: empty
- Existing dirty/untracked worktree was preserved.
- No commit, push, stage, reset, or clean was performed.
- No Provider, `codex exec`, Worker, Desktop interlock, cache/auth mutation,
  OpenClaw, Feishu, Gateway, Binding, Cron, ComfyUI/model download, or
  publication action was performed.

## Remaining Phase 1 work

- Implement read-only local-reference theme/structure analysis and prove an
  original reference-derived MP4 without reused audio, watermark, source
  footage, or near-copy sequencing.
- Add Flash/watchdog and FreeRTOS fixtures and their deterministic technical
  illustrations.
- Complete cancel/retry and optional CPU/NVENC fallback evidence across all
  required fixtures.
- Obtain Jovi's human review of this first package, then run the final Phase 1
  gate only after every required fixture is complete.

The next implementation task is another Phase 1 increment, not 005V4, 006,
Feishu, or Cron.
