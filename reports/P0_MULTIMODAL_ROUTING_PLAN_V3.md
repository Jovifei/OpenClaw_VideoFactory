# P0：多模态路由计划 V3

## 模型能力边界

| 角色 | 模型 | 输入 | 允许用途 |
|---|---|---|---|
| `video-factory-router` | `xiaomimimo/mimo-v2.5-pro` | text | 普通文本、路由、状态与原群回复 |
| `video-factory-image-analyzer` | `xiaomimimo/mimo-v2.5` 或批准的本地视觉模型 | text + image | 读取隔离图片副本 |
| `video-factory-audio-analyzer` | faster-whisper CUDA/CPU | audio | 读取隔离音频副本 |
| `video-factory-video-analyzer` | ffprobe/ffmpeg + 批准多模态模型 | text + image/audio-derived artifacts | 读取隔离视频副本 |

`mimo-v2.5-pro` 是纯文本入口；`mimo-v2.5` 是多模态。不要把二者作为无条件 fallback 链。

## 路由状态机

```text
receipt 校验
   ├─ 失败 → ingest_failed / 不创建分析 job
   └─ 成功
       ├─ image → image-analyzer
       ├─ audio → audio-analyzer
       └─ video → video-analyzer
```

多模态服务失败时，只允许尝试另一种已批准的多模态后端（例如本地 Qwen-VL）；所有多模态后端都不可用时返回 `multimodal_model_unavailable`。禁止回退到 `mimo-v2.5-pro`，因为它不能理解图像像素。

## 安全输入合同

后置 Agent 只接受 `receipt_path`、`stored_path`、`job_id`、`analysis_policy`。它不得接受原始 `MediaPath`、URL、base64、Feishu `file_key` 或未经 receipt 的任意路径。所有结果写入内部 job 状态，由入口 Agent 统一回送原群。

## 本轮边界

本轮只固定能力矩阵、失败码和禁止 fallback；不修改模型配置、不安装 Qwen-VL、不调用外部多模态服务、不触发真实媒体任务。
