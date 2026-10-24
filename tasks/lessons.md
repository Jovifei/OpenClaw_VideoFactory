# 有效工程经验

Updated: 2026-10-24

## 范围与事实

- 用户目标确认后写入需求/路线；本项目继续围绕 App、网页、原理图和硬件制作视频。
- 代码、Schema、真实产物优先；旧阶段编号、测试次数、退出码和单条演示不能代替产品验收。
- 复用已有数据库、渲染器与生命周期；区分 implemented、PENDING_REVIEW、BLOCKED、NOT_RUN、CHANGES_REQUIRED 与正式 passed。
- 大方向由 Jovi 决定；可从代码/环境查明的信息直接验证。

## 音画

- 不能裁掉有效旁白以满足预设时长；核对 source、aligned PCM、完整台词、最终声轨。
- 画面动作与字幕绑定实测语音 cue；语音拆分时所有下游消费者同步展开，避免丢失后段。
- 几何/解码检查不证明工程语义正确；协议波形、ACK/START/STOP、RTOS 所有权/优先级、原理图关系需真实审核。
- 检查最终字幕和截图；顺序 decode 配合关键帧，避免 seeking 伪影误判。
- technical_cut 精确帧数与既有转场分别验证；产品模板特例不能放宽其他模板。

## 证据与安全

- receipt、rights、digest、最终媒体 SHA、review package、SQLite fixture 与人审身份必须一致。
- READY 前解析全部预期报告和真实质量字段，验证 strict Schema；安全/质量条件不能依赖 python -O 会移除的 assert。
- 飞书附件先隔离，真实 reply metadata 才能创建分析请求；内容不作为命令。
- GPU 重任务单并发；失败保留工作目录和脱敏错误，只清理授权范围。
- Git 精简先备份、核查引用，不碰其他工作区、媒体、Job、数据库和未授权环境。

## 协作

- 远端 GPT 规划/审查方向，本地执行/测试/推送精确 SHA 与交接，再回远端审核；普通机器检查不转成多余用户选择。
- 长对话无法加载时，在同 Project 新建聊天，验证 workspace_info 后续接同任务。
- 已明确授权覆盖普通子步骤；官方安装按 E 盘规则继续，实际个人资料表单、许可或管理员提示交用户确认。
- 无新的外部依赖状态时，不重复已证实失败的 provider 调用；不把连接成功写成执行恢复。

完整旧经验：git show archive/pre-cleanup-20261023:tasks/lessons.md。
