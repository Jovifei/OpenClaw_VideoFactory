# PHASE1-JIANYING-AUDIO-REMOTION-REDO-004

Change Request: `reports/change_requests/PHASE1-JIANYING-AUDIO-REMOTION-REDO-004.json`.

## Scope

Redo the rejected Flash/watchdog candidate. Keep the existing five-beat text and
Registry-only Flash visuals, render a new 16:9 visual-only Remotion input, then
create a fresh E-drive Jianying draft with one selected SAMI voice and one native
subtitle track. The old `final_master.mp4` and all prior drafts remain immutable.

## Steps

- [x] Add a deterministic 1920x1080 Remotion composition with neutral technical palette.
- [x] Render visual-only MP4 and verify no audio or burned subtitles.
- [x] Make the Jianying draft helper accept explicit canvas dimensions and create a new landscape draft.
- [x] Generate a fresh five-segment SAMI voice draft with one subtitle authority.
- [x] Run typecheck, focused tests, ffprobe, full decode, and frame inspection.
- [x] Save sanitized evidence, update task lessons and Obsidian, and commit only scoped files.

## Review

- Remotion visual: 1920×1080, 30 FPS, 50 seconds, video-only, complete decode passed.
- Jianying draft: `DouyinStructure_FlashWatchdog_16x9_SAMI_20260823`, 5 SAMI segments,
  one unmuted VoiceOver, one native Subtitles track, automatic export disabled.
- Human gate remains open: Jovi must listen in Jianying and decide whether to export.

## Human gate

Jovi must open the new E-drive draft in Jianying, listen to the selected voice,
review the 16:9 visual and single subtitle track, and export manually if it is
acceptable. This work does not promote Phase 1 or publish automatically.
