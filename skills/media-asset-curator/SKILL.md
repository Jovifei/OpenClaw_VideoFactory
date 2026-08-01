---
name: media-asset-curator
description: "Select, generate, verify, license-track, and organize all visual and audio assets for a video job."
version: 0.2.0
metadata:
  openclaw:
    emoji: "🗂️"
---

# Media asset curator

## Source priority

1. User-owned project assets.
2. Deterministic diagrams generated from verified data.
3. Local licensed asset library.
4. Properly licensed stock media.
5. ComfyUI-generated original media.
6. Generic programmatic fallback.

## Manifest

Every asset must record:

- job ID;
- file path;
- scene ID;
- source type;
- source URL or generator workflow;
- license/right basis;
- hash;
- crop and transformation;
- factual or decorative classification.

## Rules

- Never use watermarked material.
- Never use random search-result images without rights metadata.
- Factual visuals must be verified; generated text inside AI images is not trusted.
- Keep visual consistency through `style_tokens.json`.
- Avoid one image per sentence. Prefer purposeful scene changes.
