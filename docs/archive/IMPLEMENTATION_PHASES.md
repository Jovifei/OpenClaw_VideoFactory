# 实施阶段（Phase 1 本地优先）

本文件的产品阶段以 [`PRODUCT_PHASES.md`](../PRODUCT_PHASES.md) 为准。历史 `P0`–`P5`
仍可用于定位已有报告与代码，但不再决定产品的交付顺序。

## PACKAGE

交付包结构、配置、Skill、密钥扫描、SHA 和文档渲染。PACKAGE 通过不代表任何
视频工厂或飞书能力已经通过。

## Phase 1 — 本地确定性视频工厂

- 输入为 Jovi 手工主题、Jovi 提供的本地参考视频，或 Jovi 明确授权的公开主题研究；
- 本地参考视频只做主题/结构/通用表达线索分析，原始文件只读，后续内容必须原创；
- 建立 job-scoped 输入说明、事实简报、脚本、分镜、素材清单、音频、字幕、
  render manifest 和质量报告；
- 固定 JSON 到可解码 1080x1920 MP4，随后逐步加入 TTS、字幕、Remotion 模板、
  小粉飞猪和 CPU/NVENC 回退；
- 至少证明主题模式与本地参考视频主题模式各一条可审阅成片；
- 交付为本地 `final_master.mp4` 和人工审阅包，不发送飞书。

Phase 1 禁止飞书、OpenClaw/Gateway、lark-cli、Cron、自动选题、自动上传、
自动发布、未批准模型下载和第三方平台抓取。

## Phase 1.5 Video Use Adapter Pilot（可选）

- 仅在基础本地成片稳定后评估用户授权的已有素材剪辑；
- 可提炼 packed transcript、EDL、词边界切点、转录缓存和最多三轮自评修复；
- 适配 Windows、本地字幕安全区与 NVENC/CPU 回退；
- 原始素材只读，失败不影响 Phase 2 或主题生成主链。

## Phase 2 — 飞书选题与自动化

先把历史 `P0` 迁入本阶段并通过其安全门：OpenClaw 实时 Schema、allowlist、
飞书单消费者、隔离入站、显式两消息分析意图、受控 lark-cli 幂等出站与恢复证据。

随后实现：

- 白名单来源、历史、28 条配额、候选、去重、评分和事实来源；
- 08:30 生成至少 10 个原始候选并发送 3–5 张飞书候选卡；
- 飞书自然语言选择；未选择时仅在所有门通过后执行 12:00 fallback；
- 取消、恢复、重试、每天最多一条和受控飞书审阅包交付；
- 非定时验证与 Phase 2 Gate 后，才可注册正式 Cron 和进行七天试运行。

## Phase 3 — GPU 与质量增强

- 4070S 串行队列；
- faster-whisper CUDA / CPU 回退；
- ComfyUI 白名单 workflow、模型预算与哈希；
- OOM/超时回退、Real-ESRGAN、NVENC 指标。

## Phase 4 — 高级参考视频原创再创作

Phase 1 的参考视频“主题提取”不等于本阶段。这里才加入多源转录、切镜、关键帧、
风格 token、复杂字幕/节奏与原创性检查；不复用原音、水印、连续镜头或完整文案。

## Phase 4.5 OpenMontage Sidecar Pilot（可选）

- 仅在 Phase 4 稳定且获独立实验环境与许可证批准后进行；
- 不接生产 Cron、生产 Secret 或主状态库；
- 失败不影响后续阶段。

## Phase 5 — 剪映草稿

- 兼容性调查；
- 选择一个后端生成可编辑草稿；
- 失败不影响 MP4，也不自动导出或发布。
