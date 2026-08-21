# 04 — Phase 1 本地确定性视频 MVP

## 目标

不依赖飞书、OpenClaw、Cron、AI 视频和剪映，严格按本地增量构建确定性视频 MVP。输入可以是 Jovi 给出的主题、Jovi 提供的本地参考视频，或 Jovi 明确授权的公开主题研究。一次只增加一个类别；前一步未验证通过，不进入下一步。

## Phase 1-0 — 输入与原创边界

- 主题模式：记录主题、受众、时长和最小来源上下文；
- 本地参考视频模式：原文件只读，只提取主题、结构、节奏和通用表达线索；
- 授权研究模式：只检索获准的公开资料，记录来源和日期；
- 不抓取受限平台，不使用 Cookie/账号/验证码，不复用原音、水印、连续镜头或完整文案。

三个模式都要产出可追溯的 `topic_brief` / `reference_report`（如适用），然后生成原创脚本与分镜。

## P1-A — SQLite 与 CLI

只实现 `src/factory/` 的 config、db、state、events 和 CLI。

CLI：doctor、create-topic、run、status、retry、cancel。`scripts/factory.py`只作薄包装。

至少：jobs、job_events、artifacts、topic_history、source_records、stage_attempts、locks。

唯一键：job_id、本地输入 digest、阶段尝试号。

状态：NEW→RESEARCHING→SCRIPTING→VOICE→CAPTIONS→ASSETS→RENDERING→QUALITY_CHECK→PENDING_REVIEW；失败/重试/取消都写事件。

验收：幂等、取消和重启恢复测试通过。P1-A 不生成视频。

## P1-B — 固定 JSON 生成 10 秒 MP4

输入固定 `script.json`，只增加一个 Remotion 静态模板，输出 10 秒、1080x1920、30FPS、可解码 MP4。不做网络研究、TTS或字幕。

## P1-C — TTS 与字幕

在 P1-B 固定脚本上增加 AI TTS Provider、WAV、字幕对齐和 SRT。记录版本、音色、分句和发音例外。此阶段不增加新模板。

## P1-D — Remotion 模板逐个增加

每次只增加并验证一套：

1. protocol-frame；
2. code-explainer；
3. flow-diagram；
4. engineering-case。

每套独立验证分辨率、FPS、时长、音轨、字幕安全区和可解码性。

## P1-E — 确定性小粉飞猪

使用固定透明 PNG/SVG：normal、question、warning、thinking、repair、measure、success、ending。禁止每次随机生成角色；先验证遮挡和失败降级。

## P1-F — 三个 Fixture 逐个完成

依次完成，禁止并行堆叠：

1. Modbus；
2. Flash/看门狗；
3. FreeRTOS。

每个 fixture 都要从零、重跑、取消、失败重试和 CPU/NVENC 回退验证。

## P1-G — 本地审阅包与人工检查

只有三个 fixture 都通过后，才增加 cover、`final_master.mp4`、report 和本地人工审阅清单。不得发送飞书；Phase 2 才实现受控交付、消息幂等和 OpenClaw 日常状态。

## Job产物

每个 job 有 job/config/topic/research/sources/reference_report（如适用）/script/storyboard/style/asset_manifest/voice/captions/render_manifest/final_master/cover/publish_info/quality/logs，全部 Schema 校验。

## FFmpeg

输出本地母版。优先 h264_nvenc，CPU libx264 回退，AAC，记录编码器。Phase 2 才额外生成飞书大小受限的预览版。

## 质量

检查分辨率、FPS、时长、音轨、首 2 秒、字幕安全、黑屏、音量、来源、参考视频原创边界、角色遮挡和可解码性。

## P1 禁止项

通过未来的 Phase 1 本地验收前，禁止飞书、自动选题、Cron、ComfyUI 模型、AI 视频、剪映、抖音发布和继续排查 OpenClaw Codex Plugin OAuth。允许按本文件的隔离与原创规则处理 Jovi 提供的本地参考视频。
