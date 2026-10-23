# 逐星宣传片修订执行计划（2026-09-13）

## 当前状态

- 目标：重做一条 9:16 逐星网站宣传片，修正第一屏采集、旁白声音和文案排版。
- 已确认：第一屏 1440×900 桌面大屏；声音 `ICL_zh_male_shuyisyh`；文案 A 功能叙事。
- 基线：VideoFactory 修订分支从 `bf709a0e0aaca306ead48708759460fc109fa583` 隔离；Star 仅只读。
- 禁止：不改 Star 业务/部署，不接 Feishu/Cron，不自动发布，不下载模型/节点，不覆盖旧 003。

## 步骤

1. **新分支与依赖核对**
   - 目的：确认隔离边界和现有 Chrome/Playwright/SAMI 运行时。
   - 文件：仅 `tasks/todo.md`、本计划、修订设计文档。
   - 证据：`git status`、两个 repo 的 `origin/main`、浏览器/运行时路径。
   - 失败：停止并保留现场；不 reset/clean/stash/rebase。
   - 状态：`baseline_verified`。

2. **桌面真实采集**
   - 目的：用 1440×900 真实线上页面替换第一屏；保留既有五张已审查 capture。
   - 文件：运行时 `capture_plan_v2.json`、新 capture manifest/PNG；代码仅在选择器契约需要时修改。
   - 证据：`method=live_browser_no_mock`、`mocked=false`、viewport、页面来源、版权和隐私 review。
   - 失败：写入 capture failure，不把部分截图提升为候选。
   - 状态：`desktop_capture_reviewed`（`capture_home_v3`，真实 1440×900；degraded/stale 已披露）。

3. **新脚本与静态文案卡**
   - 目的：把 8 段文案改成利益点/解释/边界三层，并生成朋友圈/小红书可截图文案。
   - 文件：运行时 `script_v2.json`、`storyboard_v2.json`、`social_copy_card.html`；不混入技术主题评分。
   - 证据：脚本 hash、scene/beat 一一对应、文本预算和事实边界检查。
   - 失败：修正文案后再测，不进入 TTS。
   - 状态：`copy_v2_ready`。

4. **温暖男声时序**
   - 目的：用 SAMI speaker A 重新生成 8 段音频和微秒时序。
   - 文件：运行时新的 timing root/manifest；不重用旧声音 hash。
   - 证据：`speaker=ICL_zh_male_shuyisyh`、8 段 SAMI、coverage≥0.75、音频 hash/时长。
   - 失败：保留失败 attempt，不拼接旧声音。
   - 状态：`sami_timing_v2_ready`。

5. **产品输入与排版适配**
   - 目的：绑定新 capture、脚本、故事板、timing，调整桌面截图在竖屏中的 contain 尺寸和文字栏。
   - 文件：必要时修改 `WebsiteProductDemo.tsx`、产品 contract/tests；保持 TechnicalExplainer 不变。
   - 证据：Node product tests、typecheck、关键帧不溢出、下角无重复作者文本。
   - 失败：不渲染，修复单一契约问题后重测。
   - 状态：`product_input_v2_validated`（8 场景、1350 帧；竖屏关键帧已检查）。

6. **单次视觉渲染与最终封装**
   - 目的：复用现有 Remotion/FFmpeg 链，生成一份新视觉母版，再封装 A 声音和 ASS 字幕。
   - 文件：运行时新 render/final/review 目录；不覆盖旧 003。
   - 证据：一次 Remotion render、1080×1920/30fps/H.264/AAC、SRT/ASS、CTA≥4秒、全帧解码。
   - 失败：保留新 attempt 和报告，不把 failed 输出标为候选。
   - 状态：`ready_for_jovi_human_review`（job `job-4de5499239aa4af877267315` / attempt `1`，MP4 SHA `73183808c78b0e31cfe3462c0fc1cb2ea4e0915dc4e9302e92a22149a3daac47`）。

7. **双渠道交付与 Git**
   - 目的：生成朋友圈/小红书截图文案卡；记录 SQLite job/attempt/artifact，提交并推送任务分支。
   - 文件：只提交源码、测试、计划、设计和变更请求；所有媒体/音频/DB 在 E 盘 runtime。
   - 证据：review package、MP4 SHA、copy-card path、`git diff --check`、测试日志、远端分支 head。
   - 失败：停止在可审查状态，不合并 main、不做 Phase Promotion。
   - 状态：`pushed_human_review_pending`（review package 与社交卡已生成；未自动发布）。
