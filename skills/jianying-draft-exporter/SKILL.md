---
name: jianying-draft-exporter
description: "Package a completed local candidate into an editable Jianying draft using the reviewed jianying-editor-skill backend."
version: 0.2.0
metadata:
  openclaw:
    emoji: "✂️"
---

# Jianying draft exporter

For Jovi video deliverables this is the selected editing backend. The deterministic MP4 is an auditable visual input, not the final edited delivery.

## Backend selection

Selected backend: reviewed `jianying-editor-skill` on Windows.

Do not enable CapCut Mate for the same job; this project keeps one Jianying backend per draft.

## Inputs

- final or per-scene video;
- narration WAV;
- BGM;
- captions;
- cover;
- asset manifest;
- style tokens.

## Output

- a new draft directory;
- import report;
- track map;
- manual-open instructions;
- compatibility warnings.

## Rules

- Generate a new draft; do not repeatedly mutate a draft already edited in Jianying.
- Do not invoke automatic export by default.
- Do not control mouse/keyboard on the user's active desktop.
- If using old-version automatic export, use a dedicated Windows account/session and explicit opt-in.
- A draft failure must never mark the whole video job failed.
