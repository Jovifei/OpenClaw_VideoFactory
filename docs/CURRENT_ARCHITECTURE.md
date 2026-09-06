# OpenClaw VideoFactory — Current Architecture

Updated: 2026-09-05

本文件是当前 Phase 1 技术架构的权威说明。它吸收了 2026-08 至今的 Pink Pig、AI Director、Composition、reference-video、Remotion、Jianying 和 acceptance/gate 迭代，但不把任何单次实验当成全局默认。

## 1. 产品边界

### Phase 1 当前必须解决的问题

Phase 1 的目标不是“写出一个能把图片拼成 MP4 的 Demo”，而是把本地视频生产变成可反复执行、可追踪、可取消、可恢复、可审核的产品链。

核心输入只有三类：

1. `topic` — Jovi 给主题和事实边界；
2. `local_reference` — Jovi 给一条拥有处理权的本地 MP4 + rights；
3. `authorized_public_research` — Jovi 明确授权使用公开资料研究主题，必须保存来源和日期。

核心输出：

- 原创脚本；
- Storyboard；
- Asset Selection / Manifest；
- Timeline；
- 本地 TTS/Voice evidence；
- subtitle / timing evidence；
- Render Report；
- H.264/AAC MP4；
- Cover；
- Quality Report；
- Review Package；
- SQLite Job/Event/Artifact evidence；
- Jovi Human Review；
- Phase 1 Prereview / Acceptance / Gate evidence。

Phase 1 **不依赖**飞书、OpenClaw Daily Runtime、Cron、自动选题或自动发布。

## 2. 当前主链

```text
                   ┌─────────────────────────────┐
                   │         Phase 1 Input       │
                   │ topic / local_reference /   │
                   │ authorized_public_research  │
                   └──────────────┬──────────────┘
                                  │
                                  v
                    factual / rights / digest
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 v                                 v
        Topic planning path               Reference analysis path
   src/factory/phase1_local.py          src/factory/reference_video.py
                 │                     ffprobe / PySceneDetect /
                 │                     optional cached ASR
                 │                                 │
                 └──────────────┬──────────────────┘
                                v
                   Script / Storyboard / Assets
                    src/factory/director/*
                    PinkPig/technical Registry
                                │
                                v
                       Storyboard compiler
                                │
                                v
                            Timeline
                                │
                ┌───────────────┼────────────────┐
                │               │                │
                v               v                v
              TTS          Subtitle/timing   Visual planning
                │               │                │
                └───────────────┼────────────────┘
                                v
                   Remotion / deterministic visual
                                │
                                v
                         existing FFmpeg path
                                │
                                v
                       final local MP4
                                │
                                v
                Quality Report / Review Package
                                │
                                v
                     SQLite PENDING_REVIEW
                                │
                                v
                       Jovi Human Review
                                │
                                v
                         Phase 1 Prereview
                                │
                                v
                     Acceptance Manifest / Gate
```

## 3. 状态与生命周期

`src/factory/db.py` 是当前本地控制平面的核心，而不是未来待实现项。数据库已经覆盖：

- jobs；
- job_events；
- artifacts；
- topic_history；
- source_records；
- stage_attempts；
- locks；
- 历史 delivery 表（Phase 1 不做真实发送）。

本地阶段：

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

异常状态：

```text
FAILED
CANCELLED
```

当前必须补齐的不是数据库表，而是：

- cancel 的真实执行证据；
- failed→retry 的真实执行证据；
- 进程中断/重启后的 controlled recovery 证据；
- encoder fallback 的统一 evidence JSON；
- 这些证据进入正式 Phase 1 acceptance manifest。

## 4. Topic 模式

Topic 模式当前可以通过 `phase1_local_brief` 与 verified factual brief 进入确定性规划。

关键原则：

- 用户输入不能直接指定 `asset_id`、文件路径、render 参数或 Provider Prompt；
- 事实必须通过 factual brief 的 source/fact contract；
- Script/Storyboard 必须由系统控制 ID、顺序和渲染字段；
- AssetSelector 只能选择 Registry 中允许的素材；
- 技术图优先 deterministic SVG/HTML/Remotion，不用 text-to-image 重画协议帧、寄存器、电路、代码和公式。

