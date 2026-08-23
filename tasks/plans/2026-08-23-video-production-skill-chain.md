# PHASE1-VIDEO-PRODUCTION-SKILL-CHAIN-003

## Objective

Make the local video workflow a single, auditable chain: verified topic or
reference analysis → original text → storyboard → Registry assets → local
audio/captions → deterministic visual render → one Jianying draft backend →
quality and manual review.

## Decisions

- Keep the existing renderer and job state as the sole deterministic render
  path.
- Use `jianying-editor-skill` through `jianying-draft-exporter` as the only
  editor backend for a job. CapCut Mate and JianYing MCP remain isolated
  candidates.
- Default to 1920×1080; allow 1080×1920 only by explicit brief.
- Send Jianying a visual-only MP4 so native Jianying subtitles and VoiceOver
  cannot duplicate burned-in layers.
- Keep Pink Pig opt-in and user-original-only.
- Keep automatic export, UI automation, remote providers, and publication
  disabled.

## Acceptance

- The route is documented in `skills/video-production-chain/SKILL.md`.
- All stage handoffs identify a single owner and a hard stop.
- Manifest and runbook select `jianying-editor-skill` as the default editor.
- No second renderer or second editor is introduced.
- Existing Phase 1 and video regression suites remain green.
