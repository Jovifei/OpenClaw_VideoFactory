# OpenClaw VideoFactory — Deep Handoff 2026-09-05

## 0. Read this first

This handoff is for a new ChatGPT/Codex agent taking over the project after a long multi-agent history.

Repository:

`E:\project\OpenClaw_VideoFactory`

Remote:

`https://github.com/Jovifei/OpenClaw_VideoFactory`

Active branch:

`codex/phase1-reference-video-analysis-001`

Branch baseline before the 2026-09-05 documentation refresh:

`edc0f2eaaf7ee826d694e94d3ecbe820ef294cad`

The branch has moved forward with documentation commits after that SHA. The new agent must `git fetch` and use the actual remote HEAD; never reset back to `edc0f2e`.

Current product phase:

`PHASE_1_LOCAL_VIDEO_FACTORY`

Current status:

`in_progress`

Formal Phase 1 result:

**NOT PASSED YET.**

---

# 1. What this project is actually trying to become

## 1.1 Final product

OpenClaw VideoFactory is intended to become a Windows-native AI short-video factory for Jovi's content account.

Content positioning:

- primary: embedded systems / engineering knowledge;
- secondary: AI/tooling topics with engineering relevance;
- optional personal brand: Jovi's Pink Pig mascot when original assets are explicitly enabled.

The final user experience should be:

### Topic mode

Jovi says:

> 做一个讲 FreeRTOS 优先级反转的视频。

The system does the rest:

```text
Topic
→ factual research / verified facts
→ script
→ storyboard
→ asset selection
→ technical visuals
→ narration
→ subtitle/timing
→ Remotion/FFmpeg render
→ quality checks
→ local MP4 + review package
→ Jovi review
```

### Reference-video mode

Jovi gives an owned/licensed local video:

```text
Reference MP4 + rights
→ safe read-only ingest
→ SHA-256 / ffprobe / scene / pace / optional ASR
→ abstract reference report
→ original brief
→ new script/storyboard/visual system
→ new narration
→ new MP4
→ difference/originality evidence
→ Jovi human originality review
```

### Phase 2 later

Only after local Phase 1 is formally qualified:

```text
OpenClaw / Feishu
→ 08:30 topic candidates
→ Jovi selection
→ qualified 12:00 fallback when necessary
→ invoke already-qualified local factory
→ controlled review-package delivery
→ Jovi manually publishes to Douyin
```

The product must never automatically publish to Douyin unless a future task explicitly changes that rule.

---

# 2. Correct product phase model

The repository contains historical P0/P1/P2/P3/P4/P5 labels from an earlier Feishu-first roadmap. Those labels remain for evidence compatibility but are no longer the product execution order.

Correct order:

## Phase 1 — Local Video Factory — CURRENT

Must prove:

- topic → original local video;
- reference video → safe analysis → original local video;
- auditable job state;
- cancel/retry/restart/fallback;
- quality report;
- review package;
- Jovi human review;
- formal Phase 1 Gate.

No Feishu dependency.

## Phase 2 — Feishu Automation

Only after Phase 1 passed:

- safe inbound/outbound;
- topic cards;
- user selection;
- qualified fallback;
- idempotency;
- recovery;
- controlled delivery;
- production Cron only after non-scheduled proof.

## Phase 3 — GPU / advanced media

Optional controlled acceleration/enhancement:

- RTX 4070 SUPER queue;
- ComfyUI approved workflows;
- NVENC;
- WhisperX if needed;
- OOM/CPU fallback.

## Phase 4 — advanced reference-video originality analysis

- richer semantic visual analysis;
- perceptual similarity;
- shot-sequence similarity;
- watermark/face/copyright assist;
- human originality decision still final.

## Phase 5 — editable delivery / publishing assistance

- Jianying editable draft;
- titles/covers/copy;
- manual export/publish.

Some Phase 5 technology has already been experimentally proven early. That is reusable technical evidence, not permission to reorder product phases.

---

# 3. Why the project had so many detours

The project originally spent substantial time on OpenClaw/Feishu/P0 security, Gateway, Binding, OAuth, Direct Codex CLI, media ingress and evidence collection.

Those efforts were not wasted: they created useful future Phase 2 safety evidence.

But they became a product-management problem because the core user value was still missing: **a local system that can actually make a good video from a topic and analyze/recreate a reference video.**

