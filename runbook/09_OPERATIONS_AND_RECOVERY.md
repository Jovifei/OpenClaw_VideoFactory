# 09 — 日常运维与恢复

开机检查Gateway、Cron和runtime gate。ComfyUI按需启动。

每日：08:30候选→12:00制作→飞书交付→用户发布→写published history。

支持暂停/恢复/取消今天；维护时禁用Cron，恢复前检查未完成任务。

日志按job保存并脱敏，含事件、命令摘要、GPU指标、交付和质量。

默认保留：参考原视频30天、中间缓存14天、成片/报告90天、发布历史长期；只清理项目内明确目录。

备份数据库、config、skills、schemas、published history、status和versions，不把密钥纳入普通备份。

OpenClaw/lark-cli/ComfyUI/节点/模型/剪映/CUDA不自动滚动更新；更新走分支、备份、fixture、通过、生产、回滚。

紧急停止：禁用Cron→停止Gateway→保留数据库和日志，禁止先删现场。
