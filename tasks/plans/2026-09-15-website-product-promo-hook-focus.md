# 逐星宣传片重做计划：Hook 封面与焦点镜头（2026-09-15）

## 当前目标

把上一版“整页缩小展示”重做成能快速吸引人、看得清有效信息的 9:16 宣传片：首屏是封面钩子，随后用真实线上页面的局部放大镜头讲清功能，云海画面必须来自最新 Star `origin/main` 对应的线上版本。

## 已有证据与边界

- 旧候选 `final_master_003.mp4` 与修订候选 `final_master_v2.mp4` 均保留，不覆盖。
- VideoFactory 修订分支继续使用现有 Remotion → FFmpeg → SAMI 链，不新增 pipeline 或数据库。
- Star 只读；最新线上 healthz 为 `1.0.18 / 3334e0c08f9a`，云海接口当前 200。
- 不接 Feishu/Cron，不自动发布，不做 Phase Promotion，不修改 Star 业务代码。

## 增量步骤

1. **最新页面采集**
   - 目的：以当前线上 `/`、`/?...`、`/fireglow`、`/cloudsea` 重新采集 1440×900 桌面素材。
   - 证据：live browser、no mock、最新版本/接口状态、PNG SHA、版权与隐私审计。
   - 失败：保留 capture failure，不把旧或错误态截图混入候选。

2. **Hook/焦点脚本**
   - 目的：把片头压到 2 秒内，功能镜头改为有效区域放大；云海文案采用成熟功能描述，不称测试版。
   - 文件：运行时 `script_v3.json`、`storyboard_v3.json`、焦点矩形；仓库只改必要的产品 contract/component/tests。
   - 证据：每段有一个视觉焦点、文本预算、无作者/调试元数据。

3. **快速 SAMI 声音**
   - 目的：使用更有宣传感的本地 SAMI 男声，压缩首句并以新时序生成字幕。
   - 证据：speaker、音频 SHA、覆盖率 ≥0.75、无混用 backend。

4. **单次视觉渲染与封装**
   - 目的：9:16/1080×1920，约 32 秒；只调用一次 Remotion，再用 FFmpeg 合成音频与 ASS 字幕。
   - 证据：视觉母版、最终 H.264/AAC、全帧解码、局部焦点关键帧、CTA ≥4 秒。

5. **审核与交付**
   - 目的：建立新 job/attempt/review package，生成朋友圈/小红书静态文案卡。
   - 停止条件：机器门禁通过后停在 `PENDING_REVIEW`，等待 Jovi 人工观看/试听。

## 采用的公开技能原则

- Remotion 官方 video-layout：每个镜头只保留一个主注意点并使用安全边界。
- Remotion 官方 transitions/captions：使用帧驱动短转场与单一字幕时序；不引入第二渲染器。

## 回滚边界

只保留新的 E 盘运行时目录和修订分支变更；失败候选不覆盖旧候选，Star 与根工作区不做 reset/clean/stash/rebase。

## Review

- Latest capture set uses v1.0.18 / `3334e0c08f9a`; the first six shots plus a separate cloudsea detail shot are hash-bound in `capture_manifest_v3.json`.
- Final job `job-68ebe2322d4a7930f2a05769` is `PENDING_REVIEW`; final MP4 SHA is `6106fab2c1606d53ff42ac2523945844c32614f29e91f1c366dedadede7b5cd3`.
- Remotion visual render, FFmpeg mux, full decode, sequential frame scan and subtitle visibility all passed; only Jovi human watch/listen remains.