The roadmap was therefore reset:

- local video product first;
- Feishu second;
- advanced GPU/visual later.

New agents must not reopen historical Feishu blockers during Phase 1.

---

# 4. Major implementation milestones already completed

## 4.1 Offline/legacy video baseline

Early repository work proved:

- local image/audio/video composition;
- FFmpeg output;
- Remotion templates;
- TTS/caption basics;
- 25–60 second target;
- local quality checks.

This proved media feasibility but was not yet a product.

## 4.2 Pink Pig productization

Added:

- Registry;
- Storyboard Schema;
- Timeline Schema;
- Video Job Schema;
- asset selection;
- multi-scene demo;
- Pink Pig style/quality gates;
- composition/subtitle safe areas.

Important lesson: the upstream `Jovifei/ian-fenzhu-illustrations` repository is primarily style/persona/composition guidance, not a complete final user-owned image library.

## 4.3 Composition / subtitle safety

A real rendering defect showed subtitles overlapping technical imagery.

The project added:

- Composition Contract;
- content/subtitle safe areas;
- bounded font/line rules;
- overlap detection;
- render-report geometry evidence.

This moved layout quality from subjective convention into an enforceable contract.

## 4.4 AI Director / structured planning

Added:

- provider-neutral Director interface;
- Director Script / Draft / factual brief Schemas;
- StoryboardAssembler;
- AssetSelector;
- controlled model output: model cannot choose arbitrary asset path/render settings;
- topic-only pipeline tests;
- Fake Provider E2E.

A real Codex CLI Provider attempt failed because a local models cache lacked `base_instructions`.

Lesson: provider environment failures must not contaminate the renderer and must not become the only Phase 1 blocker. The deterministic local factory can be qualified without resolving this historical cache issue.

## 4.5 Phase 1 local product reset

The repository was reoriented around:

- local topic brief;
- local state;
- review package;
- no Feishu dependency.

`src/factory/phase1_local.py` and `src/factory/phase1_cli.py` became the local product control layer.

## 4.6 SQLite lifecycle

`src/factory/db.py` already implements the local transactional state store.

Tables include:

- `jobs`;
- `job_events`;
- `artifacts`;
- `topic_history`;
- `source_records`;
- `inbound_messages` (historical/future use);
- `deliveries` (dry-run/historical/future use);
- `stage_attempts`;
- `locks`.

State path:

```text
NEW
→ RESEARCHING
→ SCRIPTING
→ VOICE
→ CAPTIONS
→ ASSETS
→ RENDERING
→ QUALITY_CHECK
→ PENDING_REVIEW
```

Terminal exception states:

- FAILED;
- CANCELLED.

Do not create another DB.

## 4.7 Modbus topic baseline

Modbus was the first end-to-end engineering fixture.

It proved:

- factual brief;
- five-scene structured video;
- technical illustrations;
- narration;
- burned subtitles;
- local MP4;
- quality/review artifacts.

The original Pink Pig/Modbus work is useful baseline evidence, but final Gate should rebind it to the current schema/prereview contract instead of regenerating all historical demos.

## 4.8 Safe reference-video analysis

On branch `codex/phase1-reference-video-analysis-001`, the project added:

- local MP4 validation;
- rights schema;
- receipt;
- read-only/private storage;
- SHA-256;
- ffprobe;
- PySceneDetect;
- optional local faster-whisper ASR;
- abstract `reference_report`;
- `original_brief`;
- `difference_report`;
- source/path leakage protection;
- synthetic reference E2E;
- fresh-clone evidence at the original reference baseline.

The baseline commit `56cb442f...` recorded `355 passed, 1 skipped` across the bounded core suites at that point.

Do not treat this old count as the current universal test count; later work added tests and some unrelated root suites remain environment-dependent.

## 4.9 Formal Phase 1 acceptance/gate infrastructure

Added after the reference baseline:

- `phase1_human_review.schema.json`;
- `phase1_job_prereview.schema.json`;
- `phase1_acceptance_manifest.schema.json`;
- `phase1_lifecycle_evidence.schema.json`;
- `phase1_boundary_audit.schema.json`;
- `phase1_gate_report.schema.json`;
- `src/factory/phase1_acceptance.py`;
- `src/factory/phase1_gate.py`;
- CLI wrappers;
- acceptance/gate tests.

