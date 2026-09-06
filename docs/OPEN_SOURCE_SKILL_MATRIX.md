# 开源 Skill / 工具 / 项目采用矩阵

Updated: 2026-09-06；审核基线 main `4eb3d37e1464d6f55f0a6bbff5abad98dcc664be`。

**先纠正旧记录：OpenMontage 已有选取并适配的源码，MoneyPrinterTurbo 已有文案草稿 adapter。** 旧“OpenMontage仅方法参考、不vendoring”的描述不适用于当前主分支。详见 [本轮审核](PHASE1_REMOTE_AUDIT_20260906.md)、根 LICENSE、THIRD_PARTY_NOTICES 和 third_party/openmontage/PROVENANCE.json。本页不改变已有许可证或第三方义务。

## 1. 已采用的组件：保留，不重建

| 组件 | 实际职责/证据 | 采用边界 |
|---|---|---|
| FFmpeg / ffprobe | 合成、H264/AAC、完整解码、媒体检查；012新增从最终visual master提取审阅资产 | 不拥有任务状态。CPU/NVENC运行资格仍需本机证据 |
| Remotion | TechnicalExplainer、Flash、RC高通、语音cue动画；现有layout-utils固定4.0.500 | 既有视觉引擎，不升级锁文件、不自动下载浏览器、不接管SQLite |
| PySceneDetect | reference_video.py 本地scene boundary/pace | 分析只读授权素材，不拿参考帧做原创画面 |
| faster-whisper | 可选参考音频ASR，现有缓存 | 普通自生成TTS直接用脚本/实测时序，不强制再跑ASR；缺缓存不下载 |
| MoneyPrinterTurbo | phase1_mpt_script_drafter.py / phase1_topic.py，v1.3.5、eb8c23757e098a07bbcd93b3b50e252fc8d1869a | 只消费候选文案；不接入MoviePy渲染、自动cross-post或第二套状态；在线Provider需既有授权 |
| OpenMontage | third_party/openmontage 生产检查、pipeline manifest、只读Backlot等，cd9f3c1f03368be87b140af494914b8ee4e3c7a4 | 源码适配且有AGPL声明；SQLite仍唯一状态权威，不扩展独立写状态/第二后端 |
| luoluoluo22/jianying-editor-skill | 已选可选编辑后端；现有SAMI/字幕能力沿用 | 一个Job只允许一个编辑后端；核心交付必须已有MP4，禁止自动导出/发布 |

## 2. 方法借鉴：本轮没有复制这些项目的源码

| 项目 | 值得采用 | 不引入 |
|---|---|---|
| HITsz-TMG/VideoClaw | 阶段Artifact、检查点、人可介入、可恢复/可修改 | 第二套VideoClaw前后端/DB、强制云生成模型 |
| AnthusAI/Babulus | narration-first、scene/cue的时间到帧映射；012在既有微秒合同内独立实现帧范围 | 新DSL、新TTS、第二份timing权威 |
| outscal/video-generator | 脚本/导演/音频/素材/code分工，逐场景迭代 | agent runtime替换、自评分冒充事实/人审；未完成许可审核前不复制 |
| Agents365-ai/video-podcast-maker | research→script→TTS/timing→Remotion方法 | 原记录CC BY-NC 4.0下的代码/模板不得未经许可直接搬入可能商业路径 |
| Jovifei/ian-fenzhu-illustrations | style/persona/composition规范 | 上游sample、自制/AI临时角色不是Jovi最终原始IP资产 |
| Code2MP4/OpenReels等 | 合同、archetype、成本/局部重试的研究方向 | 不因仓库名称/评分系统就宣称已经集成或可自动通过 |

## 3. 本轮真正落地的吸收

`TechnicalExplainer一次渲染 → 最终visual master → FFmpeg按帧派生PNG/场景片段 → master SHA与解码帧数校验`。

既有媒体合同保持，新增实现及真实FFmpeg测试见 `scripts/lib/phase1_review_artifacts.mjs` 与 `tests/video/phase1_review_artifacts.test.mjs`。没有新增npm/pip依赖、模型、第三方vendored文件。单次renderMedia调用已可静态测试；完整性能收益和Windows渲染仍需本地Codex测量。

## 4. 延后，不能阻挡 Phase 1

ComfyUI approved workflow/创意B-roll、WhisperX更精细对齐、Auto-Editor长口播初剪、Real-ESRGAN非事实图放大均延后。技术事实（代码、电路、协议、公式、时序）不用不受控生成图替代。新增模型/节点、预算、GPU资源需授权。

CapCut Mate、其他Jianying MCP保持隔离候选，不能与已选编辑后端同时控制一个Job。OpenClaw/Feishu/larksuite CLI、选题卡与Cron属于Phase 2，不是当前自动出片前提。n8n/LangGraph/Temporal及其他全链工厂不作为第二编排层。

## 5. 当前 Skill 路由与政策

Topic/verified research → script-storyboard-director → media-asset-curator → audio-subtitle-engine → remotion-layout-engine/现有FFmpeg → video-quality-gate → local MP4 + review package。剪映可选。

授权Reference → reference-video-analyzer → 去内容化抽象/original brief → 同一生产链 → difference evidence + Jovi原创性审阅。

Aspect是Job合同，支持1080×1920和1920×1080；mascot默认off，opt-in必须Jovi原始资产+receipt；无角色不应阻断正常技术视频。音频实测timing是时间权威。Phase 1验收profile按当前schemas，不能用历史文档偷换。
