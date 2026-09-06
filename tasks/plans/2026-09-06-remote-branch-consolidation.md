# Remote branch consolidation — 2026-09-06

Change Request: `reports/change_requests/GIT-REMOTE-BRANCH-CONSOLIDATION-011.json`.

## Goal

Consolidate the two non-ancestor Phase 1 branches into `main` through this isolated
integration branch, while preserving current Phase 1 boundaries. The requested
remote update happens only after merged-tree tests and a review of the staged
merge resolution succeed.

## Audited branch inventory

| Remote branch | Relation to `origin/main` | Decision |
| --- | --- | --- |
| `codex/ai-director-video-factory-phase2-001` | ancestor; 0 unique commits | no merge needed |
| `codex/p0-feishu-single-consumer-086` | ancestor; 0 unique commits | no merge needed |
| `codex/pink-pig-phase1-5-composition` | ancestor; 0 unique commits | no merge needed |
| `codex/product-optimization-093` | ancestor; 0 unique commits | no merge needed |
| `codex/phase1-topic-openmontage-010` | 30 unique commits; `main` is its ancestor | fast-forward into integration branch |
| `codex/phase1-reference-video-analysis-001` | 24 unique commits; diverged from the topic branch | non-fast-forward merge after review |

No branch deletion, force-push, reset, clean, rebase, phase promotion, runtime
configuration, provider invocation, media rendering, or publication is in scope.

## Execution plan

1. Preserve the user-owned dirty `main` worktree. Work only in
   `E:\project\worktrees\OpenClaw_VideoFactory\branch-consolidation-011`, created
   from `origin/main` at `3ba05c3`.
2. Merge `origin/codex/phase1-topic-openmontage-010` with fast-forward only.
   Abort and stop if this cannot fast-forward.
3. Merge `origin/codex/phase1-reference-video-analysis-001` without committing.
   The preflight predicts conflicts only in `PROJECT_STATUS.yaml`,
   `START_HERE_CODEX.md`, `docs/PRODUCT_PHASES.md`, `runbook/11_PHASE1_COMPLETION.md`,
   and `skills/video-production-chain/SKILL.md`.
4. Resolve only those five files by retaining both current Phase 1 topic-only
   qualification requirements and the newer local-factory architecture/status
   guidance. Do not claim a Phase 1 pass, replace the single renderer/state chain,
   or introduce Phase 2 behavior.
5. Inspect the merged diff, parse the affected YAML/JSON, and run:
   `python -m pytest tests/phase1_local/test_phase1_topic.py tests/phase1_local/test_local_script_content.py tests/video/test_phase1_topic_visual.py -q`.
   Stop on any failure; preserve the integration worktree and do not update `main`.
6. Commit only the merge result to `codex/branch-consolidation-011`. Merge it into
   local `main` only after the preceding checks pass. Push `main` to `origin` only
   after local-main verification succeeds.

## Repair amendment — authorized after merged-tree verification

The full suite exposed two independently reproducible compatibility gaps:

1. `1961efb` changes the Registry from `1.3.0` to `1.4.0`, but leaves
   `examples/pink_pig_story_demo/storyboard.json` at `1.3.0`; the compiler correctly
   rejects the mismatch.
2. `dist/story_demo/` and its paired MP4 are ignored generated evidence, so a clean
   integration worktree cannot run legacy media tests until the existing demo jobs
   regenerate them.

Jovi authorized one minimal repair increment: align that single fixture version,
run the existing main and offline demo jobs only to recreate ignored local evidence,
then rerun the same bounded suite. No new media workflow, provider, export,
publication, tracked `dist` file, or unrelated source edit is allowed.

### Repair evidence

- The original `04-short-isr-defer.png` Git blob was malformed (`ffprobe` read
  `0x0`). Its committed SVG source rendered correctly through local Chrome at
  `836x471`; the repaired PNG and its Registry SHA-256 are now bound together.
- Three additional FreeRTOS PNG entries had stale Registry hashes, and the old
  demo storyboard/tests still declared Registry `1.3.0` after the branch's
  `1.4.0` Registry upgrade. All are aligned to the committed bytes/version.
- The existing primary demo ran through local Windows SAPI only; the existing
  offline fixture used its BGM fallback. Their ignored output files remain local.
- Verification: focused Registry/storyboard `73 passed`; media/schema `88 passed`;
  merged Phase 1 local, acceptance, video and OpenMontage set `502 passed`.

## Rollback and stop conditions

- Pre-merge remote `main`: `3ba05c3`.
- Source branch tips are immutable inputs: `1d2607c` and `1961efb`.
- On an unexpected conflict, malformed structured file, failed test, unclean
  integration index, or push failure: stop before `main` changes; preserve the
  worktree and report the exact state. Never reset or force-push.
