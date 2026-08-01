# 04 — P1 确定性视频MVP

## 目标

不依赖AI视频和剪映，严格按 P1-A 到 P1-G 小步构建确定性视频 MVP。一次只增加一个类别；前一步未验证通过，不进入下一步。

## P1-A — SQLite 与 CLI

只实现 `src/factory/` 的 config、db、state、events 和 CLI。

CLI：doctor、create-topic、run、status、retry、cancel。`scripts/factory.py`只作薄包装。

至少：jobs、job_events、artifacts、topic_history、source_records、inbound_messages、deliveries、stage_attempts、locks。

唯一键：job_id、source_message_id、每日自动键、delivery幂等键、阶段尝试号。

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

## P1-G — 最后接飞书交付

只有三个 fixture 都通过后，才增加 cover、preview MP4、report 和幂等交付。OpenClaw 继续负责飞书与任务状态；Codex CLI 负责代码实施。

## Job产物

每个job有job/config/topic/research/sources/script/storyboard/style/asset_manifest/voice/captions/render_manifest/final_master/feishu_preview/cover/publish_info/quality/logs，全部Schema校验。

## FFmpeg

输出母版和≤25MB飞书预览。优先h264_nvenc，CPU libx264回退，AAC，记录编码器。

## 质量

检查分辨率、FPS、时长、音轨、首2秒、字幕安全、黑屏、音量、来源、角色遮挡、可解码和预览大小。

## P1 禁止项

通过 `python .\scripts\90_acceptance_gate.py --gate p1` 前，禁止自动选题、Cron、ComfyUI模型、AI视频、参考视频、剪映、抖音发布和继续排查 OpenClaw Codex Plugin OAuth。
