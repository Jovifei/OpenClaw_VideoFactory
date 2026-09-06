# Phase 1 远端审核与开源吸收 — 2026-09-06

## 结论与审核边界

审核基线：`main@4eb3d37e1464d6f55f0a6bbff5abad98dcc664be`，整合提交 `9164fe317fd16139947400a0861b30809052b5ce`。相对交接包 `c815b4e...`，GitHub compare 返回 ahead 36 / behind 0。本报告是指定源码和合同的有界审核，不是整个仓库独立审计，更不是 Phase 1 通过证明。

当前唯一目标：主题或授权参考输入，经现有本地链自动生成可审阅 MP4。飞书、Gateway、OAuth、Cron、自动发布均不属于本轮。剪映编辑可选；不能把“还必须人工剪完”当自动出片完成。

真实环境边界：通过 GitHub connector 读取锁定提交、目录、源文件和提交关系。终端 `git clone` 因 `Could not resolve host: github.com` 失败，后续 `git fetch` 未执行；不能称作 fresh clone。仅将本轮修改文件组成隔离增量工作区运行 Node/FFmpeg 测试；未运行 Windows TTS、Remotion 浏览器渲染、全仓 pytest 或 Formal Gate。

## 本地 Codex 已经做了什么

| 事项 | 远端可核对的实现 | 当前判断 |
|---|---|---|
| Topic/Reference 合并 | 主分支父提交、CR `GIT-REMOTE-BRANCH-CONSOLIDATION-011` | 代码已整合；本地未提交 AGENTS 不在审核范围 |
| FreeRTOS 固定素材 | Registry 1.4、专属素材、脚本事实、主题族过滤及测试 | 不应重做或重新写入上一轮损坏 PNG；真正成片/人工审核另计 |
| 主题起跑 | `phase1_cli.py`、`phase1_topic.py`、MPT adapter | 三候选和有限改写预算已存在，不是从零开始 |
| 主题生产/交付 | `phase1_subject_media.py`、`phase1_subject_delivery.py`、TechnicalExplainer | 已有自动链及质量/交付合同；能编码不等于语义画面过关 |
| OpenMontage | `third_party/openmontage`、PROVENANCE、LICENSE、THIRD_PARTY_NOTICES | **实际选取并适配源码**，不能再说“仅方法参考、未 vendoring” |
| 验收路线 | `topic_only_v1` 和 `legacy_topic_reference_v1` | 两个 profile 保留，不能混合或互相偷换证据 |

CR 011 记录整合树 `502 passed, 1 external deprecation warning`；用户另报告 main 核心 `56 passed`。这些是已有执行记录/用户报告，**不是本轮重新跑出的结果**，不得与新测试相加为“527 passed”。

## 审核发现与本轮修复

### A. 审阅资产重复渲染，且不是最终 MP4 的派生产物【本轮修复】

原 `scripts/render_phase1_topic_visual.mjs` 对 N 场景分别调用 renderStill/renderMedia，再整片 renderMedia，共 N+1 次视频渲染；中点图也单独渲染。独立渲染的审阅图不直接证明最终 MP4 对应帧的内容。

改为一次整片 Remotion 渲染，保留现有无声 visual master，再用 FFmpeg 提取中点 PNG 和各场景 review MP4。每项记录 master SHA-256、半开帧范围、解码帧数、输出 SHA。派生片段用 libx264 CRF18 重编码，仅供审阅，**不替换最终母版，也不声称片段像素无损**；PNG 像素在测试中与母版对应帧逐字节比对。

可证明的是 Remotion 视频渲染调用从 N+1 变成 1。总耗时收益尚未在目标 Windows 机器测量；FFmpeg 解码/重编码及验证也有成本，不能宣传“整体加速一倍”。

### B. 非整帧边界取 round 会夹带上一场景帧【本轮修复】

组件按 `start_seconds <= frame/fps < end_seconds` 选场景。旧审阅范围却 round 场景开始/结束。例如 0.501 秒的边界，在 30 FPS 时下一场景应从 frame 16 开始，不是 round 得到的 frame 15。

使用现有 integer microseconds，BigInt ceil 转帧，半开区间 `[start, end)`，最终末端与 Root.tsx 的 round 总帧数一致。拒绝间隙、重叠、无帧场景、非有限数、字符串/布尔时间、帧数/分辨率不匹配。

真实 FFmpeg 测试还暴露：短片段 passthrough 时间戳可能出现 nb_frames 与 nb_read_frames 不同。采用 CFR `setpts=N/(fps*TB)`，逐个验证实际解码帧数，未用“文件存在”代替通过。

### C. 旧证据覆盖/残留【本轮加固】

新尝试要求 fresh output/report 和空的独立 stills/clips 目录，拒绝路径逃逸、符号链接/Node 可识别 junction、输入输出重合及旧文件覆盖。失败保留本次文件供诊断，不写成功报告；重试用新的 attempt 目录，不删除历史成片。沿用 SQLite 的 Job/lock 权威，不另起状态系统。

