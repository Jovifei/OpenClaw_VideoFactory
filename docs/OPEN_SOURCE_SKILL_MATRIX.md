# 开源 Skill / 工具 / 项目采用矩阵

Updated: 2026-09-05

## 总原则

OpenClaw VideoFactory 不把多个“一键视频生成器”叠加到同一主链。我们的核心资产是：

- 本地可恢复 SQLite Job；
- 明确的 Script / Storyboard / Asset / Timeline / Render / Review Schema；
- 技术知识视频的确定性视觉；
- Reference → Original Reconstruction 的安全边界；
- Phase Gate 与人工审阅。

因此对开源项目采用三种方式：

1. **Direct dependency / pinned adapter**：组件职责单一、许可证清晰、不会接管状态；
2. **Method adoption**：借设计和流程，不复制代码；
3. **Deferred / isolated**：保留候选，但不进入当前 Phase 1 Gate。

---

## A. 当前实际使用 / 强关联

### FFmpeg / ffprobe

角色：最终媒体基础设施。

使用：

- H.264/AAC；
- 音视频 mux；
- complete decode；
- stream/metadata probe；
- volume checks；
- libx264 / h264_nvenc fallback。

规则：FFmpeg 只执行结构化媒体合同，不拥有 Job 状态和事实审核。

### Remotion + remotion-dev/skills

角色：程序化视觉和时序引擎。

当前已经用于：

- technical cards；
- Flash visual；
- RC high-pass reference reconstruction；
- geometry contracts；
- speech-cue-bound animation；
- 9:16 / 16:9 Composition。

Remotion 官方 Skills 仍持续更新。修改 Remotion composition 前应优先读取当前 `remotion-best-practices` / create / markup / multimedia 等对应 Skill，而不是使用旧记忆中的 API。

不采用：Remotion 不接管 SQLite、Phase Gate、参考视频 rights 或 Feishu。

### PySceneDetect

当前 Phase 1 reference analysis 的直接离线依赖。

用途：

- scene boundary；
- scene duration；
- pace / shot density；
- 为 reference abstraction 提供确定性时间证据。

当前代码锁定的策略以 `src/factory/reference_video.py` 和 reference-analysis lock 为准。

### faster-whisper

角色：**参考视频可选本地 ASR**。

重要修正：它不是普通 TTS 成片必需组件。系统自己生成 narration 时，字幕/timing 应直接来自脚本与真实 TTS timing；只有需要理解外部参考音频时才调用 ASR。

Phase 1 规则：

- 只使用已经存在的本地 cache；
- cache 缺失记录 `unavailable`；
- 不自动联网下载模型；
- 普通 reference analysis 可降级继续。

### luoluoluo22/jianying-editor-skill

许可证：MIT。

角色：当前已经验证的 **可选剪映编辑后端**。

使用边界：

- 一次 Job 只使用一个编辑后端；
- visual-only input；
- 一个 VoiceOver track；
- 一个 native Subtitles track；
- 自动导出关闭；
- Jovi 手工打开、试听、审美检查和导出；
- E-drive runtime；
- 草稿链不替代核心 local MP4 Gate。

---

## B. 核心方法借鉴，不引入第二套系统

### HITsz-TMG/VideoClaw

许可证：MIT。

截至当前 README，VideoClaw 是一个从 idea 到 film 的阶段化 AI 导演系统，强调：

- script planning；
- character/scene design；
- storyboard；
- reference image；
- video generation；
- final editing；
- 每阶段产生可查看、可确认、可修改的中间资产；
- backend 中有 pipeline runner / events / storage 等职责拆分。

**我们直接借鉴的思想：**

1. 阶段 Artifact 是产品界面，不只是临时文件；
2. 上一阶段结果是下一阶段明确输入；
3. 人可以在关键节点审核/修改；
4. Job 应可恢复，失败点可定位；
5. pipeline runner / event / storage 的职责要分离；
6. 最终交付前必须存在可审阅中间资产。

**不直接引入的部分：**

- 第二套 VideoClaw backend；
- 第二套 frontend；
- 第二套 project/state DB；
- 云视频生成 Provider 作为 Phase 1 依赖；
- 替换我们的 Storyboard/Timeline/Renderer/SQLite；
- 把创意短剧式角色/场景生成强加给工程知识视频。

原因：这些部分与我们已有体系高度重叠，引入后会产生双状态、双渲染器和双审计链。

### Agents365-ai/video-podcast-maker

当前许可证：**CC BY-NC 4.0**。

用途：方法借鉴。

值得吸收：

- research → script；
- narration/TTS；
- timing；
- Remotion component；
- review/validation；
- Skill 内组织 references/scripts/templates 的方式。

重要许可证边界：

