# 10 — 最终验收

## 静态

结构正确；YAML/JSON/JSON5有效；Skill有效；无密钥；版本锁完整；文档配置一致。

## P0

OpenClaw版本满足飞书；Schema捕获；workspace正确；OpenClaw Default Runtime允许；Direct Codex CLI 只读/受控写 smoke；飞书单消费者；TXT/PNG/MP4真实入站和安全入库；lark-cli四类真实出站与幂等；原有Agent/Binding回归；无VideoFactory正式Cron；本地Skill可见。OpenClaw Codex Plugin OAuth为`deferred_optional_not_blocking`。

## P1

三fixture生成母版/预览；字幕音频封面文案报告完整；幂等、重启恢复、CPU回退和角色一致。

## P2

08:30候选；飞书选择；12:00兜底；低分暂停；每日一条；28条配额；AI来源；Cron history。

## P3

CUDA字幕、Comfy白名单、预算、OOM、NVENC、无GPU并发。

## P4

安全入站、三参考视频、原创检查、无原音/水印/连续镜头。

## P5

草稿可开、失败不阻塞MP4、不自动发布。

## 七天

完成率≥90%；重复0；高风险事实错误0；人工修改中位≤15分钟；GPU整单失败0；合格候选兜底成功≥95%。

最后运行production gate，只有全部必需阶段和七天报告通过才创建PRODUCTION_READY。抖音仍人工发布。
