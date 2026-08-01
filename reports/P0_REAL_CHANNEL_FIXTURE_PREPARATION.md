# P0 Real-Channel Fixture Preparation (008)

Task: `P0-REAL-CHANNEL-QUALIFICATION-008`
Status: **fixtures prepared (audio + video) - offline, no cloud, no new dependencies**

## Existing fixtures (retained, unchanged)

| File | MIME | Size | SHA-256 |
| --- | --- | --- | --- |
| p0-file-test.txt | text/plain | 55 | c8a155b4d5eccafd2b36758b9fa67af186174dfe6e99e184b56231bd8382663d |
| p0-image-test.png | image/png | 17247 | 624223e0f8d14374d40301574b721c9debd46d4168ad4c44d06767e5f74a4214 |
| p0-video-test.mp4 | video/mp4 | 8858 | ea8ce1539fc1c7520b1bb1d275529749a5f4190e82516f12b3e9b98eba7632cc |
| p0-video-cover.png | image/png | 19582 | f1220bcdfac6737239951c49986efd639bdf349553cb85f455ee2ad31207d1b1 |

Note: `p0-video-test.mp4` is silent (no audio track). For video-analyzer audio-path validation, use `p0-video-analysis-test.mp4`.

## New fixtures (this round)

### p0-audio-test.wav
- MIME: audio/wav (pcm_s16le, 16000 Hz, mono)
- Size: 184674 bytes
- SHA-256: cc08486c989b5b6004f96ca6c5b102503852c76e709dee165d0e10408c287b6b
- Duration: 5.769625 s (within 3-6 s)
- Generation: PowerShell `System.Speech.Synthesis.SpeechSynthesizer` (Rate=3, Volume=100, 16kHz mono 16-bit PCM) - **offline .NET TTS, no cloud APIs, no new dependencies**
- Spoken text: "OpenClaw VideoFactory P zero audio test. The quick brown fox jumps over the lazy dog."
- Expected transcript: "OpenClaw VideoFactory P0 audio test. The quick brown fox jumps over the lazy dog."
- faster-whisper actual transcript (validated): "Openclaw Video Factory P0 Audio Test The quick brown fox jumps over the lazy dog" (semantically correct; TTS split "VideoFactory" into two words)

### p0-video-analysis-test.mp4
- MIME: video/mp4 (h264 video + aac audio, 16kHz mono)
- Size: 52037 bytes
- SHA-256: ca844094b316103d6084b59936685c1be8037174044cf4a2d4041db6acb689fc
- Duration: 5.0 s (within 4-8 s)
- Generation: `ffmpeg -f lavfi -i color=c=0x29465B:s=640x360:r=25:d=5 -i p0-audio-test.wav -vf drawtext=...text='P0 VIDEO ANALYSIS'... -c:v libx264 -c:a aac -shortest -y` - **existing ffmpeg 8.1.1 at C:\ffmpeg\bin, no downloaded assets**
- Expected frame features: dark blue (#29465B) background, white centered text "P0 VIDEO ANALYSIS" (fontsize 48, 640x360)
- Expected transcript (from embedded audio track): same as p0-audio-test.wav

## fixture_manifest.json

Updated to include all 6 files (4 retained + 2 new) with MIME, size, SHA-256, duration, format, generation_command, expected_transcript, and expected_frame_features.

## Git ignore

All binary fixtures (png, mp4, wav) remain git-ignored (the `.gitignore` excludes `tests/fixtures/feishu_delivery/*` binary types; verified by `Test-IngestInboundMedia.ps1` "keeps inbound originals and receipts Git-ignored" test).

## No sensitive data

All fixtures contain only test patterns / synthetic TTS sentences. No real business content, no user data, no secrets. `contains_sensitive_data: false` in the manifest.

## Validation

Both new fixtures were validated in the local analyzer runtime validation (`P0_LOCAL_ANALYZER_RUNTIME_VALIDATION`):
- p0-audio-test.wav: faster-whisper CUDA transcribed it correctly.
- p0-video-analysis-test.mp4: ffprobe probed it (h264+aac, 5.0s); 3 CPU frames extracted; audio extracted; faster-whisper transcribed the audio track.

## Evidence

- `tests/fixtures/feishu_delivery/p0-audio-test.wav` (sha cc08486c...)
- `tests/fixtures/feishu_delivery/p0-video-analysis-test.mp4` (sha ca844094...)
- `tests/fixtures/feishu_delivery/fixture_manifest.json` (updated)
- `reports/P0_LOCAL_ANALYZER_RUNTIME_VALIDATION.json/.md`
