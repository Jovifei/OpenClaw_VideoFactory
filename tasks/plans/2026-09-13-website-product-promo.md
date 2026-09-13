# Website product promo — 2026-09-13

## Goal

Produce one local, portrait `website_product_promo` candidate for `逐星` from
fresh real-page screenshots, measured SAMI narration timing, and the existing
Remotion/FFmpeg path. Preserve all existing Phase 1 compositions and stop at
Jovi human review.

## Boundaries

- Read-only Star `origin/main` worktree; no Star business-code or deployment changes.
- New E-drive VideoFactory worktree only; preserve root `AGENTS.md` and all old candidates.
- No mock API/data, no iframe/live-site render dependency, no new backend/database,
  no new model/download, no music/mascot/QR requirement, no Feishu/Cron/publication.
- Runtime screenshots/audio/SQLite stay outside Git; commit only scoped source,
  tests and sanitized evidence.

## Steps

1. Verify package manifest, two repo HEADs, dependencies and baseline.
2. Confirm live selectors/viewport; capture six exact public routes and write a
   SHA-bound local asset review.
3. Add the package contract/component and an additive `WebsiteProductDemo`
   registration plus a profile-specific renderer route. Keep the TechnicalExplainer
   route and its contracts unchanged.
4. Add/execute integration tests first (RED), then implement the minimal route and
   report/metadata binding (GREEN).
5. Generate real SAMI timing from the supplied eight-beat script, build product
   props from reviewed captures, and run Remotion typecheck plus a one-frame/short
   preview.
6. Render the single portrait master, mux the measured audio and subtitles, run
   decode/safe-area/CTA/audio checks, inspect key frames, and write review evidence.
7. Run the bounded regression suite, commit/push the task branch, and report the
   unique candidate path/SHA and remaining human-review gate.

## Exit criteria

- six captures are `captured_unreviewed` and then `suitable_for_candidate` only
  after explicit local agent checks;
- product props are `production_candidate` with four upstream SHA bindings;
- final MP4 is 1080x1920, 30 FPS, H.264/AAC, fully decodable, subtitled, with a
  final CTA scene held for at least four seconds;
- quality/review package says `ready_for_jovi_human_review`, never `approved`.
