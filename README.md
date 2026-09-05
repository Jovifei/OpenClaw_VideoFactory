# OpenClaw VideoFactory

OpenClaw VideoFactory 是一个 **Windows 本地 AI 短视频生产工程**。项目的产品顺序已经明确：

1. **Phase 1：先把本地视频工厂做完整**——用户给主题，系统自动完成事实输入、脚本、分镜、素材、配音、字幕、渲染、质量检查和本地审阅包；用户给一条有权处理的参考视频时，系统还能做安全分析并生成原创重构视频。
2. **Phase 2：Phase 1 正式通过后才接飞书**——候选选题、用户选择、12:00 合格兜底、受控交付、取消/恢复和最终 Cron。
3. GPU/ComfyUI、WhisperX、高级参考视频相似度检查、剪映深度编辑等属于后续增强，不得反过来阻塞 Phase 1 的本地 MP4 闭环。

抖音发布始终由 Jovi 人工完成，除非未来另有明确授权。

> **当前分支事实入口**：先读 `START_HERE_CODEX.md` → `PROJECT_STATUS.yaml` → `docs/README.md` → `docs/CURRENT_ARCHITECTURE.md` → `docs/PRODUCT_PHASES.md` → `handoff/codex/PROJECT_HANDOFF_20260905.md`。历史 P0/P1/P2 报告仍保留作证据，但不再定义产品执行顺序。

GitHub：<https://github.com/Jovifei/OpenClaw_VideoFactory>

## 当前状态

当前产品阶段：`PHASE_1_LOCAL_VIDEO_FACTORY`，状态应理解为 **in progress / implementation mature, final gate not passed**。

已经落地的核心能力：

- `src/factory/db.py`：SQLite Job、事件、Artifact、Stage Attempt、幂等与状态记录；
- `src/factory/phase1_cli.py`：`create-topic`、`create-reference`、`run`、`status`、`cancel`、`retry`；
- `src/factory/phase1_local.py`：主题/参考抽象到结构化脚本、Storyboard、Registry 资产选择；
- `src/factory/reference_video.py`：本地参考 MP4 安全入库、SHA-256、PySceneDetect、可选离线 ASR、original brief 与 difference report；
- `src/factory/director/`：Provider-neutral Director 与受限结构化输出合同；
- `video_factory/pipeline/`：Storyboard、Timeline、TTS、字幕、Composition、Renderer、Render Report、Review Package；
- `generate_video.py`：现有统一渲染入口；
- Remotion：已用于确定性技术画面和参考重构视觉；
- FFmpeg/ffprobe：最终编码、探测、完整 decode 和质量证据；
- 剪映草稿链：已形成可审阅实验/编辑分支，但 **不是 Phase 1 本地 MP4 Gate 的硬前置**；
- 本地参考重构：已完成多个 RC 高通重构迭代，并将知识卡动效绑定到实测语音 cue；
- Flash/看门狗：已有 factual brief、确定性技术插图、无 mascot 版本和本地成片证据；
- FreeRTOS：已有 Phase 1 brief，但仍需完成与 Modbus/Flash 同等级的成片与资格证据；
- Phase 1 acceptance/gate：已有 Schema、Prereview、人工审阅合同和 Gate 工具，尚未获得整阶段通过证据。

因此当前真正缺口不是“再造一个视频生成器”，而是：**把已完成子链统一收口为正式 Phase 1 产品验收，并补齐尚缺的 Fixture、生命周期和人工审阅证据。**

## 最终 Phase 1 用户体验

### 主题模式

```text
Jovi："做一个讲 FreeRTOS 优先级反转的视频"
  ↓
verified factual brief / 已授权公开研究
  ↓
脚本 → Storyboard → 技术素材/可选个人 IP → TTS → 字幕/语音 cue
  ↓
Remotion/确定性画面 + FFmpeg
  ↓
本地 MP4 + cover + quality report + review package
  ↓
Jovi 人工审阅
```

### 参考视频模式

```text
Jovi 提供有权处理的本地 MP4 + rights
  ↓
只读入库 + SHA-256 + 场景/节奏/可选 ASR
  ↓
抽象 reference report / original brief
  ↓
重新写脚本、重新做分镜和视觉
  ↓
原创 MP4 + difference report + review package
  ↓
Jovi 人工原创性审阅
```

参考视频模式禁止复用原音、水印、连续原镜头或完整原文案。高级感知相似度不是 Phase 1 最低门，但人工原创性审核必须保留。

## 渲染与画布策略

项目已经验证过竖屏和横屏两种路线，因此不要再把某一个分辨率写成全局唯一真理：

