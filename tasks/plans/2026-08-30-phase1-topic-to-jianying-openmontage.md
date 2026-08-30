# PHASE1-TOPIC-TO-JIANYING-010

## Goal

One Jovi topic must travel without intermediate human approval through verified research, three MPT drafts, deterministic selection, a five-beat/5-9-scene plan, measured SAMI timing, the existing Remotion composer, scene still/contact-sheet review, all-frame QA, and a new E-drive Jianying draft. The only human gate is Jovi's final review.

## Evidence boundary

- Current baseline: `30 passed`; `356 passed`; Remotion `tsc --noEmit` passed.
- Current branch/worktree: `codex/phase1-topic-openmontage-010` in `E:/project/worktrees/OpenClaw_VideoFactory/phase1-topic-openmontage-010`.
- The implementation may end only at `PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW` until Jovi reviews the produced draft.

## Increments

1. AGPL/OpenMontage baseline: license, notices, fixed upstream hashes, minimal source, manifest, read-only checkpoint/event/Backlot projection.
2. Topic contracts: `create-subject`, stable ID, research brief, three drafts, deterministic scoring/rewrite, proposal and scene-plan bridge.
3. Timing/visuals: SAMI timing authority, generic technical-explainer Remotion composition, per-scene stills, contact sheet, delivery promise, slideshow and semantic review.
4. Editing/package: per-scene visual clips, pinned Jianying backend, one VoiceOver and one native subtitle track, audible preview, expanded review manifest.
5. Qualification: lifecycle negative cases, three fixtures, one real topic, full regressions, fresh clone, final review handoff, docs and Obsidian sync.

## Stop conditions

- Fewer than two reliable sources, no primary/official source, MPT score below 85 after one rewrite, path/control injection, timing drift greater than one frame, slideshow verdict `fail`, visual review failure after one revision, incomplete decode, or Jianying track mismatch.
- Never silently fall back from Remotion to the legacy FFmpeg card renderer.
- Never create approval evidence on Jovi's behalf.