This is critical: the project now knows how to prove a Phase 1 result. The missing work is evidence closure, not inventing another acceptance mechanism.

## 4.10 Flash / Watchdog

Later branch work added:

- `examples/phase1_local_flash_watchdog/brief.json`;
- deterministic Flash/watchdog technical cards;
- mascot and mascot-free variants during debugging;
- a corrected mascot-free production candidate after the project discovered that repository-created Pink Pig art should not substitute for Jovi's final original IP;
- local MP4 evidence;
- local narration/subtitle timing;
- Jianying draft experiments;
- regression evidence.

The current task is to pick one final Flash candidate and bind it to current Review/Prereview evidence. Do not keep promoting multiple historical versions.

## 4.11 FreeRTOS

Added:

- `examples/phase1_local_freertos/brief.json`.

Still missing the full render/review/prereview qualification at the same level as Modbus/Flash.

This is one of the clearest Phase 1 implementation gaps.

## 4.12 Production Skill chain

Added `skills/video-production-chain/SKILL.md` to define one explicit handoff chain.

The Skill has now been corrected so the mandatory Phase 1 result is:

`local MP4 + quality report + review package`

Jianying is optional editable delivery, not the only success path.

## 4.13 Reference reconstruction / RC high-pass

The branch then evolved reference analysis into a practical reconstruction workflow.

Recent work includes:

- 9:16 RC high-pass visual;
- corrected topology/geometry;
- visible equations and engineering facts;
- timing manifest;
- local narration;
- speech subsegments;
- measured semantic cue timestamps;
- Remotion knowledge-card animation bound to measured speech cue starts;
- critical-frame checks;
- sequential/all-frame quality checks;
- optional Jianying draft/visible-junction path.

Latest pre-document-refresh implementation commit:

`edc0f2eaaf7ee826d694e94d3ecbe820ef294cad`

Message:

`fix(reference): bind knowledge cards to measured speech cues`

This is strong evidence that the product can analyze/reference a video structure and rebuild an original technical explanation. It is still awaiting final human review and standard Phase 1 evidence binding.

---

# 5. Current architecture by path

## Control / state

- `src/factory/db.py`
- `src/factory/state.py`
- `src/factory/phase1_cli.py`
- `scripts/factory.py`

## Topic/local planning

- `src/factory/phase1_local.py`
- `src/factory/director/`

## Reference analysis

- `src/factory/reference_video.py`
- `scripts/reference_scene_detect.py`
- `scripts/reference_transcribe.py`
- `docs/REFERENCE_VIDEO_ANALYSIS.md`

## Video contracts

- `schemas/video/`

Important current schemas include:

- Storyboard;
- Timeline;
- Video Job;
- Video Job State;
- Composition;
- Director contracts;
- Phase 1 local brief;
- Quality Report;
- Review Package;
- Reference evidence;
- Human Review;
- Job Prereview;
- Acceptance Manifest;
- Lifecycle Evidence;
- Boundary Audit;
- Gate Report.

## Video pipeline

- `video_factory/pipeline/`
- `generate_video.py`

Key responsibilities:

- Storyboard compilation;
- Registry/asset loading;
- audio planning;
- subtitle layout;
- composition;
- render command;
- render report;
- review package;
- validation/failure contracts.

## Deterministic visual layer

- `remotion/`
- `assets/*_illustrations/`

## Optional Jianying branch

- `scripts/phase1_jianying_*`
- `scripts/prepare_jianying_visual.py`
- `scripts/assemble_jianying_voice_preview.py`
- `skills/jianying-draft-exporter/`
- external pinned `luoluoluo22/jianying-editor-skill`

## Quality

- `video_factory/pipeline/review_package.py`
- `scripts/phase1_post_render_check.py`
- `skills/video-quality-gate/`
- `src/factory/phase1_acceptance.py`
- `src/factory/phase1_gate.py`

---

# 6. Current render/profile policy

Do not reintroduce the old conflict “the project is always 1080×1920” vs “the project is always 1920×1080”.

Current rule:

**Aspect ratio belongs to the Job/brief.**

Supported current profiles:

- 9:16, 1080×1920 — vertical/Douyin knowledge video;
- 16:9, 1920×1080 — landscape/reference-edit/Jianying jobs when explicitly requested.

