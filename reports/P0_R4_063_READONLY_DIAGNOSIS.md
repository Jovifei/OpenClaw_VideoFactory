# P0-R4-063 只读诊断

结果：`DIAGNOSED_VIDEO_INPUT_WITHOUT_AUDIO_STREAM`

本轮实际入站 receipt 是 `mp4` / `video/mp4`，Ticket 与请求因此正确选择 `analyze_video`。它不是 WAV 被误判：现有 WAV 入库测试 42/42 通过，Ticket 路由测试 3/3 通过。

隔离 MP4 的脱敏探测显示：`ffprobe` 成功、时长为正、有视频流、没有音频流、无写入抽帧成功，而无写入音频提取以 `missing_required_stream` 失败。当前 `analyzer_mcp.py` 将抽帧失败和音频提取失败都映射为 `video_frame_extract_failed`，导致无音轨视频在视觉分析前终止。

`douyin_to_obsidian` 的既有视频流程会捕获提音频失败、跳过 ASR，并继续可选视觉处理；但其脚本含硬编码路径、配置与 Obsidian 写入，不能直接复制到 VideoFactory。

建议的最小修复：视频已成功探测/抽帧时，将无音轨单独标为 `no_audio_stream`，以空转录继续现有视觉路径，并用现有静音 MP4 fixture 增加回归测试。未修改源码、配置、Gateway/Core、Git 或阶段状态。
