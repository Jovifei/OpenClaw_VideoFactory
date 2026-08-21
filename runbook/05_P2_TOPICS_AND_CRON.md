# 05 — Phase 2 飞书选题、受控交付与 Cron

> 本 Runbook 不属于当前 Phase 1。本地视频工厂通过人工审阅后，且 Jovi 单独授权
> 飞书接入时，才可以按此执行。

## Phase 2 前置门

1. Phase 1 的主题模式与本地参考视频主题模式均已有可审阅原创 MP4 证据；
2. 历史 P0 飞书安全门重新归入本阶段：实时 Schema、allowlist、单消费者、
   receipt/MIME/SHA 隔离、两消息分析意图、受控幂等出站与恢复；
3. OpenClaw、Gateway、Binding、lark-cli、凭据、真实出站和 Cron 的每项变更均有
   单独授权、回滚和可审计证据；
4. 任何一项失败时只保留本地 Phase 1 审阅包，不发送或自动发布。

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

Phase 2 验收：飞书安全前置、候选一次、自然语言选择、低分暂停、每天最多一条、重启/重试不重复、配额/AI 门禁/幂等生效。运行 Phase 2 gate；通过前禁止注册生产 Cron 或自动发布。
