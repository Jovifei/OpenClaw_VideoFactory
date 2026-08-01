# P0 Real Media Test Runbook 053

Status: **READY FOR USER-AUTHORIZED R3 ONLY; NOT EXECUTED.** Use Jovi's current
private `zhongshu` VideoFactory group. Do not start Project Gateway, change
Bindings, restart OpenClaw, or reuse a Ticket. Stop permanently at the first
deviation and retain only redacted evidence.

## R3 image

1. Confirm the local execution switch remains explicitly enabled and Project
   Gateway process count is zero.
2. Upload `E:\project\OpenClaw_VideoFactory\tests\fixtures\feishu_delivery\p0-image-test.png`.
3. Wait for exactly one new opaque Ticket from the bot.
4. Send only `/vf image <new-ticket>` as a fresh message; no explanation, quote,
   extra text, or copied historical Ticket.
5. Pass only if there is one quarantine receipt, one Ticket, one analysis request,
   one image Analyzer call using `xiaomimimo/mimo-v2.5`, and one reply, with no
   `mimo-v2.5-pro` fallback.

## R4 audio (only after R3 pass)

Upload `p0-audio-test.wav`, then send only `/vf audio <new-ticket>`. Pass only
with one receipt/Ticket/request/reply, local faster-whisper CUDA on RTX 4070
SUPER, GPU lock evidence, and no cloud fallback.

## R5 video (only after R4 pass)

Upload `p0-video-analysis-test.mp4`, then send only `/vf video <new-ticket>`.
Pass only with one receipt/Ticket/request/reply, `ffprobe`, bounded frame/audio
work, local transcription, GPU serialization, `mimo-v2.5` key-frame analysis,
and temporary-file cleanup.

Failure at R3, R4, or R5 is a stop condition. Do not continue to a later stage,
do not retry by changing settings, and do not run the P0 Gate from this runbook.
