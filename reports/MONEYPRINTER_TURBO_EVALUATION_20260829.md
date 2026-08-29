# MoneyPrinterTurbo 本地部署评估（2026-08-29）

> Change Request: `PHASE1-EXTERNAL-EVAL-MONEYPRINTER-TURBO-001`
> 结论先行：**可以本地部署，已实测跑通；建议把它作为"选题关键词 → 旁白文案草稿"的上游输入工具接入，不引入它的成片渲染链。**

## 1. 对象与合规

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/harry0703/MoneyPrinterTurbo |
| 版本 | v1.3.5，固定 commit `eb8c237`（shallow clone） |
| 协议 | MIT（Copyright (c) 2024 Harry）——与本项目使用兼容 |
| 位置 | `external/MoneyPrinterTurbo/`（已被 .gitignore 覆盖，不进 Git） |
| 运行环境 | 独立 Python 3.12 venv（`external/MoneyPrinterTurbo/.venv`），不污染项目 `.venv` |
| 主要依赖 | moviepy 2.1.2、edge_tts 7.2.7、faster-whisper 1.1.0、streamlit 1.59.1、fastapi 0.136.3 |

## 2. 本地部署实测（零 API Key）

全部在本机（Windows 原生、系统 FFmpeg 8.1.1 自动发现）真实运行：

1. **CLI**：`cli.py --help` 正常，支持 `--stop-at {script,terms,audio,subtitle,materials,video}` 阶段截断。
2. **WebUI**：Streamlit 启动，`http://127.0.0.1:8503` 返回 HTTP 200。
3. **API**：`uvicorn app.asgi:app` 启动，`/docs` 返回 HTTP 200；状态后端存在 `MemoryState` 内存回退，**本地不需要 Redis**。
4. **Edge TTS 独立出声**：`zh-CN-XiaoxiaoNeural` 合成中文旁白 MP3（4.488 秒），无密钥。注意它是微软**在线**免费服务，不是完全本地。
5. **流水线冒烟（最有价值）**：自带脚本（跳过 LLM）+ `--video-source local`（跳过素材检索）+ `--stop-at subtitle`，任务 `72848715…` 完整跑通 编排 → TTS → 字幕，产出 `audio.mp3`、`script.json`、`subtitle.srt`（3 条字幕、时间轴正确）。**全程零密钥、零模型下载**。

原始证据：`reports/phase1/moneyprinter_turbo_smoke_20260829.json`。

## 3. 它的能力 vs 我们现有链路

| 能力 | MoneyPrinterTurbo | 我们现有链路 | 重叠/冲突 |
|---|---|---|---|
| 文案生成 | LLM 一键生成（30+ 提供商） | 人工 brief → 原创脚本 | **互补**：可作为候选文案上游 |
| 配音 | edge-tts（免费在线）/ Azure | 剪映 SAMI（唯一 TTS 后端） | 重叠；替换需另批变更请求 |
| 字幕 | TTS 时间轴 / faster-whisper | SAMI 时间轴（单一 manifest） | 库相同（faster-whisper 1.1.0），思路一致 |
| 素材 | Pexels/Pixabay/Coverr 检索、本地素材、AI 生视频 | Remotion 程序化技术画面 | 风格不同；可选 B-roll 补充 |
| 成片合成 | MoviePy + 烧录字幕 | Remotion 底片 + 剪映草稿 | **冲突**：锁定决策禁止第二渲染器 |
| 发布 | TikTok/YouTube 自动 cross-post | 禁止自动发布 | **禁用**（默认即关闭，保持关闭） |

## 4. 与锁定决策的冲突边界

- 「Remotion 唯一画面渲染器 + jianying-editor-skill 唯一编辑/SAMI/字幕后端」：MPT 的 MoviePy 成片段**不采纳**。其 `stop_at` 机制恰好允许只消费前段能力，绕开 MoviePy。
- 「远程 Provider 须另有获批变更请求和预检」：LLM 文案与 edge-tts 均属远程服务；本次仅为隔离评估，未接入生产链。正式启用需 Jovi 批准下文选项。
- 「不自动下载模型」：字幕默认 `large-v3`（约 3GB 运行时下载）**未触发**；若采纳 whisper 字幕，必须固定小模型或复用现有 faster-whisper 缓存。
- 自动 cross-post 保持未配置、未启用。

## 5. 接入选项与建议

- **选项 A（推荐）：选题关键词 → 文案草稿器。** 在 `external/` 以子进程/CLI 方式调用 MPT `--stop-at script`（LLM 提供商建议 DeepSeek 或 Moonshot，需 Jovi 提供并自行保管 Key，写入 gitignored 的 `config.toml`），产出 2–3 个候选旁白文案 → Jovi 挑选修改 → 进入现有 `original_brief` → 我们的 Remotion/SAMI/剪映链成片。它补齐"关键词起跑"的自动化，不触碰渲染与编辑后端。
- **选项 B（可选）：edge-tts 作为 QA 试听备选配音。** 免费、中文音色好，可加速无剪映依赖的预览；但 SAMI 是锁定后端，需单独变更请求批准，且正式配音仍走 SAMI。
- **选项 C（可选，暂缓）：Pexels/Pixabay B-roll 素材检索**，由 `media-asset-curator` 管理权利记录。当前主线是程序化技术画面，暂不需要。
- **不采纳**：MPT 整体成片链（MoviePy 烧录字幕）、自动 cross-post。

## 6. 后续最小接入步骤（待 Jovi 批准选项 A 后）

1. 新建变更请求：MPT 作为外部文案草稿适配器（subprocess 调 `cli.py --stop-at script`，超时/取消/日志落 `reports/`）。
2. `config.toml`（gitignored）配 LLM 提供商与 Key；仓库内只留占位模板。
3. 加一条冒烟测试：给定主题关键词 → 生成候选文案 JSON → 断言不触碰渲染链、无密钥泄漏。
4. 人工审阅文案后再走现有原创 brief 流程；MPT 文案只是草稿，不直接成片。
