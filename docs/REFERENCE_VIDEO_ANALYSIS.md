# Local reference video analysis (Phase 1)

This adapter accepts an owned or licensed local `.mp4`, validates it with
`ffprobe`, copies it by SHA-256 into the ignored read-only reference store, and
keeps only abstract timing/style metadata in the review package. The renderer
remains the existing `run_local_brief()` → `run_job()` chain.

The analyzer uses PySceneDetect 0.7.1 `ContentDetector(threshold=27,
min_scene_len=0.8s)` through the dedicated Python 3.12 environment. A cached
faster-whisper 1.2.1 `small` snapshot may add transcript evidence; absent or
incomplete cache is recorded as `unavailable` without network access or model
download.

The generated `original_brief.json` carries only the user topic, a separately
verified factual brief, and coarse pace/structure/30-40-50 second guidance.
It never carries source paths, source frames/audio, a full transcript, asset
IDs, renderer settings, or provider prompts. `difference_report.json` checks
source/output hashes, Registry-only assets, local SAPI narration, source-audio
absence, and the 0.30 text-similarity policy. Logo, watermark, face,
perceptual-frame, and shot-order checks remain explicitly
`human_review_required`.

## CLI

```text
python scripts/factory.py phase1 create-reference \
  --video <local.mp4> --brief <topic-brief.json> --rights <rights.json>
python scripts/factory.py phase1 run --job-id <job-id>
python scripts/factory.py phase1 status --job-id <job-id>
```

`--brief` is a verified topic-mode brief. The command creates the analyzed
local-reference brief and a hash-bound idempotent job. The source MP4 remains
outside Git and outside the review package.
