# 开源 Skill 与工具筛选矩阵

## 结论

不要把多个“一键生成视频”项目同时放进主链路。它们会重复管理脚本、素材、字幕和渲染状态，出错时难以恢复。

主链路按产品阶段保留：

1. **Phase 1 本地成片**：我们的细粒度 Skill（主题/参考视频主题分析、分镜、画面、字幕、渲染、质量）+ Remotion 官方 Skill + 本地可控 TTS/FFmpeg。
2. **Phase 2 飞书自动化**：OpenClaw（长期运行、定时、聊天入口、状态和通知）+ 飞书官方 larksuite/cli。
3. **后续增强**：video-podcast-maker 的方法、comfyui-mcp 与 CapCut Mate/jianying-editor-skill 的隔离评估。

## A 级：进入正式生产链

### larksuite/cli（仅 Phase 2）

定位：飞书官方团队维护的 CLI 与 Agent Skills。

采用方式：

- 使用官方 npm 安装器；
- 启用 `lark-shared`、`lark-im`、`lark-event`；
- `lark-drive`、`lark-doc` 和 `lark-markdown` 按需启用；
- OpenClaw 飞书 Channel 是 **Phase 2** 的主要入站通道；
- lark-cli 负责受控的消息、文件、视频、资源下载和可选事件操作；
- 所有自动发送使用 bot 身份、固定目标白名单、dry-run 和幂等键；
- 高风险写操作必须等待用户明确确认。


### remotion-dev/skills（Phase 1 起）

定位：官方 Remotion Agent Skill。

采用方式：

- 只在单独授权安装后使用 `skills/remotion`；
- 所有 Remotion 模板新增或修改前必须读取；
- 用于时序、转场、字幕、音频、动态图表、Lottie、图像和参数化视频；
- Codex 开发模板时同样遵守该 Skill。

### Agents365-ai/video-podcast-maker

定位：主题研究到视频交付的知识视频工作流。

采用方式：

- 借用其研究、脚本、TTS、timing、发布资料和组件化思想；
- 不直接让它管理日常任务状态；
- 将长视频脚本规范改写为 25～60 秒抖音技术短视频规范；
- Windows 下复用可移植部分，不照搬其系统安装步骤。

### artokun/comfyui-mcp（Phase 3 候选）

定位：Agent 对本地 ComfyUI 的控制层。

采用方式：

- 4070 SUPER 的主要入口；
- 只开放封面、背景图、风格参考、2～4 秒 B-roll、抠图、放大等白名单工作流；
- 不在无人值守期间自动安装节点和下载陌生模型；
- 生成失败自动退回静态图或 Remotion 动画。

### CapCut Mate / jianying-editor-skill（Phase 5 编辑后端）

两者不要在同一任务同时启用。当前 Jovi 视频默认选择已审核并锁定版本
的 `jianying-editor-skill`；CapCut Mate 只作为隔离适配器候选。

CapCut Mate 更适合：

- OpenClaw 通过 localhost REST API 调用；
- 稳定生成剪映草稿；
- 添加视频、音频、图片、字幕、动画和关键帧；
- 与主流程解耦。

jianying-editor-skill 更适合：

- Windows 本机深度使用剪映；
- 自动搭时间线、配音、字幕、特效、录屏和网页动效；
- 专用旧版剪映环境中的自动导出。

推荐默认：现有 Remotion/FFmpeg 负责可审计的视觉底片，
`jianying-editor-skill` 负责唯一的剪映草稿、SAMI 配音和原生字幕轨；
最终试听和导出仍由 Jovi 在剪映中手动完成。

## B 级：包装成我们自己的 Runtime Skill

### faster-whisper

用于 CUDA 转录、词级时间戳和 VAD。正常 TTS 成片使用它即可。

### WhisperX（Phase 3/4 候选）

用于参考视频、多人对话或对齐精度要求高的任务。普通单人 TTS 不必每条调用。

### PySceneDetect（Phase 1 本地参考视频主题分析可评估；Phase 4 高级分析）

用于参考视频切镜、镜头时长、节奏和转场分析。

### Auto-Editor

用于口播、录屏和长素材的“初剪”，自动删除静音或静止区域。它不替代最终编排。

### Real-ESRGAN

用于 ComfyUI 图片、低清参考素材和短 AI 镜头的放大。技术文字和电路图不做 AI 放大后直接当事实图。

## C 级：实验室或方法参考

### OpenMontage

优点：

- 参考视频分析；
- 分镜和审批门；
- 素材检索；
- 多流水线；
- Backlot 可视化；
- 自我质检。

限制：

- 项目规模很大；
- 与现有架构重叠；
- AGPL-3.0，需要单独评估许可义务。

因此只在独立目录运行，或学习其方法后自行实现，不把代码复制到本项目。

### OpenReels

适合快速比较：

- Topic 到 Short 的一键流水线；
- Director Score；
- 视觉 archetype；
- 自动重试和成本预估。

不作为主链路，因为它偏云端视觉供应商，且会重复我们的研究、脚本和 Remotion 状态。

### MediaCrawler

不默认启用。平台爬取涉及服务条款、登录和频率限制。Phase 1 的“扒取主题”只表示 Jovi 明确授权的、可公开访问且可追溯的主题研究，不表示自动抓取抖音或受限平台。

选题数据默认来源：

- 用户真实项目与 Git 提交；
- 用户提供的评论；
- 公开网页检索；
- 官方文档和技术社区；
- 手工导入的 CSV/JSON。

## 推荐最终 Skill 路由

```text
topic-intelligence
        ├─ Phase 1：Jovi 主题 / 本地参考视频 / 已授权公开研究
        └─ Phase 2：飞书候选卡与选择
        ↓
script-storyboard-director
        ↓
media-asset-curator
        ├─ deterministic SVG/HTML/Remotion
        └─ comfyui-gpu-renderer
        ↓
audio-subtitle-engine
        ↓
remotion-layout-engine
        ↓
video-quality-gate
        ├─ MP4 待发布
        └─ jianying-draft-exporter（可选）
```

端到端单链路的阶段所有权、输入输出和停止条件见
`skills/video-production-chain/SKILL.md`。该路由不引入第二套 renderer，
也不把 CapCut Mate 或 JianYing MCP 混入同一任务。


## D 级：品牌角色系统

### Jovifei/ian-fenzhu-illustrations

用途：

- 作为“小粉猪”角色系统来源；
- 增强个人视频辨识度；
- 为嵌入式主内容和 AI 热点栏目增加轻量陪伴角色。

采用方式：

- 先审查仓库的 skill、素材、许可证与目录结构；
- 优先复用现成 skill 或素材；
- 若不适合直接接入，则提炼角色定义、表情包和使用规则，沉淀为本地 `pink-pig-mascot-director` skill；
- 不让角色系统阻塞主视频生产链。
