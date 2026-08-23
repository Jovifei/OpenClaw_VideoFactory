# RC High-Pass Reference Reconstruction Implementation Plan

> **For agentic workers:** Execute this plan inline with review checkpoints. Do not promote PROJECT_STATUS or automate Jianying export.

**Goal:** Build and verify a 9:16 original RC high-pass reference-style candidate with theme-driven palette, bounded typography, voice-first timing, Jianying review draft, and mandatory post-render gates.

**Architecture:** A structured five-beat script drives a timing probe, a deterministic Remotion composition, a layout contract, and the existing Jianying draft adapter. HyperFrames rules are encoded as timing/layout metadata; Remotion owns picture rendering; Jianying owns editable voice/subtitle review. A post-render gate runs before draft creation.

**Tech Stack:** TypeScript/React, Remotion 4.0.500, FFmpeg/ffprobe, Python 3.12, pinned `jianying-editor-skill` SAMI, optional HeyGen voice adapter, pytest.

---

### Task 1: Freeze the scoped change and authored source contracts

**Files:**
- Create: `reports/change_requests/PHASE1-RC-HIGHPASS-9X16-RECONSTRUCTION-007.json`
- Create: `docs/superpowers/specs/2026-08-23-rc-highpass-reference-reconstruction-design.md`
- Create: `reports/phase1/douyin_7676032444876819739_rc_highpass_reconstruction_script.json`
- Create: `reports/phase1/douyin_7676032444876819739_rc_highpass_storyboard.json`

- [x] Record the source hash and public-reference-only rights mode.
- [x] Write five original beats covering hook, topology, cutoff/Bode, phase/time intuition, and summary.
- [x] Add factual references for `fc = 1/(2πRC)`, `|H(fc)| = -3 dB`, phase lead, and `τ = RC`.
- [x] Assert the brief contains no source path, source audio, frame path, full transcript, asset ID, or provider control.

### Task 2: Add bounded 9:16 Remotion composition

**Files:**
- Create: `remotion/src/ReferenceRcHighPassVisual.tsx`
- Modify: `remotion/src/Root.tsx`
- Create: `scripts/render_rc_highpass_remotion_visual.mjs`
- Test: `tests/video/test_rc_highpass_visual_contract.py`

- [x] Use 1080x1920, `SAFE.left=72`, `SAFE.right=72`, `SAFE.bottom=180`, and a theme token selected for technical content.
- [x] Implement five diagrams with deterministic SVG/DOM geometry; no source frame or audio imports.
- [x] Wrap all visible text in a bounded text primitive with max width, max height, natural wrapping, and explicit `data-layout-box` metadata.
- [x] Drive scene starts and ends from the timing manifest; keep the visual subtitle-free for Jianying's native subtitle authority.
- [x] Add a render report containing `layout_contract`, `burned_in_subtitles=false`, canvas, fps, and hashes.

### Task 3: Make long-form timing and optional HeyGen narration safe

**Files:**
- Modify: `scripts/phase1_jianying_timing.py`
- Modify: `scripts/phase1_jianying_timing_probe.py`
- Modify: `scripts/phase1_jianying_tts_draft.py`
- Create: `scripts/phase1_heygen_narration_probe.py`
- Test: `tests/video/test_timing_manifest.py`

- [x] Permit an explicit long-form visual duration up to 120 seconds while preserving the existing 25-second lower bound.
- [x] Generate exact SAMI timings with no fallback when the selected local adapter is used.
- [x] If HeyGen voice generation is explicitly attempted, store only the new narration asset/hash and mark provider failure as `unavailable`; never upload the source MP4.
- [x] Keep Jianying's selected backend and one VoiceOver track authoritative.

### Task 4: Add mandatory post-render inspection

**Files:**
- Create: `scripts/phase1_post_render_check.py`
- Create: `tests/video/test_phase1_post_render_check.py`
- Modify: `scripts/render_rc_highpass_remotion_visual.mjs`

- [x] Verify output path is on E:, canvas is 1080x1920, fps is 30, H.264 is present, and visual-only output has no audio/subtitle stream.
- [x] Verify every declared layout box is inside safe bounds and no text box exceeds its max height/line count.
- [x] Extract representative chapter frames and reject black/frozen samples.
- [x] Verify full decode, source-audio absence, and deterministic output hash.
- [x] Write a JSON/Markdown report and stop before Jianying on failure.

### Task 5: Integrate Jianying review draft and assembled preview

**Files:**
- Create: `scripts/assemble_rc_highpass_jianying_preview.py`
- Modify: `scripts/phase1_jianying_tts_draft.py`
- Test: `tests/video/test_jianying_chain.py`

- [x] Create a new E-drive draft with one visual track, one unmuted VoiceOver track, and one native subtitle track.
- [x] Verify manifest timing against visual windows within one 30 FPS frame.
- [x] Assemble a local AAC preview only for QA; do not call automatic Jianying export.
- [x] Record manual listening/export as the remaining human gate.

### Task 6: Verify, document, and publish evidence

**Files:**
- Modify: `tasks/todo.md`
- Modify: `tasks/lessons.md`
- Create: `reports/phase1/douyin_7676032444876819739_rc_highpass_quality_20260823.json`
- Create: `reports/phase1/douyin_7676032444876819739_rc_highpass_jianying_20260823.json`

- [x] Run focused timing/layout/video tests, Remotion typecheck, ffprobe, complete decode, and staged-diff audit.
- [x] Inspect representative rendered frames using the visual companion and record the Bode label correction.
- [x] Keep status at `PHASE1_LOCAL_REFERENCE_REVIEW_PACKAGE_READY`; do not mark formal Phase 1 passed.
- [ ] Commit the scoped change and push only the current feature branch after final staged-diff audit.
