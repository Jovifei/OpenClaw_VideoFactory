# 产品阶段验收矩阵（2026-08-14 对齐）

历史 `P0`–`P5` 证据仍可追溯；当前产品顺序以 [`docs/PRODUCT_PHASES.md`](../../docs/PRODUCT_PHASES.md) 为准。

| 阶段 | 关键需求 | 必须证据 | 阻塞 |
|---|---|---|---|
| PACKAGE | 扁平目录、Skill、无密钥、SHA、文档完整 | `reports/package_release_validation.json` | 是 |
| Phase 1 输入 | Jovi 主题、本地参考视频、或明确授权公开研究 | 输入说明、来源/权利边界、只读参考 digest | 是 |
| Phase 1 成片 | 原创脚本/分镜、TTS、字幕、MP4、质量报告 | 主题 fixture + 本地参考视频 fixture、可解码 MP4、WAV/SRT、人工视听复核 | 是 |
| Phase 1 状态 | 本地 job 工件、取消/重试/重启恢复、CPU 回退 | job events、失败快照、render manifest | 是 |
| Phase 1 边界 | 不使用飞书、OpenClaw、lark-cli、Cron、自动发布 | 命令/产物边界审计 | 是 |
| Phase 2 飞书安全 | 历史 P0：OpenClaw、飞书、lark-cli、Direct Codex CLI、权限 | Gateway/doctor、单消费者、TXT/PNG/MP4 安全入站、两消息意图、四类受控出站与幂等、无 Cron | 是 |
| Phase 2 自动化 | 候选、选择、12:00 兜底、恢复 | 高分/低分/取消/重复/Cron run history | 是 |
| Phase 2 内容门 | 栏目配额和 AI 门禁 | 最近 28 条比例、来源和日期报告 | 是 |
| Phase 3 | GPU 有效使用与回退 | CUDA、显存、ComfyUI、NVENC、OOM/CPU/静态图回退日志 | 是 |
| Phase 4 | 高级参考视频原创改编 | 三类分析、新视频、人工原创检查 | 是 |
| Phase 5 | 剪映草稿 | 本机可开；失败不阻塞 MP4 | 可选 |
| PRODUCTION | 七天试运行 | 完成率≥90%、重复 0、人工≤15 分钟 | 是 |
| 发布 | 抖音 | Jovi 人工发布 | 非系统自动化 |
