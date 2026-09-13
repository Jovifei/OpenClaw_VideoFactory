# 逐星网站宣传片修订设计（2026-09-13）

## 目标

在现有 `WebsiteProductDemo` 和本地 Remotion/FFmpeg 链上重做一条 9:16
宣传片：第一屏使用逐星真实桌面大屏页面，旁白改为 A 温暖男声，采用 A
功能叙事文案，并交付一份可听、可看、有字幕的 MP4。朋友圈/小红书另给
一张可截图的文案卡，不接飞书、不发布、不代表 Phase Promotion。

## 已锁定选择

- 成片：1080×1920、30fps、约 45 秒、无背景音乐。
- 第一屏采集：`https://photo.joviluma.com/`，1440×900 桌面视口，真实无 mock；
  contain 放入竖屏截图区，保留导航、地图、数据和版权信息。
- 声音：本地 SAMI `ICL_zh_male_shuyisyh`（温暖男声），以新实测时序驱动字幕。
- 文案：A 功能叙事；每段使用一条利益点、一条解释或边界，字幕短句化。
- 版式：标题最多两行；截图下只放日期/归属；功能说明单栏；字幕固定安全区；
  不显示左右下角作者/调试信息。

## 数据流

`live desktop capture → capture review → v2 script/storyboard → SAMI timing →
SHA-bound product input → WebsiteProductDemo visual master → existing ASS/audio
assembler → post-render/full-frame checks → SQLite job/attempt/review package`.

只新增一个版本化运行时 attempt；旧 003 及本轮旧输出不覆盖、不删除。Star
仓库只读，业务代码和部署不在范围内。

## 组件边界

- `capture_product_pages.mjs` 继续负责白名单 URL、桌面视口、可见就绪条件、
  真实截图和来源 receipt；禁止 mock/API fulfill。
- `build_product_input.mjs` 继续绑定脚本、故事板、SAMI manifest、捕获和人工
  资产检查；不创建第二套数据库或渲染器。
- `WebsiteProductDemo.tsx` 只调整宣传片排版尺寸和安全区；不改变技术片。
- `assemble_product_preview.py` 继续复用测量音频，生成 SRT/ASS 并烧录 ASS；
  只做后处理，不重新渲染视觉。
- 朋友圈/小红书文案卡是独立静态文案产物，不混入抖音 MP4 的质量评分。

## 验收

1. 采集 receipt 的第一屏 viewport 为 1440×900、`method=live_browser_no_mock`、
   `mocked=false`，并通过来源/版权/隐私检查。
2. 新声音的 8 个 SAMI 音频段、脚本 hash、字幕 hash 和场景边界一致，覆盖率
   不低于现有 0.75 门槛。
3. 视觉母版只渲染一次；最终 MP4 为 H.264/AAC、1080×1920、30fps、全片可解码，
   字幕在安全区可见，CTA 至少 4 秒。
4. 运行 typecheck、跨语言 contract、产品测试、post-render、全帧扫描、音量与
   关键帧检查；SQLite 状态停在 `PENDING_REVIEW`。
5. 最终状态只可写 `ready_for_jovi_human_review`；人工观看/试听后才有下一步。

## 禁止项

不修改 Star 业务代码或部署，不接 Feishu/Cron，不自动发布抖音，不下载新模型
或节点，不伪造人工审核，不降低既有质量门槛，不把静态文案卡当作视频交付。
