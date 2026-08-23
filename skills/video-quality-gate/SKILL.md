---
name: video-quality-gate
description: "Validate vertical short-video files, audio, subtitles, safe areas, timing, and production readiness."
version: 0.1.0
metadata:
  openclaw:
    requires:
      bins:
        - python
        - ffmpeg
        - ffprobe
    emoji: "✅"
---

# Video quality gate

Before queueing any video:

1. Verify file decodes.
2. Verify the configured canvas (Phase 1 defaults to 1920x1080; explicit legacy
   1080x1920 remains valid), 30 FPS, an audible audio track, and configured duration.
3. Check first meaningful title appears within two seconds.
4. Detect black/frozen sections and excessive scene duration.
5. Check subtitle safe areas and line length from render metadata.
6. Check voice/music levels.
7. Verify script claims have source records.
8. Verify no reference watermark or original audio was reused.
9. Score:
   - 85+ queue;
   - 75–84 revise once;
   - below 75 stop and report.
10. Write a JSON and Markdown report.
