# OpenClaw VideoFactory 产品阶段定义

## 最终产品目标

在 Windows 本机完成一条可审阅、可追溯、可恢复的短视频生产链：

```text
Jovi 提供主题 / 本地授权参考视频 / 明确授权的公开主题研究
  → 事实输入与原创边界
  → 脚本、分镜与小粉飞猪资产选择
  → TTS、字幕、知识插图与程序化画面
  → FFmpeg / 可选 Remotion 模板渲染
  → 1080×1920 MP4、质量报告和人工审阅包
  → Phase 2 才接入飞书候选、选择、兜底和受控交付
```

抖音发布始终由 Jovi 人工完成，除非未来存在单独授权。

## Phase 1 — 本地视频工厂（当前阶段）

### 输入模式

1. `topic`：Jovi 给出主题和经过核验的 factual brief；
2. `local_reference`：Jovi 提供本地、拥有权利的 MP4 和 rights 记录；只提取主题、结构、节奏和通用表达线索；
3. `authorized_public_research`：只在单独授权时使用公开来源，并记录日期与来源。

### 必须输出

- 原创脚本与 Storyboard；
- Registry 内的小粉飞猪资产选择；
- Timeline、TTS、SRT 与 Render Report；
- 25–60 秒、1080×1920、30fps、H.264/AAC 的可解码 MP4；
- Cover、质量报告、发布信息和人工审阅清单；
- SQLite Job、事件、阶段尝试和 Artifact Hash；
- 参考视频模式的 receipt、rights、抽象分析、original brief 和 difference report。

### 正式通过条件

- 三个固定主题 Fixture：Modbus RTU、Flash/看门狗、FreeRTOS；
- 至少一个 Jovi 授权的真实本地参考视频；
- 每个 Job 均处于 `PENDING_REVIEW`，Artifact Hash 与 Review Package 一致；
- Jovi 对每个成片提交结构化人工审阅并批准；
- 取消、失败重试、受控重启恢复和 CPU/NVENC 回退证据通过；
- 无飞书、OpenClaw Runtime、Cron 或自动发布副作用；
- 正式 Gate 产生 `reports/gates/PHASE1_READY.json`；
- Gate 不自动修改 `PROJECT_STATUS.yaml`。

### 明确不阻塞 Phase 1

- 飞书入口与候选卡；
- 08:30/12:00 调度与 Cron；
- ComfyUI、WhisperX 和高级视觉模型；
- 剪映草稿；
- Project Gateway、Device Auth 或 OpenClaw Channel 替换。

## Phase 2 — 飞书自动化

Phase 1 通过后才实施：

- 飞书安全入站与受控出站；
- 08:30 推送 3–5 个候选；
- 用户选择或 12:00 合格兜底；
- 消息、任务、交付幂等；
- 取消、重试、重启恢复；
- 非定时验证通过后才注册 Cron；
- Jovi 人工发布抖音。

## Phase 3 — GPU 与高级视觉生产

- RTX 4070 SUPER 任务队列；
- ComfyUI 白名单工作流；
- 可选 WhisperX；
- NVENC、OOM 和 CPU 回退；
- 模型下载必须单独授权并遵守磁盘预算。

## Phase 4 — 高级参考视频原创化

- 更丰富的视觉/节奏分析；
- 原创性、镜头序列和感知相似度辅助检查；
- 不复用原音、水印、连续镜头和完整文案；
- 人工版权/原创审阅仍是最终门。

## Phase 5 — 可编辑交付与发布辅助

- 可选剪映草稿导出；
- 标题、封面、简介和发布检查清单；
- 草稿失败不得阻塞 MP4；
- 不自动发布抖音。

## 借鉴 VideoClaw 的边界

可以吸收：

- 阶段化项目 Artifact；
- 可编辑中间产物；
- 可恢复 Job 状态；
- Pipeline/Skill 的显式输入输出；
- 人工审阅后再进入下一阶段。

当前不引入：

- 第二套 Backend/Frontend 编排系统；
- 第二套状态数据库；
- 替换现有 Storyboard、Timeline 和 Renderer；
- 多 Provider 扩张或自动模型下载。