Both remain 30 FPS by default and must produce valid H.264/AAC output where audio is required.

Current `phase1_quality_report` schema already allows both 1080×1920 and 1920×1080 and allows `pink_pig_status` to be `pass` or `off`.

Therefore do not “fix” the schema back to one orientation.

---

# 7. Current Pink Pig policy

This has changed materially over project history.

## Early assumption

Repository-created Pink Pig PNG/SVG plus style rules were treated as enough to guarantee IP consistency.

## Problem found

The rendered character did not necessarily match Jovi's final adjusted personal mascot design.

## Current policy

- `Jovifei/ian-fenzhu-illustrations` is a style/persona/composition source;
- it is MIT, but it is not automatically the final original production asset pack;
- personal IP is default off;
- Jovi must explicitly opt in for the current brief;
- production mascot requires a Jovi-owned original asset pack plus receipt/evidence;
- repository-created mascot art, AI temporary art and upstream sample images cannot silently substitute;
- mascot-off technical videos remain valid;
- mascot-required brief without verified assets fails closed.

Read:

- `docs/PINK_PIG_CURRENT_POLICY.md`
- `config/mascot_usage.yaml`

Do not use the historical long `docs/PINK_PIG_PHASE1_ARCHITECTURE.md` as the current asset-policy source.

---

# 8. Current Jianying policy

Jianying work is useful and should not be thrown away.

What is already proven:

- visual-only render;
- native subtitle track;
- VoiceOver track;
- E-drive runtime;
- manual listening/export workflow;
- timing manifests.

But current product rule is:

```text
Mandatory Phase 1:
local MP4 + quality/review package

Optional:
Jianying editable draft + Jovi manual edit/export
```

Do not make “Jianying draft exported” a mandatory condition for local factory success.

---

# 9. Open-source/community projects and what we borrowed

## 9.1 HITsz-TMG/VideoClaw — MIT

Current project positioning: an AI director system from idea through script/character/scene/storyboard/reference-image/video-generation/final-editing stages, with intermediate assets that can be viewed, confirmed and modified.

What we borrow:

- stage artifacts;
- explicit stage handoffs;
- user intervention points;
- recoverable project/job thinking;
- separation between runner/events/storage responsibilities;
- final edit is downstream of reviewable intermediate assets.

What we do not borrow:

- its second backend/frontend;
- its state/project DB;
- cloud video Provider dependency;
- creative short-drama assumptions;
- replacement of our renderer/contracts.

Reason: our project already has SQLite + Schemas + technical-video renderer. Full adoption would create double ownership.

## 9.2 Remotion / remotion-dev/skills

What we use:

- React programmatic video;
- deterministic composition;
- frame-based timing;
- technical animation;
- layout contracts;
- speech-cue-driven visual emphasis;
- Agent best-practice skills.

Important process lesson: Remotion's own Skills evolve. Read current upstream Skill before changing a Composition.

## 9.3 FFmpeg / ffprobe

Direct media backbone for encoding, muxing, probing, full decode and evidence.

## 9.4 PySceneDetect

Direct Phase 1 reference-scene detector for coarse scene/pace abstraction.

## 9.5 faster-whisper

Optional reference ASR only.

Do not run ASR on every self-generated narration when script/TTS timing already exists.

## 9.6 Agents365-ai/video-podcast-maker — CC BY-NC 4.0

Borrowed ideas:

- research → script;
- TTS/timing;
- Remotion components;
- Skill directory organization;
- validation.

License lesson: current NonCommercial license means do not copy code/templates into a future commercial path without a new legal/license decision. Clean-room reimplementation of ideas is safer.

## 9.7 Jovifei/ian-fenzhu-illustrations — MIT

Borrowed:

- character DNA;
- persona;
- composition philosophy;
- usage rules.

Not treated as final user-owned mascot asset evidence.

## 9.8 luoluoluo22/jianying-editor-skill — MIT

Current optional editable-draft backend.

Use one editor backend per Job; automatic export remains off.

## 9.9 OpenMontage

Borrowed ideas only:

- approval gates;
- reference-analysis workflow;
- backlot/visualization;
- self-review.

Historical license review recorded AGPL concerns; do not vendor source into this project without a new license review.

