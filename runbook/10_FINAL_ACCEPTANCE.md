# 10 — 最终验收（Phase 1 本地优先）

## 静态

结构正确；YAML/JSON/JSON5 有效；Skill 有效；无密钥；版本锁完整；文档、
`PROJECT_STATUS.yaml` 与 [`docs/PRODUCT_PHASES.md`](../docs/PRODUCT_PHASES.md) 一致。

## Phase 1 — 本地视频工厂

- Jovi 给主题的模式产生原创、可解码的竖屏母版；
- Jovi 给本地参考视频的模式产生主题/结构报告和原创、可解码的竖屏母版；
- 明确授权公开研究时，来源、日期和事实边界可追溯；
- 脚本、分镜、音频、字幕、素材清单、render manifest、质量报告和人工审阅清单完整；
- 字幕安全、音轨、首屏、黑屏、角色遮挡、CPU/NVENC 回退和失败快照通过；
- 无飞书、OpenClaw/Gateway、lark-cli、Cron、自动上传或自动发布动作。

## Phase 2 — 飞书自动化

- 历史 P0 飞书安全门通过：OpenClaw Schema、allowlist、单消费者、真实安全入站、
  receipt/MIME/SHA、两消息意图、受控 lark-cli 出站与幂等；
- 08:30 候选、飞书选择、12:00 合格兜底、低分暂停、每日一条、恢复与取消可验证；
- 正式 Cron 只在非定时验证和 Phase 2 Gate 后注册；
- 飞书交付只发送审阅包，抖音仍由 Jovi 人工发布。

## Phase 3

CUDA 字幕、Comfy 白名单、预算、OOM、NVENC、无 GPU 并发。

## Phase 4

高级参考视频的安全入站、三类分析、原创检查与无原音/水印/连续原镜头。它补充而不替代
Phase 1 的基础参考视频主题提取。

## Phase 5

草稿可开、失败不阻塞 MP4、不自动发布。

## 七天生产试运行

仅在 Phase 2 通过后评估：完成率≥90%；重复 0；高风险事实错误 0；人工修改中位≤15 分钟；
GPU 整单失败 0；合格候选兜底成功≥95%。

最后运行 production gate。只有 Phase 1、Phase 2、所需增强阶段和七天报告均通过，
才能创建 `PRODUCTION_READY`；抖音仍人工发布。
