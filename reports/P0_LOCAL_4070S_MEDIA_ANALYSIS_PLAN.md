# P0：本地 RTX 4070 SUPER 媒体分析计划

本轮只做路线设计，不安装模型、不下载节点、不运行重 GPU 任务。

## 音频

`video-factory-audio-analyzer` 只接收 `receipt_path`、`stored_path`、`job_id`、`analysis_policy`。读取 stored copy 后：

1. 用 `ffprobe`/`ffmpeg` 校验音频流并标准化到隔离 job 目录；
2. 默认使用 faster-whisper CUDA，开启 VAD 和词级时间戳；
3. CUDA 不可用、显存不足或锁不可得时，进入明确的 CPU fallback 或 `audio_model_unavailable`，不能并行抢占 GPU。

现有 `audio-subtitle-engine` 明确了 CUDA 主线和 ffmpeg/ffprobe 依赖，但没有写出 CPU fallback 和锁协议；这两项是实施前必须补齐的合同。

## 视频

`video-factory-video-analyzer` 的固定顺序：

1. `ffprobe` 读取容器、视频/音频流、时长和编码信息；
2. `ffmpeg` 提取音轨到隔离目录；
3. 按时长和场景变化抽取少量关键帧；
4. 仅把这些安全副本交给本地视觉模型或允许的多模态模型；
5. 结果写入 job 产物和状态，不把原始 inbound path 传出。

AI 视频仍限制为 2–4 秒；不自动安装 custom node、不自动下载模型，模型必须有批准的 hash 和不超过 30 GB 的预算。

## GPU 互斥

4070 SUPER 重任务必须串行：`WHISPER_GPU`、`COMFY_IMAGE`、`COMFY_VIDEO`、`UPSCALE` 任一时刻只允许一个。执行前取得数据库锁或文件锁，释放后才允许下一个任务。

当前仓库的 runbook 写了“一次一个重任务”，但 `pipeline_routes.yaml` 与两项 skill 没有定义共享锁文件路径、schema 或超时回收协议；不能把 skill 顺序误认为真正的互斥。下一阶段要先确定统一锁合同，再做 GPU smoke。

## 输出失败码

- `audio_model_unavailable`
- `video_probe_failed`
- `video_frame_extract_failed`
- `gpu_lock_unavailable`
- `multimodal_model_unavailable`

失败时保留 receipt、隔离副本和可审计错误，不回读原始 inbound，也不自动切换到纯文本入口模型。
