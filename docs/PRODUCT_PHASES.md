# OpenClaw VideoFactory 产品阶段定义

Updated: 2026-09-05

## 最终产品目标

在 Windows 本机完成一条**自动生成、可审阅、可追溯、可恢复**的短视频生产链；本地视频工厂成熟后，再用 OpenClaw/飞书做选题与受控交付。

```text
Jovi 给主题 / 授权本地参考视频 / 明确授权公开研究
  → 事实输入与原创边界
  → 脚本、Storyboard、素材选择
  → TTS、字幕、知识插图、程序化画面
  → Remotion/确定性视觉 + FFmpeg
  → 本地 MP4、质量报告、Review Package
  → Jovi 人工审核
  → Phase 1 Gate
  → Phase 2 才接飞书候选/选择/兜底/交付
```

抖音发布由 Jovi 人工完成，除非未来另有明确授权。

---

## Phase 1 — 本地视频工厂（当前，in progress）

### 用户必须获得的能力

#### A. 主题自动生成视频

用户只提供一个技术主题和事实边界，系统自动完成：

```text
topic
→ factual brief
→ script
→ storyboard
→ asset selection
→ narration / subtitle timing
→ technical visuals
→ render
→ MP4
→ quality/review package
```

#### B. 参考视频分析 + 原创重构

用户提供有处理权的本地 MP4 和 rights：

```text
reference MP4
→ read-only ingest / SHA-256
→ scene/pace/optional ASR
→ abstract reference report
→ original brief
→ new script/storyboard/visuals
→ original MP4
→ difference report
→ human originality review
```

### 输入模式

1. `topic`：Jovi 给主题和 verified factual brief；
2. `local_reference`：Jovi 提供本地、拥有权利的 MP4 和 rights 记录；
3. `authorized_public_research`：只有 Jovi 明确授权时使用公开来源，并记录来源、日期和事实边界。

### 必须输出

- 原创 Script / Storyboard；
- Registry/approved technical assets；
- Timeline；
- TTS/voice evidence；
- subtitles / timing evidence；
- Render Report；
- H.264/AAC 可解码 MP4；
- Cover；
- Quality Report；
- Review Package；
- SQLite Job/Event/Stage Attempt/Artifact Hash；
- Human Review；
- Reference 模式的 receipt/rights/report/original brief/difference report。

### Render profile

不再把某一个分辨率写成所有视频的唯一标准：

- Douyin/vertical knowledge profile：`1080×1920`、9:16；
- reference/Jianying landscape profile：可按 brief 使用 `1920×1080`、16:9；
- 每个 Job 的 profile 决定 Composition、安全区和 Gate 断言；
- FPS 默认 30；最终媒体仍要求 H.264/AAC 和完整 decode。

### 已完成到什么程度

已具备：

- Topic 最小切片与 Modbus baseline；
- Flash/watchdog factual brief、确定性技术视觉、本地成片和多轮修正；
- FreeRTOS brief；
- SQLite lifecycle；
- Storyboard/Timeline/Composition/字幕安全区；
- Provider-neutral Director；
- Reference safe ingest、PySceneDetect、可选 cached ASR；
- RC high-pass reference reconstruction、Remotion visual、speech-cue-bound knowledge animation；
- Review Package / Human Review Schema / Prereview / Gate 实现；
- 可选 Jianying editable draft 实验链。

### 仍未完成的 Phase 1 Gate 证据

- FreeRTOS 固定主题成片、Review、Prereview；
- Modbus / Flash / FreeRTOS 统一证据格式和当前 Schema 对账；
- cancel / failed retry / restart recovery / encoder fallback 统一机器 evidence；
- 最新 reference candidate 的 Jovi 人工视听与原创性审核；
- 如正式 Gate 仍要求真实 local-reference fixture，则使用 Jovi 授权 MP4 + rights 完成；
- Acceptance Manifest；
- Boundary Audit；
- bounded regression / fresh-clone evidence；
- independent read-only review；
- one-shot Phase 1 Gate。

### 正式通过条件

只有以上证据齐全并产生：

`reports/gates/PHASE1_READY.json`

才允许将 Phase 1 标记为 `passed`。

Gate 本身不应自动修改 `PROJECT_STATUS.yaml`；状态提升需要单独、明确的收口操作。

### Phase 1 明确不依赖

- 飞书入口；
- 08:30/12:00 调度；
- Cron；
- OpenClaw 日常 Runtime；
- ComfyUI 新模型；
- WhisperX；
- 自动剪映导出；
- Codex CLI Provider cache 修复；
- 自动发布。

### Jianying 的位置

Jianying 是**可选编辑/可编辑交付分支**，不是 Phase 1 本地 MP4 的唯一成功路径：

```text
validated renderer output
  ├─ required: local final MP4 + review evidence
  └─ optional: visual-only MP4 → Jianying draft → Jovi manual edit/export
```

---

## Phase 2 — 飞书自动化

只有 Phase 1 passed 后才进入：

- 飞书安全入站；
- 08:30 推送 3–5 个候选；
- 用户选择；
- 12:00 只对达到质量门槛的候选执行兜底；
- 消息、Job、交付幂等；
- 取消、重试、重启恢复；
- Review Package 受控飞书交付；
- 非定时验证通过后才注册 Cron；
- Jovi 人工发布抖音。

历史 P0 飞书安全材料在这里重新成为 Phase 2 的输入证据，而不是 Phase 1 的 blocker。

---

## Phase 3 — GPU 与高级视觉生产

- RTX 4070 SUPER Job queue；
- approved ComfyUI workflow；
- NVENC 加速；
- OOM / CPU fallback；
- 可选 WhisperX；
- approved image/video generation；
- 模型/节点下载必须单独授权并受磁盘预算约束。

---

## Phase 4 — 高级参考视频原创化

在 Phase 1 保守参考分析之上增加：

- 更丰富视觉语义；
- OCR/结构/镜头语言；
- perceptual similarity 辅助检查；
- shot-sequence similarity；
- 更严格版权与原创审阅；
- 仍禁止复用原音、水印、连续原镜头和完整原文案。

---

## Phase 5 — 可编辑交付与发布辅助

- Jianying/其他经审查编辑后端；
- 标题、封面、简介、发布检查清单；
- editable draft；
- 草稿失败不得让已合格的核心 MP4 失效；
- 不自动发布抖音。

当前分支已经提前验证了部分 Jianying 技术可行性，这些成果可复用，但不改变产品阶段顺序。

---

## 从 VideoClaw 借鉴什么

`HITsz-TMG/VideoClaw` 的价值主要在产品/工作流思想：

- idea → stage-based workflow；
- 每阶段持续产出可查看、可确认、可修改的中间资产；
- pipeline runner / events / storage 的职责拆分；
- 用户可在关键节点介入；
- reference image/video → final edit 的阶段化生产理念。

本项目不直接引入：

- VideoClaw 第二套 Backend/Frontend；
- 第二个项目状态数据库；
- 替换现有 Storyboard/Timeline/Renderer；
- 云模型/视频生成 Provider 扩张作为 Phase 1 前置。

即：**借它的“可编辑阶段资产 + 人工确认 + 可恢复工作流”，保留我们的 SQLite、Schema、技术视频 Renderer 和 Phase Gate。**
