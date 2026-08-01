# P0-SINGLE-GROUP-MEDIA-ROUTER-006：安全边界

## 当前卡点

当前链路存在两个独立风险：

1. `tools.media.*` scope 尚未在 live 配置中设置，默认媒体流水线仍可能在 Agent 提示词生效前运行。
2. `video-factory` 当前 session 工具面为 52 项、sandbox off，包含直接文件/媒体能力；即使入口模型是 text-only，也不能靠模型自觉阻止读取或执行。

因此本轮不能报告“生产已实现”。必须先批准精确的 scope 和 per-agent tool policy 变更，再做最小 runtime smoke。

## 两道闸门

```text
Channel metadata
   │
   ├─ media scope deny（目标群，image/audio/video）
   │       └─ 不执行 pre-reply media understanding
   │
   └─ text-only router + tool allowlist
           └─ 只可调用 ingest_attachment / 受控内部 dispatch
                         │
                         ▼
                   quarantine receipt
                         │
                         ▼
              stored copy-only analyzer
```

scope deny 防止核心自动分析；tool allowlist 防止入口 Agent 绕过入库。任一闸门缺失都不能宣称满足需求。

## 入库安全要求

- `MediaPath` 只能由 Channel 适配层提供，不能由模型拼接、改写或从文件名推导。
- 入库前校验 approved inbound root、reparse escape、MIME/扩展名/魔数、大小和安全文件名。
- 复制后立即计算 SHA-256，receipt 与副本哈希必须相同；重复 `message_id + hash` 必须幂等。
- receipt 初始固定 `content_parsed=false`、`quarantined=true`；分析完成后才由受控状态机改变解析状态。
- 原始 inbound 路径不进入任何 analyzer 参数；analyzer 只能读取隔离副本。
- TXT 默认仍隔离，不因“可读文本”而跳过 receipt。

## 失败闭环

- scope 不命中：停止并记录，不隐式回退到允许。
- 入库失败：不创建分析 job，不调用任何 analyzer。
- receipt 缺字段、哈希不一致或隔离标志错误：fail closed。
- 多模态服务不可用：返回 `multimodal_model_unavailable`，不得回退到 `mimo-v2.5-pro`。
- GPU 锁不可得：排队或失败，不并发抢占 4070 SUPER。
- 后置分析失败：保留 receipt 和隔离副本，不能重新读取原始 inbound。

## 拓扑不变量

- 飞书群仍只有一个消费者和一个现有 core Binding。
- 后置 Agent 仅通过内部 job 调用，不订阅飞书、不主动向群发消息。
- 不新增群、不改 OAuth、不改 Runtime、不重启 Gateway。
- 所有报告、日志和诊断均不得写入真实群标识、file_key、URL、base64 或密钥。
