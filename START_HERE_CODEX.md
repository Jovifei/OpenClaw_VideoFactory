# START HERE — OpenClaw VideoFactory current execution entry

Updated: 2026-09-05

> 新 Agent 先读本文件。历史 P0/Feishu/OAuth/Gateway 调试记录仍保留在 `reports/`、`runbook/` 和 Git 历史，但**当前产品主线是 Phase 1 本地视频工厂**。不要从旧任务编号推断当前阶段。

> **Topic-only qualification compatibility:** `topic_only_v1` requires
> Flash/watchdog, FreeRTOS, I2C, and one distinct live topic with hash-bound,
> explicitly approved human reviews. It preserves, rather than replaces,
> `legacy_topic_reference_v1`. Jianying is optional/manual; export and
> publication remain disabled.

> **Current closure handoff (2026-09-28):** read
> `handoff/codex/PHASE1_AUDIO_AND_CLOSURE_HANDOFF_20260928.md` after this
> file. It records the source-aligned narration contract, objective audio
> integrity evidence, current topic-only scope, and the ordered closure work.

## 0. 当前唯一产品顺序

```text
Phase 1 — Local Video Factory  ← CURRENT
  A. Jovi 给主题 → 自动生成本地可审阅视频
  B. Jovi 给授权本地参考视频 → 分析 → 原创重构视频
  C. 状态/恢复/质量/人工审核/正式 Gate

Phase 2 — Feishu Automation
  Phase 1 passed 后才实现候选卡、选择、12:00 合格兜底、受控交付、Cron

Phase 3+ — GPU/ComfyUI/WhisperX/高级视觉/高级参考原创检查/可编辑交付
```

抖音最终发布由 Jovi 人工执行。

## 1. 当前仓库与分支

- Root: `E:\project\OpenClaw_VideoFactory`
- Active branch after branch consolidation: `main`
- Product phase: `PHASE_1_LOCAL_VIDEO_FACTORY`
- Status: `in_progress`

接手时必须重新确认：

```powershell
Set-Location E:\project\OpenClaw_VideoFactory
git fetch
git status --short --untracked-files=all
git rev-parse HEAD
git rev-parse origin/main
git diff --check
```

禁止自动 `reset`、`clean`、`stash`、`rebase` 或 force push。

## 2. 先读这些，不要先读历史 P0 报告

按顺序：

1. `PROJECT_STATUS.yaml`
2. `docs/README.md`
3. `docs/CURRENT_ARCHITECTURE.md`
4. `docs/PRODUCT_PHASES.md`
5. `handoff/codex/PROJECT_HANDOFF_20260905.md`
6. `runbook/11_PHASE1_COMPLETION.md`
7. `docs/OPEN_SOURCE_SKILL_MATRIX.md`
8. `tasks/todo.md` 中最新 Phase 1 条目
9. 当前任务对应 Change Request
10. 相关源码和测试

如果这些文件与 `docs/PINK_PIG_PHASE1_ARCHITECTURE.md`、旧 P0/P1/P2 报告、旧 Agent Prompt 冲突，以以上当前文档 + 当前源码/Schema/真实证据为准。

## 3. 最终目标

### 3.1 Topic → Video

Jovi 输入一个技术主题，例如：

`FreeRTOS 优先级反转是怎么发生的？`

系统应自动完成：

```text
verified factual brief
→ script
→ storyboard
→ approved assets / deterministic technical visuals
→ source-bound script → measured local TTS (overflow fails closed)
→ one bounded fact-preserving rewrite when the duration budget requires it
→ complete-segment padding only
→ subtitle/timing/speech cues
→ Remotion/FFmpeg
→ final local MP4
→ quality report
→ review package
→ Jovi review
```

### 3.2 Reference → Analysis → Original Video

Jovi 提供一条拥有权利的本地 MP4 和 rights evidence：

```text
read-only ingest + SHA-256
→ ffprobe / scenes / pace / optional local ASR
→ abstract reference report
→ original brief
→ new script/storyboard/visuals/narration
→ new MP4
→ difference report
→ Jovi originality review
```

禁止复用原音、水印、连续原镜头、完整原文案或可识别包装。

## 4. 已经完成的模块，不要重写

- `src/factory/db.py` — SQLite Job/Event/Artifact/Stage Attempt；
- `src/factory/state.py` — lifecycle；
- `src/factory/phase1_cli.py` — local `create-topic/create-reference/run/status/cancel/retry`；
- `src/factory/phase1_local.py` — local planning；
- `src/factory/reference_video.py` — safe reference analysis / original brief / difference report；
- `src/factory/director/` — provider-neutral Director contracts；
- `video_factory/pipeline/` — Storyboard/Timeline/TTS/Subtitle/Composition/Renderer/Review Package；
- `generate_video.py` — existing video entrypoint；
- `src/factory/phase1_acceptance.py` — single-job prereview；
- `src/factory/phase1_gate.py` — formal Phase 1 gate；
- `remotion/` — deterministic technical visual implementations；
- `skills/video-production-chain/` — current end-to-end Skill contract。

只在当前测试/证据暴露真实兼容问题时修改这些模块。

## 5. 最新实际进展

在早期 `355 passed, 1 skipped` reference baseline 之后，当前分支又前进多轮：

