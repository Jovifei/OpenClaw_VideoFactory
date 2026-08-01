# 05 — P2 选题、飞书与Cron

读取account_columns/topic_rules/mascot_usage。最近28条：嵌入式≥65%，AI≤25%，社区品牌约10%，同栏目最多连续2条。

数据源只读`config/content_sources.yaml` enabled白名单，可用Git提交、README、Bug、月报、笔记、评论和公开资料，禁止扫描敏感目录。

08:30：历史→配额→至少10候选→去重→事实→画面→评分→发3–5个。候选卡写排名、栏目、主题、钩子、结论、结构、画面、角色动作、时长、来源、风险和分数。

飞书命令：选1、做第2个、做FreeRTOS那个、第3个压到30秒、取消今天、暂停、恢复、重新生成、状态。解析和message_id去重写审计日志。

12:00：已选择则制作；未选择只有总分≥80、来源/配额/去重/fallback通过才自动选最高分并立即制作；否则暂停。没有固定10分钟等待，但重GPU/渲染前取消应尽快停止。

P2_READY后才运行：

```powershell
powershell -File .\scripts\06_register_cron.ps1 -TargetKind direct -TargetId "ou_xxx"
```

先dry-run，再`-Apply`。注册后`cron list`、`cron show`、`cron run --wait`、`cron runs`。

P2验收：候选一次、自然语言选择、低分暂停、每天最多一条、重启/重试不重复、配额/AI门禁/幂等生效。运行P2 gate。
