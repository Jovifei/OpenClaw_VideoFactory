# Pink Pig AI Video Factory — MVP Design

## Scope

This is a local Windows rendering path only: still images in a directory are
ordered, inspected, placed on a timeline, captioned and encoded to a playable
H.264/AAC portrait MP4. It deliberately has no OpenClaw, Feishu, Gateway,
Cron, OAuth, Agent-graph or publication dependency.

## Pipeline

```text
assets/pink_pig/*.png|jpg
  -> asset_manifest.json
  -> video_timeline.json
  -> subtitle.srt
  -> FFmpeg xfade + subtitle burn-in + optional local audio
  -> dist/pink_pig_demo.mp4
```

`asset_loader.py` uses FFprobe for actual dimensions and natural filename
ordering. `timeline.py` emits one scene per still image. `transition.py` maps
the stable `fade`, `zoom` and `slide` names to FFmpeg's supported xfade
transitions. `renderer.py` fixes output at 1080×1920, 30 fps, H.264 and
`yuv420p`; `audio.py` validates an optional input audio stream and
`voice_generator.py` exposes, but does not require, edge-tts.

## Demo assets

The five demo PNGs are local rasterizations of the repository-owned mascot SVG
poses. No model, online material or new dependency is downloaded. The optional
short audio tone is locally synthesized solely to prove AAC-track handling; it
is not a final music asset.

## Extension boundary

Future director, visual-selection, TTS and quality components may produce the
same manifest/timeline/script/audio inputs. They are not implemented in this
MVP, and this renderer makes no external call on their behalf.
