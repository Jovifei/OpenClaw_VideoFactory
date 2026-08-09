# Pink Pig Asset Registry (`src/factory/assets/pink_pig/`)

## Overview

This directory is the **IP (Intellectual Property) single source of truth** for the
Pink Pig character ("小粉飞猪") used in video synthesis. Every renderable frame
must reference an ``asset_id`` from this registry — there is no "scan a random
directory" path.

## Dual Source Model (Important)

| Dimension | Source | Details |
|---|---|---|
| **Image assets** | **Local repository-owned** (`assets/pink_pig/pig01..05.png`) | 1080×1920 vertical PNGs, rasterized from `src/factory/assets/mascot/*.svg`. |
| **Style / IP spec** | **Upstream MIT repo** (`external/ian-fenzhu-illustrations`, commit `99ab94973b4d9b01d1f1ddb2737acf70c89b7c52`) | Prompt/style specification Skill repository. **Not an image library** — the entire repo contains only 1 JPG image. |

The upstream repository serves as the **normative source** for style DNA,
persona, composition rules, and IP constraints. The local structured style
contract is the single external file referenced by `registry.json`:
`src/factory/assets/pink_pig/style_profile.json`.

## Vertical Screen Exemption

This project outputs **1080×1920 vertical (9:16) videos**, which intentionally
exempts it from the upstream style-DNA requirement of "16:9 horizontal format".
The two contexts differ:
- Upstream = article/illustration accompaniment (horizontal)
- This project = short-form vertical video (vertical)

No `aspect_ratio` constraint is written into `style_profile`; instead it lives in
`storyboard.globals.aspect_ratio`.

## Pose Vocabulary (Closed Set)

All 8 poses align with `src/factory/assets/mascot/*.svg`:

| Pose | PNG Available | `render_ready` | Fallback |
|---|---|---|---|
| normal | ✅ pig01.png | true | — |
| thinking | ✅ pig02.png | true | — |
| question | ❌ SVG only | false → normal | |
| measure | ✅ pig04.png | true | — |
| repair | ✅ pig03.png | true | — |
| success | ✅ pig05.png | true | — |
| warning | ❌ SVG only | false → normal | |
| ending | ❌ SVG only | false → normal | |

Poses without PNGs have `render_ready: false` and a `fallback_asset_id` pointing to
a render-ready alternative. The compiler follows fallback chains automatically
(max 3 hops).

## Pose Verification Status

| Asset ID | Confidence | Evidence |
|---|---|---|
| pink_pig.normal.v1 | **verified** | Visual comparison: plain pig body matches `normal.svg` (no extra elements) |
| pink_pig.thinking.v1 | **verified** | Visual comparison: thought-bubble elements match `thinking.svg` |
| pink_pig.repair.v1 | **verified** | Visual comparison: pencil/wrench tool matches `repair.svg` |
| pink_pig.measure.v1 | **verified** | Visual comparison: ruler element matches `measure.svg` |
| pink_pig.success.v1 | **verified** | Visual comparison: green checkmark circle matches `success.svg` |
| pink_pig.question.v1 | **verified** | SVG-only; pose name from SVG `aria-label` and visual elements (question mark + dot) |
| pink_pig.warning.v1 | **verified** | SVG-only; pose name from SVG `aria-label` and visual elements (warning triangle) |
| pink_pig.ending.v1 | **verified** | SVG-only; pose name from SVG `aria-label` and visual elements (arrow/flag) |

> **Note**: The 3 SVG-only poses are marked `verified` for *pose identity* (the
> SVG source is authoritative), but `render_ready: false` because no rasterized
> PNG exists yet.

## How to Add a New Asset

1. Place the rasterized PNG at `assets/pink_pig/pigNN.png`
2. Run ffprobe / hashlib to get exact dimensions and SHA-256
3. Add an entry to `registry.json` under `assets[]`
4. Update `pose_index` if introducing a new pose (must be one of the 8)
5. Re-run `registry.verify(repo_root)` to confirm zero errors

## Files

| File | Purpose |
|---|---|
| `registry.json` | Registry data (assets, indices, style, IP constraints) |
| `registry.schema.json` | JSON Schema for validating `registry.json` |
| `style_profile.json` | External single source for brand, character, color, pose, forbidden, and quality rules |
| `loader.py` | Load + validate + resolve API |
| `README.md` | This file |
| `__init__.py` | Package marker |
