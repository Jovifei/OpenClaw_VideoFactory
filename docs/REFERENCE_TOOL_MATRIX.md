# Reference Video Tool Adoption Matrix

Updated: 2026-09-05

| Project / Tool | Current adoption | Role | Boundary |
| --- | --- | --- | --- |
| FFmpeg / ffprobe | Direct dependency | Container/media validation, extraction, decode, mux, evidence | Does not interpret creative meaning |
| PySceneDetect 0.7.1 | Direct offline dependency | Scene boundaries, scene duration, pace, shot density | Phase 1 coarse structure only |
| faster-whisper 1.2.1 | Optional offline adapter | Reference audio transcription when an approved local cache exists | No model auto-download; not required for self-generated TTS |
| Remotion | Direct visual engine | Rebuild original deterministic technical visuals from abstracted brief/timing | Never replays source footage |
| Local TTS / SAMI timing | Direct local evidence path | Measure narration timing and produce speech cues | New narration only; source audio is forbidden |
| VideoClaw | Method adoption only | Stage artifacts, editable intermediate assets, pipeline/event/storage separation | No backend/frontend/state DB imported |
| OpenMontage | Method adoption only | Approval/gate/backlot/self-check ideas | No AGPL code vendoring into current repo |
| Video Analyzer / Scene Scribe | Clean-room ideas only | Report field organization / analyzer decomposition | No dependency in Phase 1 |
| Auto-Editor | Deferred | Long-form silence/static pre-trim | Not needed for current short reference slice |
| WhisperX | Phase 3/4 candidate | Higher-precision alignment / diarization | Not a Phase 1 blocker |
| Perceptual similarity tooling | Phase 4 candidate | Assist frame/shot-sequence originality review | Human originality review remains final |
| ComfyUI/video generation providers | Deferred | Creative reconstruction B-roll | Not allowed to replace technical fact visuals in Phase 1 |

## Current Phase 1 reference capability

The branch now goes beyond the original synthetic reference test:

1. owned/licensed local MP4 ingest with SHA-256 and rights;
2. ffprobe validation;
3. PySceneDetect coarse structure;
4. optional local cached ASR;
5. abstract `reference_report` and `original_brief`;
6. new script/storyboard/assets;
7. Remotion deterministic reconstruction;
8. local narration with measured timing;
9. speech-cue-bound knowledge animation in the RC high-pass reconstruction;
10. new MP4 + `difference_report` + review evidence;
11. optional Jianying editable-draft branch for human review.

This is still **reference-guided original reconstruction**, not source-shot reuse.

## Phase boundary

### Phase 1 must prove

- safe local ingest;
- abstract report;
- original rendering path;
- no source audio/frames in delivered package;
- human originality review;
- reproducible evidence.

### Phase 4 may add later

- visual semantic models;
- OCR/face/watermark classifiers;
- perceptual-frame similarity;
- shot-sequence similarity;
- stronger copyright-assist heuristics;
- WhisperX if alignment requires it.

Do not delay Phase 1 solely because Phase 4 tools are absent.
