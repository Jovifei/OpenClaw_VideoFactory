# Pink Pig Current Policy

Updated: 2026-09-05

## Why this file exists

The repository contains several generations of Pink Pig experiments. Some old architecture documents correctly describe the implementation at that time but are no longer the production rule. This file is the current policy.

## Canonical distinction

### Style source

`https://github.com/Jovifei/ian-fenzhu-illustrations`

This repository is used as a **style/persona/composition reference**. It defines the character DNA and illustration philosophy, but it is not treated as the user's final production-ready character asset pack.

### Production asset source

When personal IP is enabled, production assets must come from a **Jovi-owned original asset pack** whose ownership/source is bound to a receipt or equivalent local evidence.

The following are not allowed to silently substitute for that original pack:

- repository-created Pink Pig PNG/SVG;
- AI-generated temporary mascot images;
- upstream sample JPG;
- style/prompt-only repository content;
- unrelated pig characters or high-saturation cartoon variants.

## Activation

Current default: `off`.

Enable only when the current video brief explicitly requests the personal IP.

If the brief requires Pink Pig and no verified original asset pack is available, fail closed and request the original asset path/receipt. If the video does not require the mascot, the main video pipeline may continue without a mascot.

## Why the policy changed

Earlier Phase 1 experiments proved the asset registry, mascot positioning, safe-area and quality-gate concepts, but the resulting local mascot art was not guaranteed to match the user's final adjusted character design. The project therefore separates:

1. style/persona rules;
2. technical mascot infrastructure;
3. user-owned production assets.

This prevents a technically valid render from shipping the wrong brand character.

## Usage rules once enabled

- Character performs a meaningful action: measure, repair, carry, connect, mark, inspect, explain.
- Do not place it as random decoration.
- Do not cover code, protocol frames, formulas, circuits, subtitles or key operations.
- Dense technical scenes should reduce mascot prominence.
- Avoid repetitive airplane/cloud/conveyor compositions.
- Preserve the low-saturation mist-pink, small snout, dot eyes, small wings, calm/reliable/cold-humor personality.

## Related files

- `config/mascot_usage.yaml` — machine-readable activation and asset policy;
- `runbook/03_SKILLS_AND_EXTERNAL_REPOS.md` — external repository handling;
- `src/factory/assets/pink_pig/` — historical/technical registry implementation; not proof of ownership of final personal-IP assets;
- `docs/PINK_PIG_PHASE1_ARCHITECTURE.md` — historical architecture snapshot, not the current asset-policy source of truth.
