---
name: jianying-draft-exporter
description: "Optionally package a completed job into an editable Jianying draft using a reviewed local backend."
version: 0.2.0
metadata:
  openclaw:
    emoji: "✂️"
---

# Jianying draft exporter

This is optional. The reliable deliverable remains `final.mp4`.

## Backend selection

Preferred API backend: CapCut Mate on `127.0.0.1:30000`.

Alternative Windows backend: reviewed `jianying-editor-skill`.

Never enable both for the same job.

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
