# START HERE — OpenClaw VideoFactory

Updated: 2026-10-25

## 本次范围与停止点

Jovi 于 2026-10-25 明确：本次只整理项目与流程，交付后停止。不得依据旧任务、远端方案或“下一步”自动继续开发、修复、制作视频或推进阶段。后续执行须由 Jovi 重新明确启动。

整理交接见 [CURRENT_HANDOFF](handoff/codex/CURRENT_HANDOFF.md)，协作与收尾流程见 [MAINTENANCE](docs/MAINTENANCE.md#协作与收尾流程)。产品 Phase 1 仍为 in_progress；本轮整理完成不代表产品验收通过。

## 必读顺序

1. PROJECT_STATUS.yaml：当前阶段、约束。
2. [产品需求](docs/PRODUCT_REQUIREMENTS.md)。
3. [当前架构](docs/CURRENT_ARCHITECTURE.md)。
4. [产品路线](docs/PRODUCT_PHASES.md)。
5. [审核说明](docs/PROJECT_REVIEW.md)和[当前交接](handoff/codex/CURRENT_HANDOFF.md)。
6. tasks/todo.md、当前 Change Request，再读对应代码/Schema/测试。

当前是 PHASE_1_LOCAL_VIDEO_FACTORY / in_progress。本轮合并清理不代表 Phase 1 正式通过。

## 产品与工作区

围绕 App、网页、原理图、嵌入式和硬件工程制作原创教程/演示视频；后续网页/App 是操作入口。抖音由 Jovi 人工发布。

注册根目录：E:\project\OpenClaw_VideoFactory。可能存在独立工作区，以真实 Git 身份为准：

```powershell
git fetch origin
git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git diff --check
```

保护 dirty 工作区，不自动 reset、clean、stash、rebase 或 force push。当前代码、Schema 与真实证据优先，历史任务编号和测试次数不定义完成状态。

## 现有入口

- scripts/factory.py / src/factory/phase1_cli.py：主题、参考、执行、取消、重试。
- src/factory/db.py / state.py：SQLite 任务和生命周期。
- phase1_local.py / director/：来源约束的结构化规划与 Registry 素材。
- phase1_subject_audio.py / video_factory/pipeline/：旁白、时序、字幕、渲染、审阅。
- remotion/：技术视觉与 WebsiteProductDemo。
- scripts/phase1_acceptance.py / phase1_gate.py：单任务资格与整阶段 Gate。

必须保留 SQLite 和 Remotion/FFmpeg 单一主链。剪映/DaVinci 是可选编辑层。

## 当前门禁

- 历史 Flash/FreeRTOS 截断候选保持失败，需源对齐新候选及最终 SHA 人审。
- 最近 I2C 状态 I2C_BLOCKED:MPT_APPROVED_CREDENTIAL_UNAVAILABLE；新批准凭证/方案决定前不重试 provider、不创建 Candidate004。
- Phase 2 飞书/Cron、Formal Gate、模型下载和发布继续受原阶段门禁约束。
- DaVinci 最近仅记录 MCP 环境准备；Resolve 实际连接/剪辑/导出未验收。

旧过程文档从 archive/pre-cleanup-20261023 查回；当前操作不要求通读历史。reports/ 里仍有测试夹具和哈希证据，不能按日期批量删除。详见 [维护约定](docs/MAINTENANCE.md)。