- 可以学习工作流和自行实现；
- 不把其代码/模板直接复制进未来可能商业化的产品链，除非重新确认许可和使用场景；
- 不让它接管我们的 Job state。

### Jovifei/ian-fenzhu-illustrations

许可证：MIT。

用途：小粉飞猪 style/persona/composition 规范来源。

已确认：它更接近 IP 设计规范/Skill，而不是完整的用户最终 production asset library。

因此：

- 可以读取 style DNA；
- 可以借 persona/composition rule；
- 不把上游 sample 当作 Jovi 原始最终角色资产；
- Personal IP 模式仍需要 Jovi-owned asset receipt。

### OpenMontage

用途：方法参考。

值得吸收：

- reference analysis；
- approval gate；
- media/backlot 可视化；
- multi-stage self-check；
- review-before-next-stage。

许可证/规模边界：历史审计记录其为 AGPL 路线，因此不把源码 vendoring 到本仓库；如果未来要直接集成，必须重新做许可证与部署审计。

### OpenReels / Code2MP4 / similar topic-to-short projects

用途：架构和合同参考。

可借鉴：

- Director score；
- visual archetype；
- retry / cost estimate；
- contract-oriented media pipeline。

不采用：不引入第二套全链视频工厂。

---

## C. Phase 3 / Phase 4 候选

### artokun/comfyui-mcp

定位：Agent → local ComfyUI 控制层。

候选用途：

- 封面；
- 背景；
- 非事实型创意插图；
- 2–4 秒 B-roll；
- 抠图/放大。

硬规则：

- 只连 loopback；
- approved workflow whitelist；
- 禁止无人值守自动装节点/模型；
- 失败退回 deterministic visual；
- 电路/代码/协议/公式等技术事实不使用不受控生成图替代。

### WhisperX

Phase 3/4 候选。

只有以下场景才值得比 faster-whisper 更早启用：

- reference speech 对齐精度明显不足；
- 多说话人；
- word-level alignment 是 review 必需证据。

普通自生成 narration 不必每条跑 WhisperX。

### Auto-Editor

候选用途：长口播/录屏预处理、静音/静止初剪。

不替代 Storyboard 和最终 Render Timeline。

### Real-ESRGAN

候选用途：低清非文字图像/生成素材放大。

不允许 AI 放大后的技术文字/电路标注直接当事实来源。

---

## D. 剪映 / CapCut 候选

### luoluoluo22/jianying-editor-skill

当前已选的唯一剪映后端，见 A 类。

### Hommy-master/capcut-mate

保留为未来隔离适配器候选。不得与 `jianying-editor-skill` 在一个 Job 同时启用。

### hey-jian-wei/jianying-mcp

只研究。未完成独立许可证、版本、权限、恢复审计前不进入生产链。

---

## E. Phase 2 才使用的 OpenClaw / Feishu 工具

### OpenClaw

Phase 2 角色：

- 长期运行 orchestrator；
- topic cards；
- user selection；
- delivery state；
- retry/recovery notification；
- schedule after gate。

Phase 1 不依赖 OpenClaw Runtime。

### larksuite/cli

Phase 2 角色：官方飞书 CLI / Skills，负责受控消息、文件和事件操作。

规则：

- bot identity；
- target allowlist；
- idempotency；
- dry-run / human confirmation；
- 生产 Cron 只能在 Phase 2 非定时证据通过后启用。

---

## F. 明确拒绝的架构堆叠

当前不增加：

- n8n；
- LangGraph；
- Temporal；
- 第二套 VideoClaw backend；
- 第二套 DB；
- 两个剪映后端同时写一个项目；
- 多个“一键生成视频”项目串联。

原因不是这些项目不好，而是我们已经有本地状态、Schema 和渲染链；继续叠编排器会使恢复、幂等、审计和调试更差。

---

## 当前推荐 Skill 路由

### Phase 1 Topic

```text
topic / factual brief
  ↓
script-storyboard-director
  ↓
media-asset-curator
  ↓
audio-subtitle-engine
  ↓
remotion-layout-engine / deterministic visuals
  ↓
existing FFmpeg renderer
  ↓
video-quality-gate
  ↓
local MP4 + review package
  └─ optional jianying-draft-exporter
```

### Phase 1 Reference

```text
reference-video-analyzer
  ↓ abstract evidence
reference-video-recreator / original brief
  ↓
script-storyboard-director
  ↓
assets + audio/timing + Remotion
  ↓
FFmpeg
  ↓
difference report + quality + human originality review
```

### Phase 2

```text
OpenClaw + Feishu
  ↓
topic cards / selection / qualified fallback
  ↓
call the already-qualified Phase 1 factory
  ↓
controlled review-package delivery
```

不要让 Phase 2 重新拥有视频生成逻辑。