当前固定内容 Fixture：

- Modbus RTU — 已形成稳定本地 baseline；
- Flash/看门狗 — 已有 factual brief、两套技术卡片、无 mascot 修正版、本地成片/剪映实验；
- FreeRTOS — brief 已进入仓库，但仍需达到与前两者同等级的 render/review/prereview evidence。

## 5. Reference 模式

### 5.1 基础 Phase 1 分析

`src/factory/reference_video.py` 已实现：

- 仅接受本地 MP4；
- reparse/symlink 安全检查；
- SHA-256；
- ffprobe 元数据；
- 复制到 ignored/private reference store；
- 只读处理；
- PySceneDetect scene boundary；
- 可选已缓存 faster-whisper small ASR；
- `reference_receipt.json`；
- `reference_rights.json`；
- `reference_report.json`；
- `original_brief.json`；
- `difference_report.json`。

### 5.2 原创边界

Phase 1 允许学习：

- 主题；
- 粗粒度结构；
- 节奏；
- 场景密度；
- 通用表达方式。

不得复制：

- 原音；
- 水印；
- 连续原镜头；
- 完整原文案；
- 可识别包装或镜头顺序；
- 把参考视频本体/路径暴露进 review package。

### 5.3 最新 RC 高通参考重构

当前分支已经比早期 `REFERENCE_VIDEO_ANALYSIS.md` 描述更进一步：

- 新增 9:16 RC high-pass Remotion visual；
- 修复几何关系；
- 通过本地 TTS/SAMI 分段测量语音时间；
- 将 summary knowledge cards 的动画触发绑定到 measured speech cues，而不是自由循环动画；
- 增加 cutoff、transfer function、phase/time、设计验证等可见知识密度；
- 生成可供剪映打开的实验草稿和 post-render 质量证据。

这些成果说明 reference→original reconstruction 方向可行，但**仍属于 Phase 1 候选证据/人工 review-ready**，不能替代总 Gate。

## 6. Director 与 Provider

`src/factory/director/` 已存在 Provider-neutral Director、ScriptPlanner、StoryboardAssembler、AssetSelector 和 factual context。

历史上真实 Codex CLI Provider 曾因为本地 models cache / `base_instructions` 问题失败。这个故障已经证明：

- Provider 接口需要 fail closed；
- Provider 环境问题不能污染 renderer；
- 本地确定性 Phase 1 不应被 Provider cache 卡死。

所以当前 Phase 1 Gate 允许在 verified factual brief 基础上走确定性本地规划。真实 Provider 恢复是独立增强，不再是 Phase 1 的唯一 blocker。

## 7. Visual / Composition / Render

### 7.1 技术画面

优先级：

```text
确定性 SVG / HTML / Remotion
→ 已审核本地素材库
→ licensed stock（未来）
→ ComfyUI 创意素材（Phase 3）
→ deterministic fallback
```

技术事实画面（协议帧、寄存器、电路、公式、代码、时序）禁止用不受控 text-to-image 当事实图。

### 7.2 Aspect Ratio Profiles

历史文档存在两个冲突默认值：1080×1920 和 1920×1080。当前统一规则：

- Aspect ratio 是 **Job/brief contract**，不是全局常量；
- Douyin/vertical knowledge profile：1080×1920 / 9:16；
- reference/Jianying landscape profile：1920×1080 / 16:9；
- Profile 决定安全区、字幕、Composition 和 Gate 断言；
- 不能再用一个固定分辨率验收所有任务。

### 7.3 Remotion

Remotion 已从“候选模板”升级为实际使用的 deterministic visual engine：

- 参考高通动画；
- Flash visual；
- 技术卡；
- 语音 cue 驱动画面；
- Composition 可编程布局。

继续坚持：Remotion 是视觉/时序实现，不拥有 Job State、事实审核或用户权限。

### 7.4 FFmpeg

FFmpeg/ffprobe 继续是最终媒体基础设施：

- H.264/AAC；
- visual/audio mux；
- decode 验证；
- metadata；
- volume/stream checks；
- CPU/NVENC encoder fallback。

