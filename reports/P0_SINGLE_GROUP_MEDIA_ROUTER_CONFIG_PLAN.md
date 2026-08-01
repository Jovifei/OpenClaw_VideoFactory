# P0-SINGLE-GROUP-MEDIA-ROUTER-006：配置审计与待批准计划

本文件是离线计划，不是可直接粘贴执行的生产补丁。生产 `C:\Users\Admin\.openclaw\openclaw.json` 的基线 SHA-256 为 `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`，本轮保持不变。

## 目标配置语义

### 1. 目标群媒体理解 scope

三类能力分别配置同一条最小规则，规则顺序置于所有默认规则之前：

```json5
{
  tools: {
    media: {
      image: {
        scope: { rules: [{ action: "deny", match: {
          channel: "feishu", chatType: "group",
          keyPrefix: "agent:video-factory:feishu:group:<target-id>"
        }}], default: "allow" }
      },
      audio: { /* 同上 */ },
      video: { /* 同上 */ }
    }
  }
}
```

`<target-id>` 只能从 live session 结构化输出得到，不能从聊天正文猜测；真实标识不写入报告。scope 是第一道闸门，不能用 Agent 记忆替代。

### 2. 入口 Agent

待批准的 `video-factory` 语义：

- durable model：`xiaomimimo/mimo-v2.5-pro`；
- tool policy：只允许确定性 `ingest_attachment` 和受控内部 dispatch；
- deny：`exec`、`process`、`read`、`write`、`edit`、`apply_patch`、`image`、`image_generate`、`video_generate`、`music_generate`、`tts`、网页/文件/媒体读取及 Gateway 管理工具；
- sandbox 和工作区读权限不能作为唯一安全边界，必须同时采用 tool allowlist；
- 不设置全局 `agents.defaults.imageModel`，避免影响其他 13 个 Agent；图片模型只属于后置 image/video analyzer。

当前 schema 已提供 per-agent `allow`/`deny`/`profile` 结构，但 live `video-factory` 尚未采用上述收敛策略；这正是尚未达到设计就绪的生产差距。

### 3. `ingest_attachment` 合同

工具不得接收模型自由构造的路径。调用参数由 Channel 适配层生成并绑定到当前消息，只允许：`message_id`、附件序号/原始文件名、Channel 提供的真实 `MediaPath`/`MediaPaths`、MIME/type 和幂等键。工具内部必须再次做路径根约束、reparse 检查、签名/MIME/扩展名一致性、大小上限、哈希和 receipt 写入。

成功输出至少包含：

`message_id`、`stored_path`、`MIME`、`detected_kind`、`size_bytes`、`SHA-256`、`receipt_path`、`content_parsed=false`、`quarantined=true`、`status`。

当前 `scripts/07_ingest_inbound_media.ps1` 已覆盖大部分确定性校验并通过 32/32；它仍需一个受控适配层，才能成为 Agent 工具，而不是把脚本路径暴露给入口 Agent。

### 4. 后置 dispatch

只有 receipt 存在、`content_parsed=false`、`quarantined=true` 且 stored copy SHA-256 与 receipt 一致时，才允许创建内部 job：

| detected_kind | 内部 Agent | 允许输入 |
|---|---|---|
| txt | 保持隔离；只有明确任务才解析 | receipt_path、stored_path、job_id、analysis_policy |
| png/jpg | `video-factory-image-analyzer` | 同上 |
| audio | `video-factory-audio-analyzer` | 同上 |
| mp4 | `video-factory-video-analyzer` | 同上 |

严禁把原始 `MediaPath`、URL、base64 或 `file_key` 传给后置 Agent。后置 Agent 不注册飞书 Binding。

## 暂不执行的验证

生产 scope 命中、入口模型实际 payload、tool deny 生效和原群回送必须在下一次用户批准的 runtime smoke 中验证。当前只做离线契约测试，不能把模拟结果写成 Gateway 证据。