## 9.10 ComfyUI MCP / WhisperX / Auto-Editor / Real-ESRGAN

Deferred candidates, not current Phase 1 blockers.

## 9.11 n8n / LangGraph / Temporal

Intentionally not introduced.

The project already has job orchestration primitives; a second orchestration layer would increase state ambiguity.

---

# 10. Key engineering lessons from this project

## Lesson 1 — A passing demo is not a passing phase

Multiple times the project generated a good MP4, then mistakenly approached “ready”. The fix was to separate:

- implementation result;
- test result;
- human review;
- phase gate.

Never collapse these again.

## Lesson 2 — Evidence must bind to the exact artifact

Human review, Quality Report and SQLite Artifact must bind the final MP4 SHA-256. Historical version mixing is unacceptable.

## Lesson 3 — Do not use one global layout assumption

Vertical and landscape tasks both exist. The Job's render profile is authoritative.

## Lesson 4 — Audio drives time

Fixed scene duration created clipping and visual drift. Actual TTS timing must feed scene/timeline timing. Latest RC work improved this further by binding visual events to measured speech cues.

## Lesson 5 — Technical visuals should be deterministic

Protocol frames, registers, circuits, formulas, code and timing diagrams should not be generated with uncontrolled text-to-image models.

## Lesson 6 — Personal IP needs asset provenance, not just a prompt

Style guidance is not a substitute for Jovi's real character assets.

## Lesson 7 — External Provider failure must not own the product

A broken Codex local model cache blocked real Director qualification before. Provider-neutral contracts prevented the renderer from becoming dependent on that failure.

## Lesson 8 — Keep Feishu outside Phase 1

A lot of engineering time was lost because messaging/runtime evidence was treated as if it were prerequisite to making a local video. It is not.

## Lesson 9 — Optional editors must remain optional

Jianying is useful for editable delivery and human review, but a local video factory must already produce a valid video before an editor is opened.

## Lesson 10 — Borrow open-source architecture selectively

VideoClaw is valuable because of stage artifacts and interaction model. Copying its entire backend would be worse than using those ideas inside the existing architecture.

---

# 11. Current evidence caveats

Do not repeat old test totals as if they describe current HEAD.

Historical examples:

- reference baseline once passed `355 passed, 1 skipped`;
- later targeted Phase 1/Director/video/video_factory runs reported other counts such as `360 passed, 1 skipped`;
- a later combined bounded regression reported `322 passed, 1 skipped` for a different scope;
- broader `tests/` runs have historically been affected by unrelated vendor research dependencies or historical Feishu/P0 environment issues.

Therefore the next agent must establish a new explicit bounded suite list and save exact commands/results for the final Gate.

Never write a fake total by adding counts from different runs.

---

# 12. What is currently blocking Phase 1 completion

## Blocker A — FreeRTOS final fixture

The brief exists, but the full local render/review/prereview chain is not yet at the same level as Modbus/Flash.

## Blocker B — Three fixed topics need unified current evidence

Modbus and Flash have substantial historical evidence, but the final Gate should point to one final candidate/prereview for each.

## Blocker C — lifecycle evidence

Need fresh machine JSON for:

- cancel;
- failed retry;
- restart recovery;
- encoder fallback.

## Blocker D — reference human review

The latest RC high-pass candidate is technically advanced but still needs Jovi to actually watch/listen and approve visual/audio/originality.

## Blocker E — exact reference fixture contract

If final Acceptance Manifest requires a `local_reference` fixture, public/reference experiments cannot silently substitute. Use a Jovi-authorized local MP4 + rights evidence.

## Blocker F — final manifest/audit/gate

Need:

- prereviews;
- boundary audit;
- bounded regression summary;
- acceptance manifest;
- independent read-only review;
- one-shot formal Gate.

These are the real remaining blockers.

---

# 13. What is NOT a current blocker

- Feishu runtime credentials;
- Gateway/Binding/OAuth;
- Cron;
- historical P0 single-consumer evidence;
- Codex provider cache/base_instructions recovery;
- ComfyUI new models;
- WhisperX;
- automatic Jianying export;
- advanced perceptual copyright models;
- automatic Douyin publishing.

Do not spend Phase 1 effort on these.

---

# 14. Next agent execution plan

## Wave 0 — sync and audit

