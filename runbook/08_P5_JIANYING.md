# 08 — Phase 5 / Optional Jianying Editable Draft

Updated: 2026-09-05

## Position in the product

Jianying is an **optional editable-delivery and manual-review backend**. It is not the only renderer and is not a hard prerequisite for Phase 1 local MP4 qualification.

Core route:

```text
Storyboard/Timeline
→ Remotion/deterministic visual
→ FFmpeg
→ final local MP4 + quality/review package
```

Optional editing route:

```text
qualified visual output
→ visual-only MP4
→ jianying-editor-skill
→ new Jianying draft
→ Jovi manual listen/edit/export
```

A failed Jianying draft may block editable delivery, but it must not invalidate a qualified local MP4.

## Selected backend

Current reviewed backend: `luoluoluo22/jianying-editor-skill` (MIT), pinned by the current Change Request evidence.

Do not enable CapCut Mate or JianYing MCP in the same Job.

## Draft rules

- Create a new draft; never overwrite a user-edited draft.
- Store media/runtime/report/draft roots on E:.
- A C: entry, if required for the desktop application to see an E: draft, must be an explicit non-overwriting junction/visibility mechanism and must be recorded.
- Visual input contains **no audio and no burned-in subtitles**.
- Exactly one `VoiceOver` authority.
- Exactly one native `Subtitles` authority.
- VoiceOver must not be muted.
- Automatic export is disabled.
- No mouse/keyboard desktop automation unless a later task explicitly authorizes it.
- Jovi manually opens, listens, checks visual timing and exports.

## Aspect ratio

The draft follows the Job profile:

- 16:9 / 1920×1080 for the current landscape reference-edit path;
- 9:16 / 1080×1920 for vertical jobs that explicitly request it.

Do not force landscape onto all future Douyin jobs.

## Current evidence

The branch has already produced Flash/Watchdog and RC high-pass Jianying experiments with:

- visual-only media;
- local narration;
- native subtitle track;
- timing manifests;
- visible E-drive draft workflow;
- manual review gates.

These prove technical feasibility, not Phase 1 pass.

## Acceptance

A draft may be marked `draft_ready_for_manual_jianying_review` only when:

- project opens;
- video track exists;
- VoiceOver exists and is unmuted;
- subtitles exist once;
- timing evidence exists;
- paths are valid;
- automatic export is off;
- existing user drafts are untouched.

Final publication remains a separate Jovi action.