## 8. Audio / Subtitle / AV Sync

早期字幕问题推动了安全区和 Composition Contract；后续参考重构又推动了真正的音画同步。

当前原则：

- narration 是单一事实文本来源；
- 音频实际时长必须反馈到 scene/timing；
- 动画重点应优先绑定真实 speech cue，而非固定百分比或 modulo 动画；
- subtitle/caption 不得遮挡 content；
- Jianying 路线只有一个 native subtitle track 和一个可听 VoiceOver track；
- 本地 MP4 可以是 burned subtitle 版本用于确定性验收；
- visual-only Jianying input 必须无音频、无烧录字幕，避免“双字幕/双音轨权威”。

## 9. Pink Pig / Personal IP

### 历史教训

早期仓库使用过自制 Pink Pig PNG/SVG，视觉上不等同于 Jovi 确定的原始 IP。这导致“技术链正确但品牌角色错误”。

### 当前政策

- `Jovifei/ian-fenzhu-illustrations` = style DNA / persona / composition rule 来源；
- 它不是完整最终角色图包；
- mascot 默认 off；
- Jovi 明确 opt-in 时，只能用 Jovi 原始资产 pack + receipt；
- 缺资产时：mascot-required brief fail closed；普通视频可无 mascot 继续；
- local self-made / AI temporary / upstream sample 均不能冒充用户原始 IP。

详见 `docs/PINK_PIG_CURRENT_POLICY.md` 与 `config/mascot_usage.yaml`。

## 10. Jianying 的正确位置

最新分支已经证明 Jianying 草稿链可做：

- visual-only MP4；
- VoiceOver；
- native Subtitles；
- E-drive runtime；
- visible junction；
- 手工打开/试听/导出。

但**Jianying 不是 Phase 1 Core Gate 的必要 renderer**。

正确架构：

```text
                 ┌─ mandatory: final local MP4 + quality/review package
Renderer output ─┤
                 └─ optional: Jianying editable draft → Jovi manual edit/export
```

原因：

- 项目最终要自动生成视频，不能把 Phase 1 成功定义成“还必须人工剪完才能有 MP4”；
- 剪映是编辑/交付增强；
- 草稿失败不应使一个已通过媒体 Gate 的本地 MP4 失效；
- 用户仍可在 Phase 1 候选上人工试听/审美复核。

## 11. Open Source Design Adoption

### 直接依赖或实际使用

- FFmpeg / ffprobe；
- Remotion；
- PySceneDetect；
- faster-whisper（reference optional ASR）；
- JSON Schema / PyYAML 等基础组件；
- jianying-editor-skill（可选编辑后端，需 pinned revision）。

### 方法借鉴

- VideoClaw：阶段化 Artifact、用户可介入、可修改中间产物、Pipeline runner/storage/events 思想；
- video-podcast-maker：研究→脚本→TTS/timing→Remotion；
- OpenMontage：审批门、Backlot/可视化、自检方法；
- Code2MP4/OpenReels 等：数据合同/Director score/短视频 archetype 思想。

### 明确不引入

- VideoClaw 第二套 backend/frontend/state DB；
- n8n/LangGraph/Temporal 作为第二编排层；
- OpenMontage AGPL 源码直接复制；
- 多个剪映/CapCut 后端并行控制同一 Job；
- 未审查的 ComfyUI 节点/模型自动下载。

## 12. Phase 1 当前 Gate 缺口

必须补齐：

1. FreeRTOS render/review/prereview；
2. 三个固定主题统一 evidence；
3. cancel；
4. failed retry；
5. restart recovery；
6. encoder fallback；
7. 最新 reference candidate 的 Jovi 人工音画/原创性审阅；
8. 必要时一条明确授权本地 reference fixture 的正式 Gate evidence；
9. Acceptance Manifest；
10. Boundary Audit；
11. bounded full Phase 1 regression；
12. independent read-only audit；
13. one-shot Phase 1 Gate。

只有这些完成，才允许将 Phase 1 标记为 `passed` 并进入飞书 Phase 2。
