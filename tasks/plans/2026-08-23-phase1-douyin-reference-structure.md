# PHASE1-DOUYIN-REFERENCE-STRUCTURE-005

## Goal

Analyze the supplied public Douyin reference and use only abstract, non-identifying
structure/style tokens to create an original 16:9 Flash/watchdog explainer through the
existing Remotion visual path and Jianying review draft path.

## Scope

- Source: `https://www.douyin.com/video/7676032444876819739`.
- Public reference is not treated as an owned/licensed asset. No source media enters
  the repository, render manifest, audio chain, or review-package artifacts.
- Transferable: broad chapter arc, continuous motion-graphics cadence, neutral canvas,
  card/diagram layout, typography hierarchy, and accent-color roles.
- Rewrite: topic, claims, script, labels, equations, diagrams, assets, and timing.
- Forbidden: source audio, full transcript, source frames, logo/watermark, creator
  identity, recognizable characters, exact shot order, or a near-copy of the original
  expression.
- Default output: 1920×1080, 30 FPS, H.264/AAC when a manually reviewed Jianying
  export is available. The deterministic visual intermediate may be video-only.
- Pink Pig is off unless Jovi explicitly requests it and provides the original asset
  receipt. HeyGen is documented as an optional future adapter, not called in this
  local Phase 1 change.

## Work items

1. Preserve existing uncommitted changes and create this change request before edits.
2. Capture source hash, ffprobe metadata, audio level/stream metadata, PySceneDetect
   scene boundaries, representative times, and a human-readable keyframe/style profile.
3. If a complete local faster-whisper `small` snapshot exists, run offline ASR only;
   otherwise record `unavailable` without network or model download.
4. Build a five-part original Flash/watchdog brief using the abstract structure and
   verify it contains no source paths, source text, asset IDs, or provider controls.
5. Render a 16:9 Remotion visual with one subtitle authority; prepare a Jianying draft
   with local/approved voice and native captions for manual listening/export.
6. Run media, originality, subtitle/audio, and Git staged-diff checks; update reports,
   tasks/lessons.md, and the Obsidian project note only after the checks are recorded.

## Stop conditions

- Any source-media or creator-specific content is copied into the candidate.
- A source path, original audio, frame, transcript, asset ID, provider field, or
  remote-generation request appears in the original brief or render manifests.
- The visual has burned-in captions and Jianying adds a second subtitle authority.
- The voice timeline exceeds the visual timeline, audio is silent/missing, or the
  output is written to C:.
- Any test/regression or staged-diff audit fails.

## Completion label

`PHASE1_LOCAL_REFERENCE_REVIEW_PACKAGE_READY` only; human review and any real
publication decision remain open.