1. `git fetch`.
2. Confirm branch and remote HEAD.
3. Preserve user dirty files; no reset/clean/stash/rebase.
4. Read current canonical docs.
5. Run `git diff --check`.
6. Record a new current bounded test baseline.

## Wave 1 — finish fixed topic evidence

1. Rebind Modbus final candidate to current Review/Prereview contract.
2. Select one Flash final candidate; discard stale candidates only logically, not by deleting history.
3. Build and render FreeRTOS through the same current path.
4. Obtain Jovi human review one video at a time.

Expected stop states:

- `PHASE1_WAITING_HUMAN_REVIEW:modbus`
- `PHASE1_WAITING_HUMAN_REVIEW:flash_watchdog`
- `PHASE1_WAITING_HUMAN_REVIEW:freertos`

## Wave 2 — lifecycle qualification

Generate fresh evidence for:

- cancel;
- retry;
- restart recovery;
- encoder fallback.

Do not reuse narrative Markdown from an old branch as machine evidence.

## Wave 3 — reference qualification

1. Identify the single latest RC/reference candidate.
2. Verify all report hashes belong to that exact candidate.
3. Jovi watches/listens.
4. Record structured human review.
5. Produce Prereview.
6. If a standard local-reference fixture is still required, request one Jovi-authorized local MP4 + rights and run the conservative standard path.

## Wave 4 — final acceptance

1. Boundary Audit.
2. Bounded regression report.
3. Acceptance Manifest.
4. Fresh-clone or equivalent reproducibility check.
5. Independent read-only evidence review.
6. Formal Gate exactly once.

If Gate succeeds:

`PHASE1_LOCAL_VIDEO_FACTORY_READY`

Then stop. Do not start Phase 2 in the same task.

---

# 15. Human-action policy

Codex/Agent should do everything it can automatically and only ask Jovi at true human gates:

- watch/listen to a candidate;
- provide a private authorized reference MP4;
- provide the original Pink Pig asset pack if a mascot-enabled final video is required;
- approve phase promotion after a successful Gate.

Do not ask Jovi to run routine tests, inspect JSON manually, or decide implementation details the agent can resolve from repository contracts.

---

# 16. Obsidian handoff requirement

Local memory root:

`E:\AI_Tools\Obsidian\Data\notes-personal\codex_memory\03-项目记忆\OpenClaw_VideoFactory\`

Current pages to maintain:

- `04-落地状态与执行计划.md`
- `06-Phase1本地视频工厂收口.md`

Rules:

- append/update current state, don't erase history;
- record exact tested HEAD;
- record selected final candidate IDs/hashes;
- record Jovi decisions;
- do not store credentials, private media content, raw model output or raw provider prompts.

Obsidian is outside Git.

---

# 17. Git rules for the next agent

- Continue on `codex/phase1-reference-video-analysis-001` unless Jovi explicitly changes this.
- Fetch before work.
- No force push.
- No reset/clean/automatic stash.
- Do not commit `dist/`, SQLite runtime, private reference media, private human-review notes with local paths, caches, credentials or models.
- Source, Schemas, deterministic fixture assets, tests and privacy-safe reports can be committed.
- Before each commit: focused tests + `git diff --check` + secret/path scan.
- Push reviewed/scoped commits to the same remote branch.

---

# 18. Correct reading order for a new window

1. `START_HERE_CODEX.md`
2. `PROJECT_STATUS.yaml`
3. `docs/README.md`
4. `docs/CURRENT_ARCHITECTURE.md`
5. `docs/PRODUCT_PHASES.md`
6. this file
7. `runbook/11_PHASE1_COMPLETION.md`
8. `docs/OPEN_SOURCE_SKILL_MATRIX.md`
9. `docs/REFERENCE_VIDEO_ANALYSIS.md`
10. `docs/PINK_PIG_CURRENT_POLICY.md`
11. `skills/video-production-chain/SKILL.md`
12. current `tasks/todo.md`
13. latest Change Requests and code touched by the next task

Do not begin with old Feishu P0 reports or the long historical Pink Pig architecture document.

---

# 19. One-sentence project truth

**OpenClaw VideoFactory has already proven most of the technology needed to generate and reconstruct technical videos locally; the job now is to finish a small set of missing fixtures/lifecycle/human-review evidence and close one formal Phase 1 Gate before touching Feishu automation.**
