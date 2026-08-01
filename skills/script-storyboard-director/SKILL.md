---
name: script-storyboard-director
description: "Turn an approved topic or reference analysis into an original short-video script, beat sheet, storyboard, and render contract."
version: 0.2.0
metadata:
  openclaw:
    emoji: "🎞️"
---

# Script and storyboard director

Use the strongest ideas from video-podcast-maker and structured production systems, but output short-form contracts owned by this workspace.

## Required outputs

- `research.md`
- `sources.json`
- `script.json`
- `storyboard.json`
- `style_tokens.json`
- `director_score.json`

## Script rules

- 25–60 seconds.
- Core question appears in the first two seconds.
- One sentence should normally fit one breath.
- Every sentence must either advance the answer or improve retention.
- Numbers, proper nouns, protocols, APIs, and MCU-specific behavior require verification.
- No empty “今天我们来聊聊” introduction.
- Avoid generic CTA before the viewer receives value.

## Storyboard rules

For every beat specify:

- start/end or target duration;
- narration;
- on-screen text;
- visual type;
- asset source;
- motion;
- transition;
- sound cue;
- fallback visual.

## Visual type decision

Use deterministic visuals for:

- code;
- protocol frames;
- timing diagrams;
- circuits;
- register maps;
- flow charts;
- comparison tables.

Use ComfyUI for:

- abstract electronics atmosphere;
- cover backgrounds;
- non-factual illustration;
- short transition B-roll.

## Director score

Score hook, clarity, evidence, visual variety, pacing, originality, account fit, and production reliability. A weak score blocks asset generation.
