# PHASE1-AV-SYNC-TIMELINE-006

## Goal

Make the local Flash/watchdog reconstruction voice-first. One timing manifest
must drive Remotion scene boundaries, Jianying VoiceOver placement, and native
subtitle placement. Keep Jianying as the editable review backend and Remotion as
the only programmatic renderer.

## Work items

- [ ] Record the measured drift and inspect the pinned Jianying/Remotion/
  HyperFrames timing rules.
- [ ] Add an E-drive timing probe that creates the exact local SAMI segments,
  records audio hashes and microsecond boundaries, and never downloads a model.
- [ ] Make Remotion consume the manifest instead of five equal ten-second scenes.
- [ ] Make the Jianying draft builder consume the same audio files/timeline and
  fail closed on timing drift or a second subtitle authority.
- [ ] Assemble a new audio preview, run ffprobe/full decode and timing checks,
  targeted tests, and existing video regressions.
- [ ] Update reports, tasks/lessons.md, Obsidian project memory, commit only
  intended files, and push the feature branch.

## Review

The previous candidate's fixed visual scene duration was the root cause. This
change does not claim a formal Phase 1 pass; manual listening and Jianying
export remain human gates.
