# Codex 接管任务：PHASE1-LOCAL-FACTORY-COMPLETION-002

## 工作目录与分支

- 仓库：`E:\project\OpenClaw_VideoFactory`
- 分支：`codex/phase1-reference-video-analysis-001`
- 已知远端基线：`8703f7dc319c47d97ab88b4c53d1e81e94dcb782`，接管时必须重新确认 HEAD；若远端已前进，先审计差异，禁止回退。

## 最终目标

正式完成 **Phase 1 本地视频工厂**，而不是继续做参考分析子功能，也不是提前接飞书。

必须证明两条完整链：

```text
主题 + verified factual brief
→ 脚本/分镜/资产选择
→ TTS/字幕/渲染/质量报告
→ 本地原创 MP4 + 人工审阅包
```

```text
Jovi 授权的本地参考 MP4 + rights
→ 安全入库/场景/节奏/可选 ASR
→ 抽象 original brief
→ 全新脚本/分镜/小粉猪视频
→ difference report + 人工原创审阅
```

## 已有能力，不得重写

- `src/factory/db.py`：SQLite Job/Event/Artifact/Stage Attempt；
- `src/factory/phase1_cli.py`：create-topic、create-reference、run、status、cancel、retry；
- `src/factory/phase1_local.py`：主题与参考抽象到确定性计划；
- `src/factory/reference_video.py`：参考视频安全入库、分析与原创差异证据；
- `src/factory/director/`：Provider-neutral Director；
- `video_factory/pipeline/`：Storyboard、Timeline、TTS、字幕、Composition、Renderer、Review Package；
- `generate_video.py`：唯一渲染入口；
- 当前历史回归：355 passed，1 skipped（必须本轮重跑）；
- `phase1_acceptance.py` / `phase1_gate.py`：人工审阅对账和正式 Gate，已完成 9 项隔离测试，但必须在当前 Windows 环境复核。

## 本轮新增基线

先完整阅读：

- `docs/PRODUCT_PHASES.md`
- `runbook/11_PHASE1_COMPLETION.md`
- `schemas/video/phase1_human_review.schema.json`
- `schemas/video/phase1_job_prereview.schema.json`
- `schemas/video/phase1_acceptance_manifest.schema.json`
- `schemas/video/phase1_lifecycle_evidence.schema.json`
- `schemas/video/phase1_boundary_audit.schema.json`
- `src/factory/phase1_acceptance.py`
- `src/factory/phase1_gate.py`
- `scripts/phase1_acceptance.py`
- `scripts/phase1_gate.py`
- `reports/PHASE1_REMOTE_AUDIT_20260822.md`

## 连续执行顺序

1. 审计分支、HEAD、工作树和远端，不 reset/clean/stash；
2. 运行新增 acceptance/gate 测试与原 355 项回归；
3. 如新工具与真实 Job 结构存在兼容问题，只修具体兼容问题；
4. 完成 Flash/看门狗和 FreeRTOS 两个固定主题 Fixture，不重做 Modbus；
5. 证明 cancel、retry、restart recovery、CPU/NVENC fallback；
6. 等待 Jovi 提供并人工授权一条真实参考视频，不得自找受版权限制素材；
7. 对每个成片生成 Review Package，并一次只请求 Jovi 审阅一个视频；
8. 生成单 Job prereview；
9. 生成 Phase 1 acceptance manifest 和 Boundary Audit；
10. 全量回归、fresh clone、人工审阅完成后，正式 Gate 只运行一次；
11. Gate 通过后停止，等待单独授权更新 `PROJECT_STATUS.yaml`；
12. 不得在同一任务中进入 Phase 2。

## 本地 Obsidian 记忆同步

本地知识库根目录：

`E:\AI_Tools\Obsidian\Data\notes-personal\codex_memory\03-项目记忆\OpenClaw_VideoFactory\`

要求：

- 只追加或创建 Phase 1 收口记录，不重写历史；
- 更新 `04-落地状态与执行计划.md` 的当前 Phase 1 状态；
- 创建或更新 `06-Phase1本地视频工厂收口.md`；
- 记录主题模式、参考视频模式、Job 生命周期、人工审阅、Gate 输入和剩余阻塞；
- 不写入 Token、绝对私有媒体路径、参考视频内容、原始 Prompt 或模型原始输出；
- Obsidian 位于仓库外，不纳入 Git 提交；
- 每个停止点都同步一次最新状态，避免后续会话重复调研。

## Git 提交与远端规则

- 继续使用当前分支，不创建新分支；
- 开始前 `git fetch` 并确认本地/远端关系；
- 不 reset、clean、自动 stash、rebase 或 force push；
- 不提交 `dist/` 成片、参考视频原件、SQLite Runtime、私有审阅文件、Token、缓存或模型；
- 代码、Schema、Fixture 生成器和脱敏报告可以提交；
- 人工审阅只提交空白示例/Schema，不提交包含私有意见或绝对路径的本地文件；
- 建议提交分组：
  1. `feat(phase1): complete fixed topic fixtures and lifecycle evidence`
  2. `test(phase1): qualify local topic and reference workflows`
  3. `docs(phase1): record prereview and gate evidence`
- 每次提交前运行相应测试、`git diff --check` 和敏感扫描；
- 正式 Gate 前允许推送已验证的代码和测试；
- Gate 结果提交后停止，不合并到 main，不自动创建下一阶段分支。

## 禁止事项

- 不进入 Phase 2；
- 不修改 OpenClaw、飞书、Gateway、Binding、OAuth、Cron；
- 不恢复旧 Codex Provider cache 调试为主线；
- 不引入第二套 Pipeline、DB、Agent 框架或 VideoClaw Backend；
- 不自动下载模型；
- 不自动发布抖音；
- 不用 synthetic reference 代替 Jovi 的真实授权参考视频人工审阅；
- 不把离线测试写成正式阶段通过。

## 可借鉴但不直接引入的 VideoClaw 设计

- 每阶段保留可编辑 Artifact；
- Job 可恢复，失败点可定位；
- 人工审阅是阶段门；
- Pipeline 输入输出显式化。

现有 SQLite、Schema、Review Package 已覆盖这些方向，不建立第二套编排。

## 允许停止的节点

- 需要 Jovi 审阅某个成片；
- 需要 Jovi 提供真实授权参考视频；
- 发现明确代码阻塞且已有最小复现；
- 正式 Gate 已得出唯一结果。

不得在仅完成计划或报告后停止。

## 每次停止时必须汇报

1. 当前分支、HEAD、本地与远端关系；
2. 已完成代码和实际测试；
3. 当前 Job ID、输入模式和状态；
4. 需要 Jovi 做的唯一操作；
5. 未执行项和原因；
6. Obsidian 更新位置；
7. 是否有可安全提交/推送的变更。

## 最终状态

- 本地实现/证据未齐：`PHASE1_COMPLETION_IN_PROGRESS`
- 等待 Jovi 人工审阅：`PHASE1_WAITING_HUMAN_REVIEW:<job>`
- 等待真实授权参考视频：`PHASE1_WAITING_AUTHORIZED_REFERENCE`
- Gate 通过：`PHASE1_LOCAL_VIDEO_FACTORY_READY`
- 精确阻塞：`PHASE1_COMPLETION_BLOCKED:<reason>`
