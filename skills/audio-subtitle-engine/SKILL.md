---
name: audio-subtitle-engine
description: "Generate or ingest narration, align it with CUDA transcription, create readable Chinese captions, and prepare audio mixes."
version: 0.2.0
metadata:
  openclaw:
    requires:
      bins:
        - ffmpeg
        - ffprobe
        - python
    emoji: "🎙️"
---

# Audio and subtitle engine

## Narration

- Start with a stable Chinese TTS backend.
- Split text at natural breath points.
- Maintain a pronunciation dictionary for MCU names, acronyms, protocols, and English terms.
- Save raw segments and final WAV.

## Alignment

Default: faster-whisper CUDA with word timestamps and VAD.

Use WhisperX when:

- reference-video transcription needs tighter alignment;
- there are multiple speakers;
- karaoke captions drift materially.

## Caption output

Produce:

- `captions.json` with word and phrase timing;
- `captions.srt`;
- optional ASS;
- line-break metadata for Remotion and Jianying.

Chinese rules:

- max two lines;
- avoid breaking technical tokens;
- highlight only one or two keywords at a time;
- keep text out of Douyin UI zones;
- captions must describe spoken content, not add unverifiable claims.

## Audio mix

- Normalize narration first.
- Duck BGM beneath speech.
- Reject clipping, silent audio, and music louder than speech.
