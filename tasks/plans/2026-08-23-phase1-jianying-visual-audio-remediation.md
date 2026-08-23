# PHASE1-JIANYING-VISUAL-AUDIO-REMEDIATION-002

## Goal

Correct the current Flash/watchdog local candidate so the default Phase 1 path
uses a theme-appropriate neutral technical palette, prefers 16:9, keeps all
generated runtime/draft outputs on E:, has one authoritative subtitle layer in
the Jianying draft, and records an audible local narration gate.

## Scope

- Keep the existing `run_local_brief()` -> `run_job()` -> review-package chain.
- Keep Pink Pig opt-in only; this candidate remains `mascot_mode=off`.
- Keep Jianying export/manual listening as the human gate; no UI automation or
  automatic publication.
- Preserve legacy portrait jobs and old C: drafts; create new E:-root output.

## Steps

- [ ] Add the Change Request and record the current evidence/root causes.
- [ ] Add explicit render canvas parameters and make Phase 1 local defaults
      1920x1080/30 with a neutral theme palette; retain legacy renderer
      defaults for existing portrait fixtures.
- [ ] Extend Phase 1 quality/review contracts to accept both legacy portrait
      and the new landscape local candidate, with a safe subtitle region.
- [ ] Add a deterministic Jianying visual-only render mode through the existing
      renderer so the imported video has no burned-in captions; keep the
      Jianying `Subtitles` track as the only caption layer.
- [ ] Enforce E:-drive output/report/draft roots in the Jianying adapter and
      add an audio-track audibility report (unmuted, non-empty VoiceOver).
- [ ] Re-run focused tests, full affected regressions, ffprobe/decode and a
      fresh landscape Flash candidate; preserve old C: drafts and prior output
      evidence.
- [ ] Update tasks/lessons, Obsidian project memory, and the final review
      evidence. Do not mark Phase 1 passed; leave the manual Jianying review
      gate explicit.

## Acceptance

- New local candidate is 1920x1080, 30 FPS, H.264/AAC, fully decodable.
- Background is neutral/theme-appropriate, not the fixed pink fallback.
- The Jianying visual input has no audio and no burned-in subtitle; the draft
  contains exactly one `Subtitles` track and one unmuted `VoiceOver` track.
- Draft/report/runtime outputs are under E:, and a C: `--drafts-root` is
  rejected fail-closed.
- Existing portrait tests and previous drafts remain valid and untouched.
