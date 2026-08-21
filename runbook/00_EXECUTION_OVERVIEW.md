# 00 — 执行总览（Phase 1 本地优先）

## 阶段依赖

```text
PACKAGE → Phase 1 Local Video Factory → Phase 2 Feishu Automation → Phase 3 → Phase 4 → Phase 5 → PRODUCTION
                    └→ Phase 1.5 Video Use Pilot（可选）          └→ Phase 4.5 OpenMontage（可选）
```

- **Phase 1（当前）**：Jovi 给主题、本地参考视频，或明确授权公开主题研究；
  Codex 在本地生成原创、可审阅 MP4。无飞书、OpenClaw、lark-cli 或 Cron。
- **Phase 1.5**：可选的用户授权已有素材剪辑试点，不阻塞主路线。
- **Phase 2**：历史 P0 飞书安全门 + 08:30 候选、飞书选择、12:00 合格兜底、
  受控交付和 Cron。
- **Phase 3**：4070S、ComfyUI、Whisper、NVENC。
- **Phase 4**：高级参考视频原创再创作；不同于 Phase 1 的基础主题提取。
- **Phase 5**：可选剪映草稿。
- **PRODUCTION**：Phase 2 后七天试运行达标的长期运营，不是自动抖音发布。

历史 `P0`–`P5` 只用于追踪既有报告和兼容性工件。历史 P0 未完成不阻塞 Phase 1，
但仍是 Phase 2 的安全前置。

## 当前允许范围

Phase 1 只允许：本地输入、主题/事实简报、原创脚本/分镜、TTS/字幕、
Remotion/FFmpeg、质量报告、人工审阅和本地失败回退。

Phase 1 禁止：飞书/Gateway/Binding/OAuth/lark-cli/Cron、自动选题、自动上传、
自动发布、未批准的模型/依赖下载和受限平台抓取。

Phase 1 的最低路线是 CPU 兼容的本地 TTS、Remotion/FFmpeg 与人工审阅。远程 TTS、AI Director
或其他外部 Provider 不是默认授权；任何接入均需单独获批范围与预检。ComfyUI、NVENC 和 GPU
只可作为已有获批组件的可选增强，不能下载模型/节点或成为本阶段通过条件。若参考视频分析将复制
镜头顺序、节拍或可识别包装，应停止并转入 Phase 4 另行审查。

## Git 与证据

推荐分支：`phase/1-local-video-factory`、`phase/2-feishu-automation`、
`phase/3-gpu`、`phase/4-reference-video`、`phase/5-jianying`。

每阶段必须记录：任务 ID、日期、Git commit、版本、命令、退出码、测试、日志、
产物、限制、回滚和用户动作。禁止只写“完成”。本轮文档对齐本身不是任何阶段通过证据。

## 用户介入点

Phase 1：公开主题研究授权、参考视频权利/来源不清、模型下载、许可证疑问、
超预算和抖音发布必须等待 Jovi。

Phase 2：飞书授权、管理员权限、OpenClaw 升级、Gateway/Binding/Cron、
真实出站和权限扩大必须等待 Jovi。Codex Plugin OAuth 仍为可选研究，不作为
Phase 1 或 Phase 2 的默认门禁。

## 回退链

```text
研究失败→要求 Jovi 提供主题/来源
参考视频解析失败→只走主题模式或停止
TTS失败→备用 TTS
Whisper CUDA失败→CPU
ComfyUI视频失败→静态图
ComfyUI图片失败→SVG/Remotion
NVENC失败→CPU编码
角色失败→静态签名/不主动出场
飞书（仅 Phase 2）失败→保留本地审阅包，不重试发布
```
