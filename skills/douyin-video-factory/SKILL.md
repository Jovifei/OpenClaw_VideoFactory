---
name: douyin-video-factory
description: "Plan, select, produce, verify, and queue Chinese technical videos for manual Jianying review and Douyin publishing."
version: 0.1.0
metadata:
  openclaw:
    requires:
      bins:
        - python
        - ffmpeg
        - ffprobe
    emoji: "🎬"
---

# Douyin video factory

For the end-to-end route, load `video-production-chain` first. It defines the
single ownership path from verified text through the pinned Jianying backend.

Use this skill for daily topic selection and end-to-end video production.

## Workflow

1. Read workspace rules and configuration.
2. Run `python scripts/factory.py topics`.
3. Present the best candidates with rank, hook, outline, cover text, visual plan, risks, and score.
4. On user selection, run `python scripts/factory.py select --rank N`.
5. At selection deadline, run `python scripts/factory.py auto-select`.
6. Run the selected job with `python scripts/factory.py run --job-id ID`.
7. Prepare a visual-only Jianying input and create a new draft with
   `jianying-draft-exporter` when the brief requests Jianying editing.
8. Run the quality gate and assemble the review package.
9. Require manual Jianying listening, visual review, and export on E:.
10. Send the user the MP4, draft path, cover, caption, hashtags, script, and
    quality report.
11. Never publish to Douyin.

## Codex delegation

Use Codex only when:
- a renderer/template needs code changes;
- a deterministic script fails after normal retries;
- a multi-file implementation or deep code review is necessary.

OpenClaw retains job state and retries. Codex must work in a dedicated branch or worktree and return a patch/test result.

## Failure policy

- Maximum two retries per stage.
- AI video failure → static generated image.
- Image generation failure → deterministic Remotion diagram.
- Unknown or unverifiable factual claim → reject topic.
- Score below configured threshold → do not auto-produce.
