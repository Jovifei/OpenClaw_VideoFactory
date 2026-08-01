# P0 Remaining Actions V5

Status: `conditional_not_passed`. 007 production implementation complete and smoke-verified.

1. **User live validation**: re-upload `p0-file-test.txt` to the VideoFactory Feishu group to confirm the full live attachment path (pre-ingest understanding=0 -> ingest_attachment -> receipt -> reply). This is the one smoke gap not closable without a real user upload.
2. **Audio/MP4 live event smoke**: after the TXT live validation, optionally validate a PNG/audio/MP4 upload end-to-end through the real Channel (analyzer dispatch to the 3 internal agents).
3. **ffmpeg PATH**: the analyzers use `C:\ffmpeg\bin\ffmpeg.exe` (not on system PATH). If analyzer agents fail to find ffmpeg, prepend `C:\ffmpeg\bin` to the process PATH or use the absolute path in the analyzer wrapper (no system-level env change).
4. **Local VLM (deferred)**: no local VLM is immediately callable (Ollama CLI not installed; Qwen2.5-VL weights not audited). Image/video vision uses `mimo-v2.5` (cloud). If cloud multimodal is unavailable, analyzers return `multimodal_model_unavailable` (no fallback to `mimo-v2.5-pro`). Approving a local VLM (Ollama + audited Qwen2.5-VL, or HF transformers) is a separate authorization.
5. **`<target-id>` change tracking**: if the VideoFactory Feishu group is migrated/recreated, the `tools.media.*.scope` keyPrefix must be updated (it silently falls back to default allow otherwise). Track as a P1 runbook item.
6. **P0 Gate**: run the final P0 Gate only when every required real-chain item (the user live upload above) is independently complete. Not done this round (prohibited).
7. **Gateway restart budget**: 3 restarts were used this round (1 planned + 2 smoke-driven fixes). Future config refinements should batch changes to minimize restarts.

No commit/tag/push, no PROJECT_STATUS update, no P1 work, no model download.