- Flash/Watchdog factual brief 与技术插图；
- mascot-free Flash 修正；
- 16:9 与 9:16 profile 并存；
- Jianying visual-only + VoiceOver + native subtitle 实验链；
- audio/visual timing 修复；
- RC high-pass reference reconstruction；
- corrected geometry；
- local speech subsegments；
- measured speech cues；
- Remotion knowledge-card animation 绑定真实 speech cue；
- post-render / critical-frame / all-frame quality checks；
- FreeRTOS brief；
- Phase 1 Human Review / Prereview / Acceptance / Gate contracts。

这些是成熟实现增量，但整个 Phase 1 仍未通过最终 Gate。

## 6. 当前真正缺口（2026-09-28 closure track）

历史报告中“FreeRTOS 尚未渲染”“必须重新生成 lifecycle evidence”以及
“先回到 Modbus/reference 实验”的描述已被当前闭环交接 superseded；不要据此
重跑已完成的工作。当前顺序是：

1. 同步 canonical 文档与当前代码/Gate/evidence；
2. 为源对齐 TTS 增加原始 PCM 前缀、静音尾、段序和最终端点的机器合同；
3. 以同一 shared planner 完成外层生产路径的无渲染集成审计；
4. 保留 Jovi 的独立音频质量听审门：只判断发音、可懂度、节奏、停顿和工程含义；
5. 对每个获得 `AUDIO_APPROVED` 的主题只执行一个新的外层候选；
6. 再做 MP4 SHA 绑定的人审、Prereview、I2C/live topic、manifest、独立审计和一次 Gate。

生命周期证据已完成，后续只做最终 hash/schema revalidation 和 manifest 绑定；
reference reconstruction 在本 `topic_only_v1` 收口中保持可选。Phase 2、Cron、飞书和发布继续禁止。

## 7. Render profile，不要再争论全局横竖屏

Aspect ratio 是 Job contract：

- vertical/Douyin knowledge: `1080×1920`, 9:16；
- landscape/reference-edit: `1920×1080`, 16:9 when brief requests it；
- 30 FPS；
- H.264/AAC；
- profile-specific safe area and subtitle rules。

任何旧文档声称“全局只能竖屏”或“全局默认横屏且所有任务都如此”都不是当前产品真相。

## 8. Pink Pig 当前规则

不要从旧 `PINK_PIG_PHASE1_ARCHITECTURE.md` 复制早期资产假设。

Current:

- `Jovifei/ian-fenzhu-illustrations` = style/persona/composition source；
- personal mascot default off；
- Jovi explicitly opt-in；
- mascot-enabled production requires Jovi-owned original asset pack + receipt；
- repository-created mascot / AI temp art / upstream sample cannot substitute；
- normal technical video may continue mascot-off；
- mascot cannot cover technical content。

Read `docs/PINK_PIG_CURRENT_POLICY.md`.

## 9. Jianying 当前规则

Jianying 已证明技术可行，但属于 optional editable-delivery/manual-review branch。

Mandatory Phase 1 result remains:

`local MP4 + quality report + review package`

Optional branch:

`visual-only MP4 → jianying-editor-skill → manual Jovi review/export`

No automatic export/publication.

## 10. Open-source adoption

Read `docs/OPEN_SOURCE_SKILL_MATRIX.md`.

Key points:

- Remotion: direct deterministic visual engine；
- FFmpeg: direct media engine；
- PySceneDetect: direct reference scene analysis；
- faster-whisper: optional reference ASR only；
- VideoClaw: borrow stage-artifact/user-review/recoverable-workflow ideas, not its second backend/state DB；
- video-podcast-maker: method reference only; current CC BY-NC 4.0 means no careless code/template copying into a commercial path；
- ian-fenzhu-illustrations: MIT style/persona source, not final user-owned asset proof；
- jianying-editor-skill: optional pinned MIT editor backend；
- ComfyUI/WhisperX/OpenMontage/etc: deferred or method-only unless separately authorized。

## 11. Phase 1 禁止事项

- 不进入飞书/候选卡/Cron；
- 不继续把历史 Codex Provider cache 修复当主线；
- 不下载新模型或 ComfyUI 节点；
- 不引入 n8n/LangGraph/Temporal/第二套 VideoClaw backend；
- 不创建第二个 Job DB；
- 不把 reference raw media 提交 Git；
- 不自动发布抖音；
- 不自动标记 Human Review approved；
- 不为了 Gate 通过而放宽 Gate；
- 不把一个 review-ready 子任务写成整个 Phase 1 passed。

## 12. 每次停止时必须更新

### Repository

For the topic-only acceptance scope, retain the exact fixed set above. Every
other Phase 1 rule continues to prohibit Feishu delivery, automatic topic
selection, Cron, AI-video generation, automatic Jianying export, Douyin
publication, and Codex Plugin OAuth troubleshooting.

- `tasks/todo.md` 当前任务状态；
- Change Request / evidence；
- 必要的 canonical docs（若事实改变）；
- tested commit SHA。

### Obsidian（仓库外）

Root:

`E:\AI_Tools\Obsidian\Data\notes-personal\codex_memory\03-项目记忆\OpenClaw_VideoFactory\`

至少更新：

- `04-落地状态与执行计划.md`
- `06-Phase1本地视频工厂收口.md`

规则：只追加/校正当前状态，不抹历史；不写 Token、私有媒体路径、原始 Prompt、raw model output。

## 13. Stop conditions

Agent 只有在以下情况允许停下请求 Jovi：

- 需要 Jovi 观看/试听一个明确候选；
- 需要 Jovi 提供授权 reference MP4 / original Pink Pig asset pack；
- 存在有最小复现的真实 blocker；
- Formal Gate 已得出结果。

不得“写了计划/报告”就当完成。
