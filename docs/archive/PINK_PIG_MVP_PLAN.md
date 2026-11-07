# Pink Pig MVP Plan

## Run

```powershell
Set-Location E:\project\OpenClaw_VideoFactory
python generate_video.py --config examples/pink_pig_demo/config.yaml
```

Expected local outputs are `dist/pink_pig_demo.mp4`,
`dist/asset_manifest.json`, `dist/video_timeline.json` and `dist/subtitle.srt`.

## Acceptance

- five ordered PNG assets are discovered with actual dimensions;
- timeline contains fade, zoom and slide transitions;
- an SRT is generated and burned into the MP4;
- FFprobe confirms 1080×1920, 30 fps, H.264 video and AAC audio when enabled;
- empty directories, malformed images and missing configuration fail with
  stable error codes.

## Explicitly deferred

AI direction, automatic action choice, cloud/local TTS execution, quality
agents, OpenClaw/Feishu delivery, scheduling, automatic topic selection and
Douyin publication are outside this MVP.
