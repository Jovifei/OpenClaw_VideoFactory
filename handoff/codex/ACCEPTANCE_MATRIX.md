# V2.5 验收矩阵

| 阶段 | 关键需求 | 必须证据 | 阻塞 |
|---|---|---|---|
| PACKAGE | 扁平目录、14个Skill、无密钥、SHA、文档完整 | `reports/package_release_validation.json` | 是 |
| P0 | OpenClaw、飞书、lark-cli、Direct Codex CLI、权限 | Gateway/doctor、单消费者、TXT/PNG/MP4安全入站、四类出站与幂等、CLI read/write smoke、回归、无VideoFactory Cron | 是 |
| P0可选项 | OpenClaw Codex Plugin OAuth | `deferred_optional_not_blocking`；`/codex status`、`/codex models`和OpenAI Codex Runtime不参与P0 | 否 |
| P1-A | SQLite与CLI，不做视频 | 幂等、取消、重启恢复 | 是 |
| P1-B/C | 固定JSON 10秒MP4，再加TTS和字幕 | 可解码MP4、WAV、SRT | 是 |
| P1-D/E/F/G | 模板逐个增加、确定性小粉飞猪、三个fixture、最后接飞书 | 3条fixture job、NVENC/CPU、质量报告和幂等交付 | 是 |
| P1 | 状态恢复和幂等 | Gateway重启、同job重跑、取消/重试 | 是 |
| P1/P2 | 小粉飞猪一致性 | 角色DNA、遮挡、失败降级 | 是 |
| P2 | 候选、选择、12:00兜底 | 高分/低分/取消/重复/Cron run history | 是 |
| P2 | 栏目配额和AI门禁 | 最近28条比例、来源和日期报告 | 是 |
| P3 | GPU有效使用 | CUDA、显存、ComfyUI、NVENC日志 | 是 |
| P3 | GPU故障回退 | OOM注入和CPU/静态图回退 | 是 |
| P4 | 参考视频原创改编 | 3条分析、新视频和人工原创检查 | 是 |
| P5 | 剪映草稿 | 本机可开；失败不阻塞MP4 | 可选 |
| PRODUCTION | 七天试运行 | 完成率≥90%、重复0、人工≤15分钟 | 是 |
| 发布 | 抖音 | 用户人工发布 | 非系统自动化 |
