# 03 — Skills 与外部仓库

Updated: 2026-09-05

`skills/` 位于 workspace 根。端到端视频任务先读取：

1. `docs/CURRENT_ARCHITECTURE.md`；
2. `skills/video-production-chain/SKILL.md`；
3. 当前阶段对应的具体 Skill。

外部仓库统一放 `external/`（仅本地，需要时）；接入前检查 LICENSE、README、Skill、安装脚本、依赖锁、权限和网络行为，并在 `reports/external/` 记录 review。不能因为“开源”就自动下载模型、节点或执行安装脚本。

## VideoClaw

仓库：`HITsz-TMG/VideoClaw`

许可证：MIT。

当前用途：**架构方法参考，不 vendoring backend**。

重点借鉴：

- idea → multi-stage artifact；
- 每阶段资产可查看/确认/修改；
- pipeline runner / event / storage 的职责拆分；
- 用户关键节点介入；
- failure/resume 明确；
- final editing 之前保留中间成果。

禁止：

- 复制它的第二套 backend/frontend/state DB 作为本项目主控；
- 把它的云视频 Provider 设成 Phase 1 必需项；
- 替换现有 SQLite、Storyboard、Timeline、Renderer 和 Phase Gate。

## 小粉飞猪

规范仓库：

```powershell
git clone https://github.com/Jovifei/ian-fenzhu-illustrations .\external\ian-fenzhu-illustrations
git -C .\external\ian-fenzhu-illustrations rev-parse HEAD
```

许可证：MIT。

该仓库提供 style DNA/persona/composition 参考，不等于 Jovi 的最终原始生产资产包。

当前 personal-IP policy：

- 默认 off；
- Jovi 当前 brief 显式 opt-in 才启用；
- 启用必须使用 Jovi-owned original asset pack + receipt；
- 仓库自制 PNG/SVG、AI 临时图、上游样例 JPG 都不能代替最终原始 IP；
- mascot-required brief 缺资产时 fail closed；普通技术视频可以无 mascot 继续；
- 角色不能遮挡技术图、代码、公式、字幕。

权威说明：`docs/PINK_PIG_CURRENT_POLICY.md` 与 `config/mascot_usage.yaml`。

## Remotion

仓库/Skill：`remotion-dev/remotion`、`remotion-dev/skills`。

当前是实际使用的 deterministic visual engine，不再只是候选。

规则：

- 新建/修改 Composition 前读取当前 Remotion Skill；
- 时间和动画使用真实 frame/timing 合同；
- 语音相关重点动画优先绑定 measured speech cues；
- 不把 Remotion 当作 Job DB 或事实审核器；
- 竖屏/横屏由当前 brief/render profile 决定。

## Agents365-ai/video-podcast-maker

当前许可证：CC BY-NC 4.0。

只吸收方法：

- research；
- script；
- TTS/timing；
- Remotion component；
- validation；
- Skill 内 references/scripts/templates 的组织方式。

因为包含 NonCommercial 条件，未来产品化前不要直接复制其代码/模板进入商业链；优先 clean-room 自行实现思路。

## PySceneDetect / faster-whisper

Phase 1 reference path：

- PySceneDetect：scene boundary/pace；
- faster-whisper：只在 reference audio 需要 ASR 且本地 approved cache 存在时使用；
- 自己生成的 TTS 视频不需要为了字幕再次跑 ASR；
- 缺模型时 fail-soft 为 `unavailable`，不联网下载。

## ComfyUI MCP

Phase 3 候选。

只允许：

- `127.0.0.1`；
- approved workflow；
- 已批准模型；
- 创意背景/封面/B-roll 等非事实画面。

无人值守禁装节点/模型。技术事实图（电路、寄存器、代码、协议帧、公式）优先 deterministic visual。

## 剪映

当前选定：`luoluoluo22/jianying-editor-skill`，MIT。

它是**可选编辑后端**，不是 Phase 1 核心 MP4 Gate 的唯一成功路径。

当前实验链已验证：

- E-drive 新草稿；
- visual-only MP4；
- VoiceOver track；
- native Subtitles track；
- 自动导出关闭；
- Jovi 手工试听/查看/导出。

同一 Job 不启用第二编辑后端。

外部候选：

- `Hommy-master/capcut-mate`：未来隔离适配器；
- `hey-jian-wei/jianying-mcp`：研究候选；
- 未完成许可证/版本/权限/recovery review 前不能切换 production backend。

## OpenMontage / OpenReels / Auto-Editor / WhisperX / Real-ESRGAN

当前均不是 Phase 1 Gate 依赖。

- OpenMontage：借 approval/backlot/self-check 方法；历史记录为 AGPL 路线，不 vendoring；
- OpenReels：借 Director score/archetype/retry 思路；
- Auto-Editor：长素材预剪候选；
- WhisperX：Phase 3/4 高精度 alignment/diarization；
- Real-ESRGAN：非文字图像放大候选。

## Phase 2 才启用：OpenClaw / larksuite CLI

Phase 1 不接飞书。

只有 `PHASE1_READY` 后，Phase 2 才重新启用：

- OpenClaw long-running orchestration；
- larksuite/cli；
- 飞书候选卡；
- user selection；
- qualified fallback；
- controlled delivery；
- 非定时验证通过后再注册 Cron。

历史 P0 飞书证据保留，但不要在 Phase 1 重跑。
