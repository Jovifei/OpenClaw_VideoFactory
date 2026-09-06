# OpenClaw VideoFactory — History and Decision Log

Updated: 2026-09-05

This document summarizes the product/architecture decisions that matter to a new agent. It does not replace Git history or Change Requests; it explains which older ideas were superseded and why.

## 1. Initial Feishu/OpenClaw-first period

The project originally concentrated on:

- OpenClaw runtime and workspace;
- Feishu Channel/Binding/Gateway;
- lark-cli;
- safe media ingress;
- one-time analysis tickets;
- text/image/audio/video analyzers;
- GPU lock;
- event idempotency;
- P0 evidence and restart behavior.

This produced valuable future Phase 2 safety work, including real text/image/audio/video experiments.

**Decision superseded:** Feishu/P0 no longer blocks local video product development.

Reason: the user's primary value is a reliable local system that can create and reconstruct videos. Messaging automation is downstream.

## 2. Offline candidate video factory

The repository then proved local rendering:

- Python/FFmpeg pipeline;
- Remotion templates;
- local TTS and captions;
- video quality checks;
- local MP4 candidates.

This answered “can the machine render a video?” but not “can the product automatically produce a good, auditable video from a topic?”

**Lesson:** media feasibility is not product readiness.

## 3. Pink Pig productization

The project introduced:

- asset Registry;
- Storyboard/Timeline/Video Job Schemas;
- deterministic asset selection;
- multi-scene technical videos;
- Pink Pig style/quality rules.

A real output showed the mascot did not necessarily match Jovi's final personal IP design.

**Decision changed:** Pink Pig is no longer globally mandatory or allowed to use arbitrary repository-created replacements.

Current: opt-in + Jovi-owned original asset receipt.

## 4. Composition and subtitle safety

A visible defect showed FFmpeg default subtitle placement covering knowledge illustrations.

The project added:

- composition safe zones;
- subtitle line/font rules;
- collision checks;
- render-report geometry evidence.

**Lesson:** visual quality rules must be machine-checkable contracts, not verbal conventions.

## 5. AI Director phase

A provider-neutral Director layer was added:

- factual brief;
- structured script/draft;
- StoryboardAssembler;
- AssetSelector;
- controlled model fields;
- fake-provider E2E.

A real Codex CLI provider failed due to local model cache/base-instructions state.

**Decision changed:** real Provider health is no longer the only Phase 1 completion gate. The local factory can close on verified deterministic inputs while Provider recovery remains a separate enhancement.

**Lesson:** model/provider environment is an adapter boundary, not the renderer's foundation.

## 6. Product roadmap reset — local factory first

The project explicitly adopted:

```text
Phase 1 local video factory
→ Phase 2 Feishu automation
→ Phase 3 GPU/advanced media
→ Phase 4 advanced reference originality
→ Phase 5 editable delivery/publish assist
```

Historical P0-P5 labels remain only for evidence/tool compatibility.

## 7. Reference-video analysis

Branch `codex/phase1-reference-video-analysis-001` added:

- safe local MP4 ingest;
- rights/receipt;
- SHA-256;
- ffprobe;
- PySceneDetect;
- optional cached faster-whisper;
- abstract reference report;
- original brief;
- difference report;
- no raw reference media in review package;
- synthetic E2E and fresh-clone validation.

Original reference baseline reached historical `355 passed, 1 skipped` for its bounded suite at commit `56cb442f...`.

**Lesson:** a test total belongs to its exact commit and suite list; never carry the number forward as a current total.

## 8. Formal Phase 1 acceptance machinery

Added:

- Human Review Schema;
- Job Prereview;
- Acceptance Manifest;
- Lifecycle Evidence Schema;
- Boundary Audit;
- formal Phase 1 Gate.

**Decision:** Phase status is promoted only from exact evidence + Jovi review + Gate, not from agent self-report.

## 9. Flash/Watchdog and FreeRTOS fixtures

Flash/Watchdog gained:

- verified brief;
- deterministic technical cards;
- local render candidates;
- mascot-free correction;
- timing/Jianying experiments.

FreeRTOS gained a brief but still lacks the same current render/review/prereview qualification.

**Current interpretation:** Flash is mostly an evidence-selection/rebinding job; FreeRTOS is a remaining content/render implementation job.

## 10. Jianying experiment

The project validated a Jianying draft chain:

- visual-only video;
- VoiceOver;
- native subtitles;
- E-drive runtime;
- manual review/export.

An interim document made Jianying appear like the default finalizer for all Phase 1 videos.

**Decision corrected:** Jianying is optional editable/manual-review delivery. Core Phase 1 success remains a local auditable MP4 + quality/review package.

## 11. Aspect-ratio conflict resolved

Older Pink Pig/short-video work used 1080×1920.
Later reference/Jianying work used 1920×1080.

**Decision corrected:** aspect ratio belongs to the Job/brief profile.

- vertical knowledge/Douyin: 9:16;
- landscape/reference-edit: 16:9 when requested.

The current Phase 1 quality schema supports both orientations.

## 12. RC high-pass reference reconstruction

The reference track evolved into a higher-quality original reconstruction:

- dedicated Remotion technical visual;
- circuit geometry corrections;
- explicit engineering formulas/knowledge density;
- local narration subsegments;
- measured speech cue timestamps;
- knowledge-card emphasis tied to actual spoken phrases;
- post-render/critical/all-frame checks;
- optional Jianying review draft.

Latest implementation commit before the 2026-09-05 documentation refresh:

`edc0f2eaaf7ee826d694e94d3ecbe820ef294cad`

This proves strong technical feasibility but still needs exact-candidate human review and standard Phase 1 evidence binding.

## 13. Open-source strategy evolved

### VideoClaw

Adopt: stage artifacts, user intervention, recoverable workflow, runner/event/storage separation.

Reject: second backend/frontend/state DB and cloud provider dependency.

### Remotion

Moved from candidate template engine to actual deterministic visual engine.

### video-podcast-maker

Useful workflow reference, but current CC BY-NC 4.0 license means method inspiration/clean-room implementation rather than careless source copying into a future commercial path.

### ian-fenzhu-illustrations

Useful MIT style/persona reference; not proof of final user-owned mascot image assets.

### Jianying editor skill

MIT, optional current editor backend; not the core renderer.

## 14. Current decision summary

| Topic | Current decision |
|---|---|
| Product order | Local Phase 1 first, Feishu Phase 2 |
| Core renderer | Existing Remotion/deterministic visual + FFmpeg lineage |
| State | Existing SQLite store, no second DB |
| Topic video | Must become automatic and auditable |
| Reference video | Analyze abstractly, rebuild independently, human originality review |
| Aspect ratio | Job-scoped 9:16 or 16:9 |
| Pink Pig | Explicit opt-in + Jovi-owned original assets only |
| Jianying | Optional editable/manual-review branch |
| Codex real provider | Useful but not Phase 1's sole blocker |
| VideoClaw | Borrow workflow ideas, not its backend |
| Feishu | Deferred to Phase 2 |
| Cron | Phase 2 after non-scheduled proof |
| Douyin publish | Manual |
| Models/nodes | No automatic downloads |

## 15. Why Phase 1 is still not passed

Because the following are still missing as one coherent, current evidence set:

- FreeRTOS final fixture;
- current prereviews for all three fixed topics;
- fresh cancel/retry/restart/fallback evidence;
- exact latest reference candidate human review;
- final Acceptance Manifest;
- Boundary Audit;
- bounded regression at current HEAD;
- independent read-only audit;
- one-shot formal Gate.

That is the next agent's job. Do not restart architecture discovery unless current code disproves this document.
