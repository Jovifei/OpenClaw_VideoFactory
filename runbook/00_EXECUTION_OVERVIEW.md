# 00 — 执行总览（Current Product Order）

Updated: 2026-09-05

## 当前阶段依赖

```text
PACKAGE
  ↓
Phase 1 Local Video Factory  ← CURRENT / IN PROGRESS
  ↓
Phase 2 Feishu Automation
  ↓
Phase 3 GPU / Advanced Media
  ↓
Phase 4 Advanced Reference Originality
  ↓
Phase 5 Editable Delivery / Publish Assist
  ↓
PRODUCTION TRIAL
```

历史 `P0`–`P5` 是旧证据/工具兼容标签，不定义当前产品顺序。历史飞书 P0 只在 Phase 2 重新成为安全前置，不能阻塞 Phase 1。

## Phase 1 当前目标

必须完成两条用户价值链：

```text
Jovi topic
→ facts
→ script/storyboard/assets
→ TTS/subtitles/timing
→ deterministic visuals
→ Remotion/FFmpeg
→ local MP4
→ quality/review
```

```text
Jovi authorized local reference MP4
→ safe analysis
→ abstract reference report
→ original brief
→ newly rendered video
→ difference report
→ human originality review
```

同时必须证明本地 Job 的：

- idempotency；
- cancel；
- failed retry；
- controlled restart recovery；
- encoder fallback；
- human review；
- formal Gate。

## Phase 1 当前已完成的重要基础

- SQLite state/event/artifact/stage-attempt store；
- topic and reference CLI；
- Director/Storyboard/Timeline/Registry contracts；
- TTS/subtitle/composition/render/review package；
- Modbus baseline；
- Flash/watchdog technical candidates；
- FreeRTOS brief；
- PySceneDetect + optional cached faster-whisper reference analysis；
- RC high-pass Remotion reference reconstruction + measured speech cues；
- optional Jianying draft chain；
- Human Review / Prereview / Acceptance / Phase Gate implementation。

## 当前真正缺口

1. FreeRTOS 成片和 Prereview；
2. Modbus / Flash / FreeRTOS 统一最终候选证据；
3. cancel/retry/restart/fallback fresh machine evidence；
4. 最新 reference candidate 的 Jovi 人工音画/原创审核；
5. 必要时一条标准 `local_reference` fixture；
6. Acceptance Manifest + Boundary Audit；
7. bounded regression + independent review；
8. one-shot Phase 1 Gate。

## Phase 1 禁止提前做

- Feishu/Gateway/Binding/OAuth/lark-cli/Cron；
- 自动选题和自动发布；
- 把历史 Codex Provider cache 修复当主线；
- 未批准模型/ComfyUI 节点下载；
- 第二套 VideoClaw backend / n8n / LangGraph / Temporal；
- 第二套 Job DB；
- 多编辑后端同时控制一个 Job。

## Render / Editor 边界

- Aspect ratio 是 Job profile：9:16 或 16:9；
- Remotion + deterministic visual 是可审计视觉实现；
- FFmpeg 是核心媒体输出；
- Phase 1 mandatory = local MP4 + evidence；
- Jianying = optional editable/manual-review branch；
- 草稿失败不推翻已合格 local MP4。

## Pink Pig 边界

Personal IP 默认 off。只有 Jovi 明确 opt-in 且提供 Jovi-owned original asset pack + receipt 时启用；不允许 repo-created/AI/upstream sample 冒充用户原始 IP。

## Git 与证据

当前任务继续使用：

`codex/phase1-reference-video-analysis-001`

不要根据旧文档自动新建 `phase/1-*` 分支。

每个阶段结果必须记录 exact HEAD、命令、退出码、测试范围、Artifact SHA、限制和人工决策。不要把多个历史测试计数相加。

## Jovi 介入点

Phase 1 只有这些需要停下来找 Jovi：

- 观看/试听一个明确最终候选；
- 提供真实授权 reference MP4 + rights；
- mascot-required 视频需要 Jovi 原始 Pink Pig 资产包；
- 许可证/模型下载/超预算；
- formal Gate 后批准状态提升。

Routine tests、JSON 对账、代码决策由 Agent 自己完成。

## 回退链

```text
事实不足 → 请求 Jovi/可靠来源，而不是编造
reference 分析失败 → 保守 topic mode 或明确阻塞
TTS失败 → approved local fallback / fail with evidence
ASR cache缺失 → reference transcript unavailable，但保守分析可继续
creative asset失败 → deterministic technical visual
NVENC失败 → CPU libx264
mascot资产缺失 → mascot-off；若 brief 强制 mascot 则 fail closed
Jianying失败 → 保留已合格 local MP4
Feishu失败（Phase 2 only）→ 保留本地 review package，不自动发布
```
