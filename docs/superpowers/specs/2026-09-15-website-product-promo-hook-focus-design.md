# 逐星宣传片重做设计：Hook 封面与焦点镜头

## 目标

生成一条更像宣传片而不是网页录屏的 9:16 本地候选：前两秒建立观看理由，随后每个镜头只展示一个可读的产品能力，最后保留清晰 CTA。目标时长约 32 秒，仍由现有 Remotion/FFmpeg/SAMI 链完成，自动发布关闭。

## 结构

1. **Hook Cover（约 2 秒）**：真实首页地图/工作台局部作背景，深色遮罩与大字“今晚，值得出发吗？”，副标题“地点 · 天气 · 时间，一眼决定”。
2. **三步价值（约 3 秒）**：`找机位 / 看天气 / 挑时间` 三个短语快速出现，旁白直接进入收益。
3. **焦点镜头（约 23 秒）**：从最新线上页面采集的高分辨率 PNG 中，每段用声明式焦点矩形（x/y/width/height，归一化 0–1）直接裁切填充；避免把整页缩小成不可读的缩略图。镜头外显示简短标题、一个边界 badge 与统一字幕安全区。
   - 首页：地图搜索/时间控制与工作台总览。
   - 逐小时：云量、降水、风速的时间线区域。
   - 暗夜：夜光参考和候选筛选区域。
   - 观测窗口：连续时段比较区域。
   - 云海：最新 `/cloudsea` 的条件指数、压力层剖面和山顶相对云层关系；不在宣传文案中称 Beta，仍显示“模式参考，非现场实测”的边界。当前空的火烧云排行不进入宣传片。
4. **CTA（约 5 秒）**：`先看一眼，再出发` 与 `photo.joviluma.com`，足够停留让用户记住网址。

## 数据与素材契约

- 所有 PNG 必须来自当前 `https://photo.joviluma.com` 的 `live_browser_no_mock` 采集，manifest 记录 `1.0.18 / 3334e0c08f9a` 对应的采集时间、viewport、SHA 和接口状态。
- `story_v3` 为每个截图声明 `focus`，不改变原图字节；渲染器只按 focus 做视觉裁切/缩放。
- 裁切不删除版权/来源信息；来源放在镜头的窄行说明，焦点画面只放大产品有效区。
- 文案只描述页面可见能力；条件指数、压力层云底/云顶等不写成现场概率或实测。

## 动画与排版

- 所有动画由 `useCurrentFrame`/`interpolate` 驱动，封面和焦点采用 6–10 帧淡入、轻微位移或缩放；不使用 CSS animation。
- 标题保持一行或两行，主标题不小于 58px；核心内容距离左右至少 76px，底部字幕保留现有 1640–1760 安全区。
- 焦点视窗使用 `overflow:hidden` + `Img` transform；禁止全屏 dashboard 多列同时争夺注意力。
- 不渲染场景编号、信息角色、生成时间等 authoring metadata；只保留必要的产品边界提示。

## 声音与时序

- 使用本地 SAMI `zh_male_ad`（广告男声）候选；文案压短，首段语音 1.76 秒，目标 32 秒左右。
- 新 timing manifest 绑定 narration/subtitle/audio SHA；字幕从新时序生成，不能复用旧 timing。
- 仍保持单一字幕权威与 FFmpeg ASS PlayRes 1080×1920；无 BGM，避免旁白可懂度下降。

## 验证与停止条件

- capture manifest/review、focus/text contract、Node tests、Remotion typecheck 和 contracts 必须通过。
- 只调用一次 Remotion 视觉渲染；FFmpeg 封装后必须通过 full decode、逐帧健康、字幕可见性、音频峰值检查。
- 输出 job 状态只能到 `PENDING_REVIEW`；Jovi 的观看/试听是唯一人工通过条件，不自动发布、不做 Phase Promotion。

## 失败与回滚

- 最新页面采集若出现 4xx/5xx、mock 或旧版本，保留失败目录并停止，不退回旧截图冒充最新。
- 焦点或标题溢出只修订同一 contract 后使用新的 E 盘 attempt；不覆盖旧候选，不 reset/clean/stash/rebase。
