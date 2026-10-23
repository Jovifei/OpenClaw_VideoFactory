# Phase 1 topic-only closure — stage execution plan

Date: 2026-09-27. Base: `main` at `f1d94e980526ab7d0a06faadf9c78596b09db565`. This plan is the local execution copy of the `c2c_9e7a` plan from the bound ChatGPT Project, checked against current repository contracts. Estimated machine work: 4–8 working days, plus Jovi's review time. It is a stage plan, not evidence that the stage passed.

## Goal and authority

Produce one auditable local MP4 and review package for each required topic, obtain SHA-bound Jovi reviews, assemble a `topic_only_v1` acceptance manifest, complete independent audit, and run the formal Phase 1 Gate once. `PROJECT_STATUS.yaml` remains `in_progress` until a successful Gate and separate promotion. The current Gate requires Flash/watchdog, FreeRTOS, I2C, and one distinct live topic; `reference_jobs: []` is valid for this scope. A supplied reference job must satisfy the full rights, originality, and human-review contract.

Authoritative reading order: `START_HERE_CODEX.md`, `PROJECT_STATUS.yaml`, `docs/README.md`, `docs/CURRENT_ARCHITECTURE.md`, `docs/PRODUCT_PHASES.md`, current source/schema/test evidence, then older handoff/runbook/Obsidian history. The 2026-09-05 runbook is useful procedure but its pending I2C and lifecycle claims are stale. The 2026-09-06 open-source matrix supersedes its older OpenMontage and MoneyPrinterTurbo status. The 2026-09-26 website-promo voice/copy complaint belongs to a separate unmerged branch and is not Gate evidence.

## Work packages and gates

### WP0 — Current fact and evidence inventory

- Confirm local and remote HEAD, preserve dirty Owner files, inspect current acceptance schema and Gate source.
- Inventory each final candidate with control job ID, source evidence, final audible MP4 path and SHA-256, quality report, review package, SQLite state, human review, and prereview status. Mark absent evidence `PENDING`; never infer approval.
- Revalidate existing I2C corrected 9:16 candidate and four lifecycle evidence JSON files. Do not regenerate them unless their identity, schema, or hash fails.
- Output: `reports/phase1/stage_20260927/inventory.json` and a concise review note. Gate: no unresolved identity/hash conflict before media work.

### WP1 — Fresh bounded regression baseline

- Run `tests/phase1_acceptance`, `tests/phase1_local`, `tests/reference`, `tests/director`, `tests/video`, and `video_factory/tests` using one recorded interpreter and current commit. Run Remotion contract/typecheck where the package scripts expose them.
- Record each exact command, exit code, pass/fail/skip counts and failing region in `reports/phase1/stage_20260927/regression_baseline.json`. Do not add counts from historical runs or label unrelated root collection failures as Phase 1 PASS.
- Gate: repair a real bounded regression before dependent media qualification; preserve original failure output.

### WP2 — Three fixed topics

- I2C: select only `PHASE1-I2C-VISUAL-CORRECTION-014` final vertical candidate; verify audible preview SHA, artifact and SQLite binding, quality report, and current prereview contract. Jovi must watch and listen before structured review.
- Flash/watchdog: choose one current mascot-off final candidate. Rebind existing artifact/review evidence if complete; render anew only for a concrete media or contract defect. Jovi review is SHA-bound.
- FreeRTOS: inspect current artifacts before assuming absent work. Complete only missing deterministic technical visual, script/storyboard, narration/timing, render, quality, SQLite `PENDING_REVIEW`, and review-package steps. Jovi review is SHA-bound.
- Run `scripts/phase1_acceptance.py` for each only after approved human review, requiring `status=ready` and exact final MP4 identity. Gate: never create a placeholder approval.

### WP3 — One distinct live topic

- Find a qualifying non-fixture candidate or produce a fresh sourced topic through the current factory, with original technical visuals, narration/timing, final MP4, and review package.
- Its control job must differ from all three fixture jobs; mock approvals and unbound factual assertions are invalid. Jovi reviews the unique final SHA before prereview.

### WP4 — Reuse lifecycle evidence

- Validate `reports/phase1/lifecycle/{cancel,retry,restart_recovery,encoder_fallback}.json` against `phase1_lifecycle_evidence.schema.json`; compute hashes and ensure repository-relative manifest references.
- Remediate only a failing item; do not rerun the whole lifecycle set for a fresh timestamp.

### WP5 — Boundary audit and manifest

- Build a fresh boundary audit for no Feishu/OpenClaw daily runtime/Cron/automatic publication, ignored private runtime, no credentials/raw reference media in Git, no second backend, and no unapproved downloads.
- Build `topic_only_v1` manifest from selected Flash/watchdog, FreeRTOS, I2C, live topic, lifecycle evidence, audit, and regression summary. Set `reference_jobs: []` for this scope. Include repository-relative paths and SHA-256; do not insert Modbus as a substitute fixture or mix old reference candidates.

### WP6 — Independent read-only audit

- Independently check HEAD, candidate uniqueness, schema, hashes, control-job distinctness, human review binding, lifecycle identity, no stale horizontal I2C/Flash/reference mix, test accounting, private paths, and Phase 2 boundary.
- Any defect returns to its producer, then rebuilds manifest and repeats audit. Do not weaken the Gate.

### WP7 — Formal Gate, once

- Only after all reviews and WP6 PASS: run `scripts/phase1_gate.py` once on the final manifest. Exit 0 plus `PHASE1_READY.json` and matching source hashes are required.
- On failure preserve `PHASE1_FAILED.json`, stop, and open a scoped remediation task. Do not patch evidence in place and rerun the same formal Gate.

### WP8 — Promotion and stop

- After Gate PASS, separately update `PROJECT_STATUS.yaml`, `tasks/todo.md`, Change Request/evidence, tested commit SHA, and current Obsidian status. Then stop. Phase 2 needs its own authorization and gate.

## Open-source decision

Keep SQLite as sole state authority and Remotion/FFmpeg as the sole production renderer. Already integrated MoneyPrinterTurbo script drafting and OpenMontage adaptations remain within their recorded license boundaries. VideoClaw checkpoints, Outscal scene-level revision, Code2MP4 editable-source provenance, Babulus narration-first timing, and OpenReels cost/review ideas are method references only. No new package, model, node, second pipeline, or automatic publisher is needed to close Phase 1. Reconsider a technique only when a specific WP exposes a concrete defect and its license/integration cost has been checked.

## Separate backlog

The website-promo candidate in `codex/website-product-promo-revision-20260913` remains unmerged and `PENDING_REVIEW`. Jovi's 2026-09-26 correction says its voice and spoken copy were not actually remade. Audit that branch and produce a genuinely revised voice/copy candidate under a separate Change Request; do not put it in this Gate manifest. Keep that work separate unless Jovi explicitly reprioritizes it.
