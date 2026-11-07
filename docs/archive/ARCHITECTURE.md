# 产品架构（Phase 1 本地优先）

本架构以 [`PRODUCT_PHASES.md`](../PRODUCT_PHASES.md) 为准：先交付本地视频成片，
再把成熟的本地工厂接入飞书自动化。历史飞书/P0 设计保留为 Phase 2 技术门，
不是 Phase 1 的入口或前置条件。

## Phase 1 — Local Codex Video Factory

```text
Jovi / Codex 对话或本地目录
  ├─ 手工主题 + 最小来源上下文
  ├─ 用户提供的本地参考视频（只读主题/结构分析）
  └─ Jovi 明确授权的公开主题研究
             │
             ▼
      job-scoped local workspace
  topic/factual brief → script → storyboard → asset selection
             │
             ├─ TTS + captions
             ├─ SVG/HTML/Remotion or deterministic FFmpeg composition
             └─ optional approved local GPU enhancement
             ▼
  final_master.mp4 + captions + render manifest + quality report
             │
             ▼
            Jovi 人工审阅 / 人工发布
```

Phase 1 的 job 工件是本地可追溯状态，不依赖 OpenClaw、飞书、lark-cli、
Gateway 或 Cron。参考视频、字幕、链接和元数据均是不可信输入；仅提取主题、
结构和通用表达线索，并重新创作，不复用原音、水印、连续镜头或完整文案。

## Phase 2 — OpenClaw / Feishu Automation

```text
Feishu / WebChat
      │
      ▼
OpenClaw Gateway
  ├─ Feishu Channel：allowlist、单消费者、两消息分析意图
  ├─ 08:30：来源/配额/去重后发送 3–5 张候选卡
  ├─ 12:00：仅合格时的受控 fallback
  ├─ 取消、重试、恢复、通知与每日幂等
  └─ lark-cli：受控审阅包交付
      │
      ▼
Phase 1 local-video job adapter
      │
      ▼
final_master + Feishu preview + quality report
      │
      ▼
Jovi 人工发布抖音
```

Phase 2 先通过历史 P0 的飞书安全门：隔离 receipt、MIME/SHA 校验、显式
后续回复意图、单消费者、入站/出站幂等与可审计恢复。只有 Phase 1 已有稳定
本地成片，且 Phase 2 的非定时验证通过后，才可以申请 Cron。

## 责任边界

| 领域 | Phase 1 | Phase 2 |
| --- | --- | --- |
| 输入 | 本地主题、用户本地参考视频、明确授权公开研究 | 飞书文字/附件与选题指令 |
| 状态 | job-scoped 本地工件、渲染报告 | OpenClaw 长期调度、日常任务、通知与幂等 |
| 渲染 | `video_factory`、Remotion/FFmpeg、质量门 | 调用已通过的 Phase 1 渲染适配器 |
| 发布 | 本地审阅；Jovi 人工发布 | 飞书审阅包；Jovi 人工发布 |

主渲染不依赖剪映；剪映只在后续 Phase 5 提供可编辑草稿。重 GPU 任务仍需串行，
NVENC 失败回退 CPU；ComfyUI 仅使用已批准的 workflow。

## 可选适配层

- `Phase 1.5 Video Use Adapter Pilot`：只评估用户授权的已有素材智能剪辑，
  读取文本转录和按需视觉检查；不替代 Phase 1 主渲染器或本地工件合同。
- `Phase 4.5 OpenMontage Sidecar Pilot`：仅隔离的创意实验，不接生产 Cron、
  Secret 或主状态库。

两条支线失败都不得阻塞主路线。任何安装、克隆、依赖引入或 Pilot 执行需要
独立授权。