### D. I2C 78/85 和通用卡片【仍待完成】

PROJECT_STATUS 记录真实 I2C 候选在允许改写次数后仍为 78/85。源码 `_score` 包含关键词、字数、多样字符等启发式；`_claim_matches` 会因整段出现某些否定词而拒绝绑定。它们不是语义事实核验或原创性证明。未拿到该次完整私有候选，不能断言某条启发式就是该次唯一失败原因。

`build_scene_plan` 轮转五种 visual_type，TechnicalExplainer 将标点切分文本装入卡片；标上 system_diagram 不会自动变成 I2C 接线、开漏、上拉、SDA/SCL 时序图。必须做来源绑定的编辑评审和主题特定图解，不允许加关键词骗分、增加无关过程话术凑时长或降85门槛。

## 开源社区本轮复核及吸收程度

| 对象 | 当前吸收情况 | 本轮决策 |
|---|---|---|
| Remotion 官方 renderer 文档 | 已是正式视觉引擎；layout-utils 固定 4.0.500 | 使用既有 renderMedia、muted、overwrite 与显式本地 browserExecutable；不升级 npm 锁文件，不使用 4.0.502 才新增的多范围 API |
| FFmpeg/ffprobe | 已是合成、解码、检查基础 | 新增 trim/select、CFR 帧范围派生审阅资产，流与解码帧数验证；没有引入新软件依赖 |
| HITsz-TMG/VideoClaw | 阶段 Artifact、可介入/可恢复工作流思想 | 进一步把 review Artifact 绑定最终媒体；不引入其前后端、云视频生成和另一套项目状态 |
| AnthusAI/Babulus | 本轮研究其 narration-first、scene/cue→time→frame 方法 | 独立实现现有 microsecond timing 到帧的严格映射；未安装、未复制其 DSL/源码、未引入另一套 TTS |
| outscal/video-generator | 研究脚本/导演/音频/资产/code 分工及按场景迭代 | 适合下一步改善主题图解和局部重做；本轮不搬其 agent runtime，不把自评分当 human approval |
| MoneyPrinterTurbo | 已有固定 v1.3.5 / eb8c237... 的草稿 adapter | 继续只消费候选文案，禁止导入 MoviePy 全成片链和自动 cross-post |
| OpenMontage | 已适配 cd9f3c1... 的 production checks/只读 Backlot 等，仓库已有 AGPL 声明 | 保留真实 provenance 和许可证，不回退成“从未复制”；不扩展为第二个状态权威 |

此处“当前复核”不是“所有项目都完成许可证/安全/全部源码审计”。本轮新增代码为项目内自行实现，未新增第三方 vendored 文件、模型、插件、npm/pip 依赖。已有许可证不被本次报告改变。

## 仍然阻挡落地的事，按收益排序

1. 实机跑本补丁 + 当前 bounded suites，确认 same-master 审阅资产与 Python verifier/post-render checker 兼容；测耗时和两种 aspect，不先推广新框架。
2. 解决 I2C 的来源绑定编辑评审，补真实语义图解。生成一个当前最终可听 MP4，而不是继续堆“知识卡模板数量”。
3. `topic_only_v1`：Flash、FreeRTOS、I2C 和一个不同 live topic，用当前 schemas、同一候选 SHA、真实 Jovi 审阅和 prereview；不能用旧三主题＋reference 标准替代。
4. cancel/retry/new-process restart recovery/encoder fallback 的 fresh lifecycle evidence。
5. 参考链继续保留；选择 legacy_topic_reference_v1 时才按该 profile 补授权 reference + originality review。不能用 synthetic 测试代替。
6. 证据齐备后再做独立只读审计与一次 Formal Gate；本轮不执行 Gate/phase promotion。

## 一手来源

仓库事实均以基线提交中的对应文件为准：PROJECT_STATUS.yaml、THIRD_PARTY_NOTICES.md、phase1_topic.py、phase1_topic_visual.py、TechnicalExplainer.tsx、render_phase1_topic_visual.mjs、CR 011。旧文档与当前源码不一致时，本次报告指出差异但不伪造完成状态。

- https://www.remotion.dev/docs/renderer/render-media — 本轮读取的官方 API 文档。
- https://github.com/HITsz-TMG/VideoClaw — 项目 README / 阶段化生产方法。
- https://github.com/AnthusAI/Babulus — narration-first scene/cue timing 方法。
- https://github.com/outscal/video-generator — 分工与逐场景迭代方法。
- https://github.com/harry0703/MoneyPrinterTurbo — 项目已有评估/适配来源；具体采用 pin 以本仓库 phase1_topic.py 为准。
- https://github.com/calesthio/OpenMontage — 已采用代码的原项目；具体来源/hash 以 third_party/openmontage/PROVENANCE.json 为准。
- FFmpeg filter API 另用当前环境 `ffmpeg -h filter=trim` / `ffmpeg -h filter=select` 实际核对；测试日志是本次执行证据，网站打开失败未冒称读完官方网页。
