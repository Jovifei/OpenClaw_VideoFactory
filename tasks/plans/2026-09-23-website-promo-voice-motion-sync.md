# 逐星宣传片：旁白节拍与画面运动同步（2026-09-23）

## 目标与当前证据

沿着上一版已批准的 9:16 Hook/焦点方案继续重做。最新线上 Star 主线已前进到 v1.0.19 / `b2bd41d4e921`；公开 `/healthz`、`/api/data-status`、`/api/cloudsea/snapshot` 在本轮只读核对返回 200。

目标：用 v1.0.19 实拍云海详情作封面，旁白自然分段并测量每个子段时序，镜头推拉与焦点标记逐句跟随这些时序。最终片 30 秒，继续复用现有 WebsiteProductDemo、Remotion、FFmpeg 和 SAMI 流程。

## 边界

- 仅改 `codex/website-product-promo-revision-20260913` 修订分支；生产 MP4、SAMI draft、capture receipts、SQLite 全部写入新的 E 盘 runtime 子目录。
- Star 仓库仅用于只读检查和线上页面截图，不修改业务代码、不部署。
- 保留 v8 与其证据，不 reset/clean/stash/rebase，不强推、不删分支。
- 不接 Feishu/Cron，不自动导出或发布抖音，不做 Phase Promotion，不下载模型/依赖。
- 音画同步以测量到的 SAMI 子段起止为准，不对整条成片做无声画面变速，也不使用猜测的词级 ASR 时间。

## 实施步骤

1. **刷新真实素材**：基于 Star `origin/main` `b2bd41d4e921` 和公开 v1.0.19 页面，重新采集首页、逐小时、暗夜、观测窗口及云海概览/详情；记录 source status、页面版本、PNG SHA、版权与数据完整性。失败 attempt 保留。
2. **重写分段口播**：整理为 6 个 beat 并添加精确拼接的 `narration_parts`，每段在自然语气停顿切分；Story shot 声明对应的 `motion_cues`（字幕短语、镜头方向、焦点坐标），不创造额外产品事实。
3. **测量 SAMI 子段**：用固定 `zh_male_ad` 后端生成每段音频；校验脚本文本连接、每个音频 SHA、时长和 coverage。只有这份新 timing 可驱动画面和字幕。
4. **绑定声画 cue**：输入 builder 把 manifest 子段起止 frame 映射到 shot motion cues；现有渲染器在实测语音窗口内推进镜头位移/缩放、焦点标记和短语标签，语音结束后保持画面，不抢后续句子。封面使用真实云海详情局部并显示模式推导边界。
5. **复用 FFmpeg 封装**：扩展现有 assembler 以扁平化播放已测量的 SAMI 子段并延迟混音；单条句子字幕继续绑定父 beat 起止。保持现有一条 Remotion 视觉母版与一条 ASS 字幕轨。
6. **交付新候选**：单次 Remotion render，人工逐场查看封面、切点、焦点、字幕和云海画面；记录 SQLite Job/attempt/工件哈希和 review package，状态停在 `PENDING_REVIEW`。
7. **分支收尾**：更新计划/lesson/CR，提交并推送任务分支；不合并 main。

## 关键文件

- `remotion/src/product-demo/WebsiteProductDemo.tsx`
- `remotion/src/product-demo/website-product-contract.mjs` 与 `.d.mts`
- `scripts/product-demo/build_product_input.mjs`
- `scripts/assemble_product_preview.py`
- 当前生产入口：`scripts/phase1_jianying_timing_probe.py`、`scripts/render_phase1_topic_visual.mjs`
- 回归夹具位于 `tests/product-demo/`，本轮以实际 E2E render/帧审阅作为交付证据，不改其他生产链。

## 失败与停止条件

- 新鲜线上 capture 出现数值 4xx/5xx、旧版本或 mock，失败图不进入输入；不退回 v1.0.18 冒充最新。
- 子段拼接与原旁白不逐字相等、任何子段 SHA/时长错位、后端混用或 coverage 低于 0.75，停止渲染。
- 任一画面 cue 超出对应的测量语音窗口，停止封装并修复绑定。
- 最终必须保留完整 decode、声音非静音/无削波、字幕可见和人工审片要求；v8 继续原样保留。

## 最终交付核对（2026-09-23）

- 最终候选 `final_v5_attempt4/final_master_v5_attempt4.mp4`，Job `job-07b5db48afc8bec16f75c326`，render attempt 2，SHA-256 `bf0b6f98415918ae6d4d320729b6739c036b6469ef76db89c26e73bcfc605f08`。
- SAMI `zh_male_ad` 15 个实测子段；总语音 26.04s / 30s，15 个焦点标签和位移窗口与子段逐一绑定。
- Remotion 1080×1920、30fps、30s，单次视觉渲染；字幕 6 条，视频与 ASS/SRT 绑定到同一 timing/script SHA。
- Final assembly 与 `phase1_post_render_check.py` 均 passed；扫描 900 帧、0 黑帧，完整解码、AAC 音频、字幕烧录和无削波通过。
- 唯一审片包 `final_v5_attempt4/review_package_v5_final.json`；SQLite 质量 attempt 1 因字幕换行未通过，attempt 2 passed，Job 停在 `PENDING_REVIEW`。Jovi 仍需观看/收听并作人工决定。
- 不合适的天气/观测截图未进宣传镜头；脚本不陈述实时预报数值。云海条件明确为模式推导、非现场观测。