- **Douyin/知识短视频 profile**：`1080×1920`，9:16；
- **reference reconstruction / Jianying editing profile**：可按 brief 使用 `1920×1080`，16:9；
- 每个 Job 的 `aspect_ratio` / render contract 才是当前视频的权威；
- 质量 Gate 必须检查“是否符合该 Job 的 profile”，而不是用一个硬编码分辨率检查所有任务。

Remotion 负责可审计、可编程的确定性画面；FFmpeg 负责编码、音视频合成和质量探测。剪映只作为可选的可编辑交付/人工编辑后端，不能替代本地可复现 MP4 主链。

## 小粉飞猪策略

`Jovifei/ian-fenzhu-illustrations` 是 **IP/style DNA 规范来源**，不是可直接当作完整角色图库使用的仓库。

当前规则：

- 个人 IP 默认 `off`；
- Jovi 在当前 brief 明确要求时才启用；
- 启用后必须使用 Jovi 提供并通过 receipt 绑定的原始资产包；
- 仓库自制 PNG/SVG、AI 临时生成图、上游样例 JPG 都不能冒充 Jovi 原始 IP；
- 缺少原始资产时 fail closed 或无 mascot 继续主视频；
- 角色永远不能遮挡技术图、代码、协议帧、字幕或关键操作。

这条规则解决了早期“生成出来的猪不像用户确定版 IP”的问题。

## 当前开源借鉴

项目坚持“借思想/借稳定组件，不引入第二套总编排”。完整清单见 `docs/OPEN_SOURCE_SKILL_MATRIX.md`。

重点包括：

- **Remotion / remotion-dev/skills**：程序化视频、时序、Composition、预览与 Agent 最佳实践；
- **FFmpeg / ffprobe**：最终编解码、转码、探测和完整 decode；
- **PySceneDetect**：参考视频切镜和节奏测量；
- **faster-whisper**：参考视频可选本地 ASR，不是普通 TTS 成片的必需步骤；
- **VideoClaw (HITsz-TMG/VideoClaw)**：借鉴“阶段 Artifact、可修改中间资产、可恢复工作流、人工确认节点”的产品思想，不引入它的第二套 backend/frontend/state DB；
- **Agents365-ai/video-podcast-maker**：借鉴研究→脚本→TTS/timing→Remotion 的知识视频流程；其仓库当前为 CC BY-NC 4.0，不能把代码直接复制进未来商业产品；
- **Jovifei/ian-fenzhu-illustrations**：小粉飞猪 style/persona/composition 规范来源；
- **jianying-editor-skill**：当前唯一被选中的剪映编辑后端；与 CapCut Mate/JianYing MCP 不在同一 Job 双启；
- **ComfyUI MCP / WhisperX / OpenMontage / Auto-Editor / Real-ESRGAN**：后续候选或方法参考，不是当前 Phase 1 Gate 的依赖。

## 目录地图

```text
.
├── START_HERE_CODEX.md        新 Agent 的第一入口
├── PROJECT_STATUS.yaml        当前产品阶段与已知缺口
├── docs/                      当前架构、阶段、开源借鉴；含历史设计快照
├── handoff/codex/             当前执行交接与验收合同
├── src/factory/               Phase 1 领域逻辑、状态、Director、参考分析
├── video_factory/pipeline/    Storyboard/Timeline/TTS/字幕/Renderer/Review
├── remotion/                  程序化视觉实现
├── skills/                    视频生产 Skill 合同
├── schemas/video/             视频工作流与验收 Schema
├── examples/                  可复现的主题/job/brief 示例
├── assets/                    已审查技术素材与实验资产
├── scripts/                   Phase 1/参考分析/质量/剪映与历史 Phase 2 工具
├── tests/                     当前功能与历史安全回归
├── reports/                   Change Request、证据和历史报告
├── runbook/                   执行与验收步骤
└── tasks/                     当前任务、计划与经验复盘
```

运行时媒体、SQLite、用户参考原件、模型缓存、私有审阅文件和凭据不得进入公开仓库。

## 当前下一步

Phase 1 收口顺序固定为：

1. 重新跑当前分支的聚焦回归并记录统一测试基线；
2. 完成 FreeRTOS 与缺失的固定主题资格证据；
3. 把 Modbus / Flash / FreeRTOS 三个主题 Job 对齐同一 Review/Prereview 合同；
4. 形成 cancel / retry / restart recovery / encoder fallback 的机器证据；
5. 对当前最新参考重构成片做 Jovi 人工审阅；若仍需要 Phase 1 真实本地 reference fixture，使用 Jovi 授权素材完成同一 Prereview；
6. 生成 Phase 1 Acceptance Manifest 与 Boundary Audit；
7. 独立只读审核；
8. 正式 Gate 只运行一次；
9. Gate 通过后才更新 `PROJECT_STATUS.yaml` 为 passed，并另开 Phase 2 飞书任务。

**不要提前接飞书、Cron、自动选题或自动发布。**
