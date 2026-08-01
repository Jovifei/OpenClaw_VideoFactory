# P0-SINGLE-GROUP-MEDIA-ROUTER-006：架构审核

状态：离线设计审核完成；未修改生产配置，未重启 Gateway。

## 结论

目标拓扑在 OpenClaw 2026.7.1 的配置模型中可以表达，但当前生产状态还不能宣称已满足。需要一次经过批准的生产配置/工具策略变更，才能把 `video-factory` 从当前宽工具面收敛为纯文本入口。这个必要变更不等同于修改 OpenClaw 核心源码，也不需要新增 Binding 或消费者。

## 保留的拓扑

```text
现有 VideoFactory 飞书群
        │
        ▼
现有 zhongshu → 现有 core Binding → video-factory（唯一消费者）
        │
        ├─ 普通文本：同一 session 连续回复
        └─ 附件：只接收 Channel 元数据 → ingest_attachment
                         │
                         └─ receipt 成功后由内部 Agent 分派
                            image / audio / video analyzer
```

内部分析 Agent 不注册飞书 Binding，不订阅群，不直接回复群；入口 Agent 负责把结果回送原群。

## 审计事实

1. 当前 live agent 数为 14、Binding 数为 14；`video-factory` 只有一个现有 Binding。目标群的结构化 session 前缀为 `agent:video-factory:feishu:group:<target-id>`，报告只保留结构，不记录真实群标识；最小可用 `keyPrefix` 必须覆盖完整前缀。
2. `agents.defaults.model` 和 durable `video-factory` 当前仍是 `xiaomimimo/mimo-v2.5`；它的输入能力包含 `text,image`。目标群 session 曾有 `mimo-v2.5-pro` 的 auto override，但这是 session 状态，不是可依赖的持久配置。
3. `mimo-v2.5-pro` 的模型元数据为 `input: [text]`，适合作为入口纯文本模型。
4. 目标群 session 当前拥有 52 项工具，包含 `exec`、`image`、`image_generate`、`video_generate` 等直接媒体/文件能力，sandbox 为 off；因此当前入口不满足“只允许确定性入库”。
5. live `tools.media.image/audio/video` 和 `agents.defaults.imageModel` 均未设置。Schema 支持三类 media scope，但“支持配置”不是“当前已经禁用”。
6. OpenClaw 核心顺序为 `applyMediaUnderstandingIfNeeded` 先执行，再进入 pre-agent message hook。提示词或记忆无法撤销已经发生的 pre-reply media understanding。

## 可行性边界

官方 media-understanding 文档规定：scope 按第一条命中规则生效；text-only 主模型时附件保留为 `media://inbound/*` 引用；原生视觉主模型可能直接接收原始图片。由此：

- 对目标群同时配置 image/audio/video `scope` deny，可以阻止该群的自动媒体理解；本轮没有把它写入生产配置，因此尚未做 live 证明。
- 入口必须使用 `xiaomimimo/mimo-v2.5-pro`，且不能只靠提示词。现有工具面必须通过 agent tool policy 收紧，移除 `exec`、`image`、`image_generate`、`video_generate`、文件读写和其他媒体工具，只保留确定性 `ingest_attachment` 与受控内部派发接口。
- 入口模型最多看到普通文本、附件元数据或 `media://inbound/*` 引用；它不应获得原始像素读取工具。scope deny 是流水线闸门，tool deny 是第二道权限闸门，二者不能互相替代。
- 当前仓库已经有隔离入库脚本并通过 32/32 回归；但脚本是单文件、接收已解析 `SourcePath`，还不是 Gateway 可调用的 `ingest_attachment` 工具。

## 不进入本轮

不修改 OpenClaw 核心源码、`openclaw.json`、Binding、消费者数量、模型安装、Gateway 状态或 P1。只有在用户批准下一阶段的精确配置和工具写入范围后，才可做 runtime smoke。
