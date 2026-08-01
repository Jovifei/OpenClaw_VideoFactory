---
name: remotion-layout-engine
description: "Render tested 9:16 technical short-video templates with deterministic layout, motion, captions, charts, code, diagrams, and audio."
version: 0.2.0
metadata:
  openclaw:
    requires:
      bins:
        - node
        - npm
        - ffmpeg
    emoji: "📐"
---

# Remotion layout engine

Before creating or modifying Remotion code, load the official Remotion best-practices skill.

## Production templates

- `protocol-frame`
- `code-explainer`
- `flow-diagram`
- `engineering-case`
- `comparison`
- `reference-style-adapter`

## Rules

- Input is structured JSON, never free-form prose embedded in components.
- 1080x1920, 30 FPS.
- Use a consistent typography scale and safe area.
- Text layout must be measured; no blind fixed widths for variable Chinese copy.
- All scenes have deterministic duration derived from audio timing.
- Each generated asset has a fallback.
- Final render runs ffprobe and frame sampling.
- H.264 delivery encode uses NVENC when available.
- Rendering must be reproducible from the job directory.

## Codex

Codex may add/refactor templates, but it must:

- work in a branch/worktree;
- read official Remotion rules;
- render a low-resolution preview;
- run visual/safe-area tests;
- return a change report.
