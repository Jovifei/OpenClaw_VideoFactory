# P0 Real Media Sequence R3-R5 050

Prerequisite: use the existing `zhongshu` group and existing Core Feishu
Binding.  Do not start the Project Gateway, add a consumer, restart a Gateway,
or alter OpenClaw configuration.

## R3 — image

1. Upload a new `p0-image-test.png` in the existing group.
2. Confirm the bot's safe-ingress reply includes one opaque ticket and exactly
   `/vf image <ticket>`; it must not include a path, hash, chat/sender ID, file
   key, or secret.
3. As the same uploader in the same group, send that exact command.
4. Confirm one local `mimo-v2.5` image analysis result and no text-only model
   fallback.

Only then record `R3_IMAGE_ANALYSIS_OK`.  If any step fails, stop; R4/R5 do not
start.

## R4 — audio

1. Upload `p0-audio-test.wav`; receive its ticket.
2. Send `/vf audio <ticket>` as the same uploader in the same group.
3. Confirm one local faster-whisper CUDA transcript with the GPU lock and no
   cloud/model-download fallback.

Only then record `R4_AUDIO_ANALYSIS_OK`.  On failure, stop; do not start R5.

## R5 — video

1. Upload `p0-video-analysis-test.mp4`; receive its ticket.
2. Send `/vf video <ticket>` as the same uploader in the same group.
3. Confirm ffprobe, bounded frame extraction, local audio transcription under
   the GPU lock, and `mimo-v2.5` keyframe analysis; the full video must not be
   uploaded to a model.

Only then record `R5_VIDEO_ANALYSIS_OK` and
`P0_REAL_MEDIA_SEQUENCE_COMPLETE`.

