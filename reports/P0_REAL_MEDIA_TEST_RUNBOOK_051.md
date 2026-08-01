# P0 Real Media Test Runbook 051

Status: **DO NOT EXECUTE YET.**  The current 051 qualification is blocked by
`raw_command_source_provenance_not_bound_to_channel_message`.  This runbook is
prepared only for use after that channel-bound provenance requirement is
separately resolved and re-qualified.

The user must be online.  Use the same existing Feishu group and uploader
account throughout; never copy a ticket to another group.  Perform exactly one
stage at a time and stop permanently at the first deviation—no retry, next
upload, Gateway action, config change, or P0 Gate.

1. R3 image: upload
   `tests/fixtures/feishu_delivery/p0-image-test.png`; after the bot returns a
   ticket, send exactly `/vf image <ticket>`.  Record sanitized proof of one
   message, one quarantine receipt, one ticket, one analysis, one reply, fixed
   `mimo-v2.5`, and no Pro fallback.
2. Only if R3 passes, R4 audio: upload
   `tests/fixtures/feishu_delivery/p0-audio-test.wav`; send exactly
   `/vf audio <ticket>`.  Record local CUDA, GPU-lock, and no-cloud-fallback
   proof without exposing paths, IDs, hashes, or tickets.
3. Only if R4 passes, R5 video: upload
   `tests/fixtures/feishu_delivery/p0-video-analysis-test.mp4`; send exactly
   `/vf video <ticket>`.  Record bounded frames, bounded audio extraction,
   local transcription, GPU serialization, and `mimo-v2.5` key-frame proof.

The first real R3 also determines whether the running Core process discovers
the updated MCP surface; static/offline evidence cannot establish that fact.
