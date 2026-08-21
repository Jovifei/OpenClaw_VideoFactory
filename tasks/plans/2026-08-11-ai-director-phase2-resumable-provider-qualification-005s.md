# AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S — Luna 可恢复密封重试闭环执行计划

Plan path: `tasks/plans/2026-08-11-ai-director-phase2-resumable-provider-qualification-005s.md`.

> 执行模型：Subagent-Driven。Luna 负责授权边界、集成、真实命令、证据和最终结论；子代理只做实现建议或只读审查，不能替代真实测试、日志或媒体证据。

## 0. 当前真实状态与下一阶段结论

当前必须分成三层陈述：

```text
正式项目阶段
P0 = not_started
P1 = blocked_by_P0
P2 = blocked_by_P1

产品能力
Phase 1.5 = READY
AI Director Phase 2 local = AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED

真实 Provider 资格
005 = BLOCKED_PROVIDER_CACHE_DRIFT
005R = BLOCKED_DETACHED_WORKER_DIED
```

005R 唯一 Worker `session_20260810T145823Z_60876` 在 Desktop 静默、cache 采样、smoke 和 acceptance 之前终止。它没有移动 cache、没有运行 `codex exec`、没有生成真实 Provider MP4。005R 明确禁止在同一任务启动第二个 Worker，因此不能原地继续。

下一任务固定为：

```text
AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S
```

005S 的唯一目标是用一个全新 run namespace、一个 Supervisor 和有限 Worker generation，完成真实 Provider 资格。Worker 可在安全检查点恢复，但 Provider smoke/acceptance 仍各只能执行一次。它不开发新 AI Director、不修改视频 pipeline、不进入 006、Feishu、Cron 或正式 Gate。

成功最高允许状态：

```text
AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED
```

这只是产品证据，不修改 `PROJECT_STATUS.yaml`。只有成功后，下一次独立任务才可规划 `006 Video Agent Orchestration`。

## 1. 从 005R 吸取的强制执行规则

005S 必须解决的不是 Provider 产品代码，而是一次性资格执行顺序：

```text
005R 错误顺序
启动一次性 Worker
→ Worker 仍存活时继续合同审查和修改
→ Worker 被终止
→ 一次授权耗尽

005S 固定顺序
实现 + Pester/故障注入
→ 无 Provider 的真实 Desktop detached canary
→ 两轮只读初审
→ Luna 复现全部检查
→ 创建 fresh fixture，冻结源码和 SHA-256
→ Prelaunch Final Reviewer 审核精确 freeze 并 APPROVED
→ 才启动唯一 Supervisor
→ 启动后禁止编辑或人工终止；只有 Supervisor 可按 lease/checkpoint 恢复 Worker generation
```

硬规则：

- 005R 的仓库报告、Obsidian 记录和外部 run root 全部只读保留，不覆盖、不重命名、不删除。
- 005S 实时 Worker 启动前，必须完成所有源代码审查；启动后不再运行会修改 Worker 源码的子代理。
- `smoke.attempt_count`、`acceptance.attempt_count` 均只能是 0 或 1；命令状态一旦进入 `claimed` 就不能回到 `not_started`。
- 005S 只允许一个 Supervisor、最多三个 Worker generation、一个 smoke 外层命令和一个 acceptance 外层命令。
- Worker generation 与 Provider attempt 必须分离；安全检查点的 Worker 恢复不能重置命令账本。
- “一次 acceptance”指一次 `generate_video.py ... --director-provider codex-cli` 外层事务。该事务内部保留产品合同已有的最多三次受限 provider attempt；它们必须由同一进程、同一 report 和同一 outer command fingerprint 记录，绝不授权第二次外层 acceptance。
- 任一真实尝试失败后只做证据、回滚和收口，不做第二次猜测性尝试。

## 2. 授权边界

### 2.1 执行本计划时新增 Change Request

创建：

```text
reports/change_requests/AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S.json
```

固定字段：

```json
{
  "id": "AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S",
  "mode": "resumable_sealed_real_provider_qualification",
  "does_not_imply_formal_phase_pass": true,
  "authorizes_one_supervisor": true,
  "maximum_worker_generations": 3,
  "maximum_detachment_canaries": 1,
  "maximum_smoke_commands": 1,
  "maximum_acceptance_commands": 1,
  "does_not_authorize_commit_or_push": true,
  "does_not_authorize_oauth_profile_model_changes": true,
  "does_not_authorize_openclaw_feishu_changes": true
}
```

用户明确下达“执行本计划”才构成 005S 的一次新 Worker 授权；仅创建或阅读本计划不构成授权。

### 2.2 允许修改

```text
scripts/provider_qualification.ps1
scripts/provider_qualification_005r.ps1
scripts/lib/ProviderQualification.psm1
scripts/lib/ProviderQualification005R.psm1
tests/Test-ProviderQualification005R.ps1
tests/Test-ProviderQualification005S.ps1
schemas/ops/provider_qualification_run.schema.json
examples/ai_director_provider_qualification_005s/
tasks/todo.md
tasks/lessons.md
tasks/plans/2026-08-11-ai-director-phase2-resumable-provider-qualification-005s.md
reports/*005S*
reports/change_requests/*005S.json
handoff/codex/IMPLEMENTATION_BACKLOG.yaml
.gitignore
指定 Obsidian 页面
```

运行时仅允许写入：

```text
E:/Claude_allow/Download/codex-provider-recovery-005s/
C:/Users/Admin/.codex/models_cache.json
dist/director/director_3aff643f8c6a7ab8/
```

### 2.3 禁止面

- 不修改 `C:/Users/Admin/.codex/config.toml`、`auth.json`、OAuth、Profile、模型选择、Codex 配置或登录状态。
- 不执行 login、upgrade、模型下载、`--model`、`--profile`、`--add-dir`、resume、`workspace-write` 或 `danger-full-access`。
- 不修改 OpenClaw、Feishu、Gateway、Binding、Cron、`PROJECT_STATUS.yaml` 或任何正式 Gate。
- 不修改 `Director.create_storyboard(topic) -> Storyboard`，不修改 `generate_video.py --job/--config/--topic/--topic-file`。
- 不创建第二条视频 pipeline，不改 Renderer、Composition、Pink Pig、TTS、字幕或 FFmpeg 核心。
- 不 commit、push、merge、reset、clean、广泛 stage 或清理用户文件。
- Worker 不得自动关闭、终止、挂起或重启 Codex Desktop。

## 3. 固定架构

### 3.1 资格控制链

```text
Luna / Codex Desktop
  ├─ 本地基线与 Worker 合同测试
  ├─ specialist reviews
  ├─ source_freeze.json
  ├─ harmless detached rehearsal
  └─ 启动唯一 Supervisor + Worker generation 1
             ↓ run_id/lease 双向握手并连续存活
Jovi 正常关闭 Codex Desktop
             ↓
Supervisor 监督 Worker；安全检查点死亡可恢复，最多 generation 3
             ↓
Worker 证明 Desktop quiescent
             ↓
稳定 cache + 健康分类
  ├─ healthy → byte-exact backup，活动 cache 不移动
  └─ degraded → byte-exact backup + quarantine
             ↓
一次 smoke
             ↓
一次 generate_video.py 真实 acceptance
             ↓
合同/媒体/回归机器验证
             ↓
READY_TO_REOPEN.txt 或 BLOCKED.txt
             ↓
Jovi 重开 Codex → Luna 只读 Verify → 独立审核
```

### 3.2 复用而不复制 Worker

将现有 005R 入口抽取为一个 profile 驱动的通用资格执行器：

```powershell
scripts/provider_qualification.ps1 `
  -QualificationProfile 005S `
  -Mode <Preflight|Rehearse|Start|Supervisor|Worker|Status|Verify> `
  [-Apply] `
  [-RunManifest <path>] `
  [-Finalize]
```

`005R` profile 必须被锁为历史只读：它只允许 `Preflight`/`Verify`，任何 `Start` 返回 `provider_qualification_run_closed`。`005S` profile 才允许启动一个 Supervisor；Supervisor 最多创建三个 Worker generation。禁止复制一整套 Worker 代码形成维护分叉。

Profile 配置必须是脚本内固定映射，不能接受自由路径：

| Profile | Task ID | External root | Reports | Fixture |
|---|---|---|---|---|
| `005R` | 原 005R ID | `...005r` | 原 005R 报告 | 原 005R fixture |
| `005S` | `AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S` | `...005s` | 005S 报告 | 005S fixture |

### 3.3 005S 状态合同

扩展现有 Schema，保留 005R 1.0 fixture 兼容；005S 使用 `schema_version: "1.1"`。

状态顺序：

```text
prepared
→ prelaunch_validated
→ source_frozen
→ supervisor_started
→ worker_started
→ supervisor_ready
→ worker_armed
→ waiting_for_desktop_exit
→ desktop_quiescent
→ cache_stable
→ cache_backed_up
→ cache_quarantined（仅 degraded 分支）
→ smoke_started
→ smoke_passed
→ acceptance_started
→ acceptance_passed
→ verification_passed
→ complete_pending_review
→ completed
```

所有非终态允许转入 `failed` 或 `blocked`；`completed/failed/blocked` 为终态。

新增固定字段：

```json
{
  "qualification_profile": "005S",
  "worker_generation": 0,
  "worker_launch_count": 0,
  "lease_id": null,
  "lease_expires_utc": null,
  "heartbeat_sequence": 0,
  "last_checkpoint": "prepared",
  "cache_mutation_started": false,
  "rollback_required": false,
  "smoke": {"status": "not_started", "attempt_count": 0, "command_fingerprint": null},
  "acceptance": {"status": "not_started", "attempt_count": 0, "command_fingerprint": null},
  "source_freeze_sha256": null,
  "cache_strategy": "none",
  "original_cache_sha256": null,
  "active_cache_sha256": null
}
```

命令状态只能是 `not_started/claimed/succeeded/failed/outcome_unknown`；`attempt_count` 只能是 0 或 1。每次状态写入使用同目录临时文件加原子替换；`revision`、`heartbeat_sequence` 单调递增；generation 恢复不得重置命令账本。

Worker 恢复矩阵固定为：

| 中断点 | 允许行为 |
|---|---|
| cache 操作前 | Supervisor 在 lease 过期、旧 PID 不存在且 generation<3 时启动下一代 |
| backup 已验证、quarantine 前 | 对账 original/backup/active hash 后继续或 rollback |
| quarantine 后、smoke 前 | 对账 original/backup/quarantine/active 状态后继续或 rollback |
| smoke=`claimed` | 禁止重跑，标记 `BLOCKED_SMOKE_OUTCOME_UNKNOWN` 并 rollback |
| smoke=`succeeded`、acceptance 前 | 可从检查点继续 acceptance |
| acceptance=`claimed` | 禁止重跑，标记 `BLOCKED_ACCEPTANCE_OUTCOME_UNKNOWN` |
| acceptance=`succeeded`、媒体验证中 | 可恢复幂等媒体/Schema/pytest 验证 |
| state/hash/journal 有歧义 | 只允许 rollback-only，标记 `BLOCKED_CACHE_RECOVERY_AMBIGUOUS` |

## 4. Subagent-Driven 执行模型

在真实 Worker 启动前按顺序执行：

```text
Implementation subagent
  仅处理通用 profile、状态 Schema、Pester 测试
        ↓
Luna 运行 Pester、故障注入和一次真实 Desktop detached canary
        ↓ canary 通过并重开 Codex
Contract reviewer（只读）
  检查状态、one-shot、run_id、历史 005R 关闭合同
        ↓
Security reviewer（只读）
  检查路径、reparse、lease takeover、hash rollback、raw/credential 边界
        ↓
Luna 复现 reviewer 的全部 FAIL
        ↓
创建 fresh fixture 并冻结 source_freeze_sha256
        ↓
Prelaunch final reviewer 审核该精确 freeze（只读）
        ↓ APPROVED
唯一 Supervisor 启动
```

真实 Supervisor 启动后：

- 不再派实现子代理；
- 不编辑 Supervisor、Worker、Schema、fixture 或 provider adapter；
- reviewer 只能在 Worker 终态且 Jovi 重开 Desktop 后启动；
- 子代理的 `APPROVED` 不是运行证据，Luna 必须复现命令和核对产物。

## 5. 十四阶段闭环执行

### [1/14] 只读冻结真实基线并核对 005R 终态

目的：证明 005S 从未覆盖 005R，并锁定当前 dirty worktree。

先读取：

```text
START_HERE_CODEX.md
PROJECT_STATUS.yaml
AGENTS.md
tasks/lessons.md
005/005R 计划、Change Request、JSON 和最终报告
Obsidian 04/07/08
```

命令：

```powershell
$PinkPigPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
git branch --show-current
git rev-parse HEAD
git diff --cached --quiet
git status --short --untracked-files=all
```

预期：

```text
branch = codex/ai-director-video-factory-phase2-001
HEAD = 76180a59ea662bdf168d88baaeb777d3e8eb59ef
index_empty_exit = 0
```

六个受保护 dirty 文件必须保持：

```text
PROJECT_STATUS.yaml
reports/P0_ACCEPTANCE_MATRIX_V2.yaml
scripts/analysis_request.py
scripts/analyzer_mcp.py
scripts/mcp_ingest_attachment.py
scripts/media_action_ticket.py
```

其 SHA-256 必须分别等于：

```text
cd0dc97280ed86abac748dceaff73a45587a92656d4481e782b37aa33002785d
acccf9e9440776583857c67ba15094ef461f1b61dfe0ebd436fa68b4e3b6905e
68bdd12ebc45d92fff17ae01dec7f6c4efcd0cef3e89aeb68434ec9ebed9ea1d
bcf09db631eed87316c4d2b0664abc159470860b0d3e84c7e8c3460071e09d90
313f00b8f855faaf2ad22cd01a61d987670d0ff02ff4c9de3d57970039a7d52b
794b0ed4dea1fb18eb52371d1fcddc4724d8d781b141b09214545e5af19699e5
```

只读计算以下 005R 证据、源码及外部 run root 的文件清单和 SHA-256；[1/14] 不写任何仓库文件，结果在 [2/14] 创建 Change Request 后才持久化：

```text
reports/*005R*
reports/change_requests/*005R.json
tasks/plans/*005r.md
scripts/provider_qualification_005r.ps1
scripts/lib/ProviderQualification005R.psm1
schemas/ops/provider_qualification_run.schema.json
tests/Test-ProviderQualification005R.ps1
E:/Claude_allow/Download/codex-provider-recovery-005r/session_20260810T145823Z_60876/
```

[1/14] 完全只读：不更新 todo、backlog、`.gitignore`、报告或 Obsidian。

[1/14] 不运行 pytest、Python import 或任何可能创建 `__pycache__`/`.pytest_cache` 的命令。只读基线不一致时状态为 `BASELINE_BLOCKED`，不得访问 cache，不得继续。

### [2/14] 创建 005S Change Request、namespace 和任务账本

第一项仓库写入必须是创建 Change Request。Change Request 建立后，才允许写入 [1/14] 的基线/005R pre-refactor hash 清单；然后运行可能产生本地 cache 的基线测试，再在 `tasks/todo.md` 追加“005R TERMINAL BLOCKED”和 14 阶段 checklist，状态为 `IN PROGRESS`，并更新 backlog。

基线测试：

```powershell
& $PinkPigPython -m pytest tests/director -q
& $PinkPigPython -m pytest tests/video -q
& $PinkPigPython -m pytest video_factory/tests -q
& $PinkPigPython -m pytest `
  tests/test_p1_candidate_cli.py `
  tests/test_p1_candidate_pipeline.py `
  tests/test_p1_candidate_media.py `
  tests/test_p1_candidate_render.py `
  tests/test_p1_candidate_delivery.py `
  tests/test_p1_candidate_inventory.py `
  tests/test_p1_candidate_state.py `
  tests/test_p1_final_audit.py -q
```

最低验收：Director 47、Video 273、Video Factory 5、legacy 56 passed/1 skipped/13 subtests；不得减少现有测试。失败状态：`BASELINE_BLOCKED`，不得实现 Worker。

更新 backlog：

```yaml
provider_005:
  status: blocked_provider_cache_drift
provider_005r:
  status: blocked_detached_worker_died
provider_005s:
  status: planned_resumable_sealed_retry
  depends_on: provider_005r
```

外部根目录必须是全新：

```text
E:/Claude_allow/Download/codex-provider-recovery-005s/
```

如果它已包含 active run、`smoke.attempt_count=1` 或 `acceptance.attempt_count=1`，停止为 `BLOCKED_FRESH_EVIDENCE_REQUIRED`；不得删除或复用。

`.gitignore` 只追加本任务精确例外，不删除或重排旧规则。

审核门：Change Request JSON 可解析，允许/禁止路径完整，旧 005R hash 清单存在。

### [3/14] 将 005R Worker 收敛为 profile 驱动的通用执行器

实现：

```text
scripts/provider_qualification.ps1
scripts/lib/ProviderQualification.psm1
tests/Test-ProviderQualification005S.ps1
```

现有 005R 入口改为薄兼容入口；005R `Start` 永久 fail-closed。不要复制完整 Worker 代码。

必须实现：

- 固定 `005R/005S` profile 映射；拒绝未知 profile。
- 参数数组、固定 Windows PowerShell/Python、`Start-Process -WindowStyle Hidden`。
- run root containment、绝对路径/`..`/reparse/junction/symlink 拒绝。
- active-run lock 使用原子 create-new，内容绑定 task_id/run_id/supervisor PID。只有 Supervisor 与 Worker 全部退出且 state 已是终态时，才原子转换为只读 terminal ledger；陈旧 lock 必须 fail-closed，不能静默删除。
- Supervisor/Worker 的 run_id、generation、lease_id 双向握手。
- Supervisor 启动意图原子持久化；只有 Supervisor 能按恢复矩阵创建 Worker generation。
- lease 必须绑定 run_id、generation、PID 和 heartbeat；只有旧 PID 不存在且 lease 超时才能接管。
- generation 最多 3；恢复不得重置 smoke/acceptance ledger。
- `source_freeze.json` 绑定 entry/module/schema/fixture/provider adapter/generate_video 的 SHA-256。
- Supervisor/Worker 启动后和每个高风险阶段前复核 source freeze；漂移立即 blocked，不继续。
- 默认 `Verify` 只读；`-Finalize` 仍要求 run-bound `FINAL_REVIEW_APPROVED.txt`。
- 不输出完整命令行、npm 绝对路径、cache 内容、prompt、model output、stdout/stderr 或凭据。

兼容门：005R 历史 state/report 仍能通过其 1.0 Schema 和只读 Verify；005R 不能再 Start。

失败状态：`WORKER_CONTRACT_FAILED`。

### [4/14] Pester、故障注入与 detached liveness rehearsal

所有单元测试使用 `TestDrive:` 或外部 005S rehearsal 子目录；不得读取真实 cache。

覆盖至少：

- 005R Start 被拒绝；005S 只允许一个 Supervisor、最多三个 Worker generation。
- 非法 profile、manifest task/run mismatch、旧 report 混入被拒绝。
- write-once 字段不可回退；revision 单调。
- active lock、路径逃逸、reparse、hash drift、backup mismatch、rollback。
- 错误 Supervisor/Worker run_id 或 lease marker、缺 marker、正确 marker。
- Worker 在安全阶段死亡时按 lease/generation 恢复；超过上限写 `BLOCKED_WORKER_RESTART_LIMIT`。
- Worker 在 backup 后、quarantine 前，quarantine 后、smoke 前，smoke claimed，smoke succeeded，acceptance claimed，acceptance succeeded 后分别故障注入。
- Supervisor 死亡写 `BLOCKED_SUPERVISOR_DIED`，不能由 Worker 越权拉起第二 Supervisor。
- smoke/acceptance command count 最大 1。
- raw 临时文件递归检测和清理失败 fail-closed。
- config/auth/六 dirty hash drift fail-closed。
- 005S Verify 不能读取或完成 005R run。
- schema 1.0/1.1 兼容。

命令：

```powershell
Invoke-Pester tests/Test-ProviderQualification005R.ps1,tests/Test-ProviderQualification005S.ps1 -PassThru

$parseErrors = @()
[void][System.Management.Automation.Language.Parser]::ParseFile(
  'scripts/provider_qualification.ps1',
  [ref]$null,
  [ref]$parseErrors
)
if ($parseErrors.Count -ne 0) { throw 'powershell_parse_failed' }

rg -n "Stop-Process|taskkill|danger-full-access|workspace-write|--model|--profile|--add-dir|codex login|codex upgrade|resume" `
  scripts/provider_qualification.ps1 `
  scripts/lib/ProviderQualification.psm1
```

预期：Pester 总数大于现有 12 且全通过；parse 0；禁用命令无匹配。

实现 `-Mode Rehearse -Apply`：只启动一个 30 秒 dummy Worker 和 Supervisor，在外部 rehearsal 目录持续写 heartbeat。它不得读取 cache、运行 Codex、读取 config/auth 或生成真实 Provider run。

Rehearsal 必须真实经过一次 Desktop 关闭：

1. 等待 `CANARY_ARMED_TO_CLOSE_DESKTOP.txt`，确认 run_id/lease marker 和两个 PID。
2. Luna 告知 Jovi 正常关闭整个 Codex Desktop。
3. dummy Supervisor/Worker 在 Desktop 退出后继续完成至少 3 个 heartbeat 和 20 秒存活窗口。
4. 写 `CANARY_PASSED.txt` 或 `CANARY_BLOCKED.txt` 后，Jovi 重开 Codex。
5. Luna 只读复核 canary state、PID 历史和 heartbeat，再继续 [5/14]。

Canary 只允许一次；失败状态 `DETACHED_REHEARSAL_FAILED`，不得启动资格 Supervisor。Canary 成功不构成 Provider、cache 或媒体证据。

失败状态：`DETACHED_REHEARSAL_FAILED`。不得启动真实 Worker。

### [5/14] 启动前两轮初审与 Luna 复现

并行启动：

1. Contract reviewer：状态转换、one-shot、005R 关闭、run/report 绑定。
2. Security reviewer：路径、reparse、lease takeover、cache rollback、raw/credential、禁用命令。

Luna 对所有 FAIL 逐项复现；如需改代码，修改后重新执行 [4/14]，再开新的只读复审。不得在 reviewer 仍为 `CHANGES_REQUIRED` 时生成 source freeze。本阶段只做初审，不生成 Prelaunch Final Audit。

### [6/14] 创建 fresh fixture、证据隔离和 source freeze

新增：

```text
examples/ai_director_provider_qualification_005s/
├── README.md
├── topic.txt
└── factual_brief.json
```

`topic.txt` 固定为：

```text
用小粉猪解释 Modbus RTU：主从通信、帧结构、CRC 与现场排错
```

NFKC 后：

```text
用小粉猪解释 Modbus RTU:主从通信、帧结构、CRC 与现场排错
```

固定 SHA-256 与 ID：

```text
topic_sha256 = 3aff643f8c6a7ab8f55f840bd7e3d8e61b583665e5c824bfa93f92c08db22d49
job_id = director_3aff643f8c6a7ab8
script_id = script_3aff643f8c6a7ab8
```

Factual brief 只复制现有 verified Modbus 一手来源和已经核验的 claims，并替换 topic digest；禁止新增未经验证结论。fixture 不含 Storyboard、asset ID、路径、prompt 或模型输出。

运行前必须确认：

```text
dist/director/director_3aff643f8c6a7ab8/
```

不存在。若存在，停止为 `BLOCKED_FRESH_JOB_REQUIRED`；不得删除或复用。

生成 source freeze：

```text
entry/module/schema/tests/fixture
generate_video.py
src/factory/director/provider.py
src/factory/director/ai_director.py
schemas/video/director_draft.schema.json
```

记录相对路径、bytes、SHA-256；整个 freeze manifest 再计算 SHA-256，写入初始 state。冻结后禁止编辑这些文件。

冻结后才启动新的 Prelaunch Final Reviewer。它必须审核这份精确 `source_freeze_sha256`，并检查：

- Pester/parse/static scan/真实 Desktop canary 原始结果；
- profile/source freeze 的每个文件 hash；
- 005R 不可启动；
- 005S 一个 Supervisor、最多三个 generation、一个 smoke、一个 acceptance；
- Supervisor 启动后没有代码审查或编辑步骤；
- lease/checkpoint/rollback/终态状态完整。

Reviewer 只返回 `APPROVED` 或 `CHANGES_REQUIRED`，不得写文件。Luna 复核其结论后，生成绑定当前 `source_freeze_sha256` 和 reviewer-result SHA-256 的：

```text
reports/CODEX_PROVIDER_PRELAUNCH_AUDIT_005S.json
```

如 reviewer 要求任何源码修改，source freeze 立即失效；必须修改、重跑 [4/14]、重新执行 [5/14]、重新生成 freeze，再开全新 Final Reviewer。失败状态：`PRELAUNCH_REVIEW_FAILED`。

### [7/14] Live Preflight、唯一 Supervisor 启动和 armed 交接

先运行：

```powershell
powershell -File scripts/provider_qualification.ps1 `
  -QualificationProfile 005S `
  -Mode Preflight
```

Preflight 必须验证：

- branch/HEAD/index 和六 dirty hash；
- source freeze 完整；
- Prelaunch audit 为当前 source freeze 的 `APPROVED`；
- PATH 首命中 npm Codex CLI；
- CLI 版本和 `exec --help` 支持实际使用的全部 flags；
- config/auth 只记录 hash/bytes，不读出内容；
- Desktop process class 可识别；
- 外部根目录安全且无 active run；
- fixture/job 目录 fresh；
- cache 未被移动。

启动唯一 Supervisor（它创建 generation 1）：

```powershell
powershell -File scripts/provider_qualification.ps1 `
  -QualificationProfile 005S `
  -Mode Start `
  -Apply
```

Supervisor 启动意图和 generation 1 lease 必须在 `Start-Process` 前原子持久化。后续 generation 只能由 Supervisor 按恢复矩阵创建。

启动后先不要关闭 Desktop。Luna 必须等待：

```text
SUPERVISOR_READY.txt 内容 = supervisor_ready:<run_id>
WORKER_READY.txt 内容 = worker_ready:<run_id>:<generation>:<lease_id>
worker.pid 与 supervisor.pid 均存活
连续 3 个 heartbeat 样本 revision/UTC 前进
LIVE_WORKER_ARMED.txt 已写入
REOPEN_NOT_BEFORE_UTC.txt 已写入，内容绑定 run_id 和启动后 30 分钟 UTC 截止时间
```

armed 前 Worker 死亡由 Supervisor 在 generation 上限内恢复；Supervisor 死亡、generation 超限或无法 armed 时写 `BLOCKED_WORKER_NOT_ARMED` / `BLOCKED_SUPERVISOR_DIED` / `BLOCKED_WORKER_RESTART_LIMIT`。不得人工启动第二个 Supervisor。

armed 后 Luna 向 Jovi 只发送：

```text
1. 正常关闭 Codex Desktop 整个应用，不只关闭 app-server。
2. 不要终止外部 Supervisor 或 Worker。
3. 不要重新打开 Codex，直到外部 run root 出现 READY_TO_REOPEN.txt 或 BLOCKED.txt。
4. 若两个 marker 都没有，等到 REOPEN_NOT_BEFORE_UTC.txt 的截止时间后可以重开 Codex。
5. 超时重开后只允许执行 `-Mode Status` 和只读 `-Mode Verify`；不得启动第二 Supervisor、Worker、smoke 或 acceptance。
6. 重开后把 run_manifest.json 的路径交给 Luna 继续 Verify。
```

### [8/14] Desktop quiescence、稳定 cache 和健康分流

Worker 必须证明；Supervisor 持续监督 heartbeat/lease：

- captured Desktop 父 PID 已退出；
- 不存在同 WindowsApps package 的 ChatGPT/Codex Desktop；
- 不存在该 package 的 `app-server`；
- 连续 10 次、每次 1 秒均无 Desktop 进程；
- cache 连续 5 次、每次 1 秒的 SHA-256、bytes、LastWriteTime 完全一致。

健康分流只记录结构，不记录 models 内容：

```text
healthy:
  JSON valid
  models_count > 0
  missing_base_instructions_count = 0
  strategy = backup_only

degraded:
  JSON invalid，或 models_count = 0，或 missing_base_instructions_count > 0
  strategy = quarantine_rebuild
```

cache 不存在或为 reparse：`BLOCKED_PROVIDER_CACHE_MISSING` / `BLOCKED_PROVIDER_CACHE_PATH_UNSAFE`，不得 smoke。

任一进程重现或 hash 漂移：`BLOCKED_DESKTOP_NOT_QUIESCENT` / `BLOCKED_PROVIDER_CACHE_DRIFT`，不得复制或移动 cache。

### [9/14] Byte-exact backup 与条件 quarantine

外部目录：

```text
<run_root>/cache-<original_sha前16位>/
├── models_cache.original.json
├── rollback_journal.json
└── quarantine/models_cache.json   # 仅 degraded 分支
```

共同步骤：

1. 再次确认 Desktop quiescent。
2. 重读活动 cache hash，必须等于稳定样本 hash。
3. 复制到 `models_cache.original.json`。
4. 验证 backup hash 等于 original hash。
5. 重新检查 config/auth、source freeze、六 dirty hash 和 index。

健康分支：不移动活动 cache，状态进入 `cache_backed_up`。

degraded 分支：

1. backup 成功后第二次读取活动 hash；
2. 完全一致才移动到 quarantine；
3. 验证 quarantine hash；
4. 确认活动路径不存在；
5. 状态进入 `cache_quarantined`。

任何异常：若活动 cache 已移走且 quarantine hash 正确，byte-exact 恢复；验证恢复 hash；保留 backup/journal；终态 `BLOCKED_PROVIDER_RECOVERY`。

禁止编辑 cache JSON、补字段、复制他机 cache 或删除 original backup。

### [10/14] 一次真实 Codex smoke

调用前原子写 `smoke.status=claimed`、`attempt_count=1`、command fingerprint 和 `smoke_started`。固定命令：

```text
codex exec
--ephemeral
--sandbox read-only
--skip-git-repo-check
--ignore-user-config
--color never
--output-schema <director_draft.schema.json>
--output-last-message <external temp draft>
-C <external empty smoke workdir>
-
```

Prompt 通过 stdin，只要求 5 幕中文常青 Modbus Draft。验收：exit 0、合法 JSON、Draft Schema 通过、5–9 scenes。

Smoke 报告只保存：run_id、exit code、elapsed、Draft SHA/bytes/scene count、Schema status、cache before/after hash、model count、missing count。raw Draft/stdout/stderr 删除后递归复核为 0。

Smoke command 启动后若 Worker 消失而没有可验证 exit/report，写 `BLOCKED_SMOKE_OUTCOME_UNKNOWN`，绝不重跑。Supervisor 只能等待已记录的 Provider PID 自然退出；PID 仍活跃时写 `BLOCKED_PROVIDER_PROCESS_ACTIVE`，不得移动 cache。进程退出且 cache 再次稳定后才允许按 journal rollback。

Smoke 后 active cache 必须 JSON valid、models>0、missing `base_instructions`=0。明确失败时：

- degraded 分支恢复原 cache hash；
- healthy 分支若活动 hash 未变则保留；若 hash 已变，先把变化后的 cache 移入外部 evidence root，再从 original backup byte-exact 恢复；
- 新生成/异常 cache 移至外部 evidence root；
- 写 `REAL_PROVIDER_BLOCKED_SMOKE`；
- 不执行 acceptance，不做第二 smoke。

### [11/14] 一次真实 AI Director acceptance

调用前原子写 `acceptance.status=claimed`、`attempt_count=1`、command fingerprint 和 `acceptance_started`。只执行一次外层命令：

```powershell
& $PinkPigPython generate_video.py `
  --topic-file examples/ai_director_provider_qualification_005s/topic.txt `
  --factual-brief examples/ai_director_provider_qualification_005s/factual_brief.json `
  --director-provider codex-cli `
  --output-name pink_pig_modbus_ai_provider_005s.mp4
```

应用内部既有最多三次受限 provider attempt 可以保留，必须属于同一个 outer command fingerprint，并在同一 `director_report.json` 记录；禁止运行第二次外层命令。外层命令退出后，无论内部实际用了 1、2 或 3 次 attempt，本任务的 acceptance ledger 都保持 `attempt_count=1`。

Worker 在 acceptance command 中死亡且无法证明退出结果时写 `BLOCKED_ACCEPTANCE_OUTCOME_UNKNOWN`，不得重跑。明确失败必须留下当前 topic 的 sanitized director report 和终态 `failed` job state；不能停在 planning/rendering/quality_check，不能引用 003/005/005R 或 fake report。终态：`PROVIDER_RECOVERED_ACCEPTANCE_FAILED`。

成功预期目录：

```text
dist/director/director_3aff643f8c6a7ab8/
```

### [12/14] 合同、媒体、Pink Pig 和完整回归

Worker 自动执行机器门：

- DirectorScript、Storyboard、asset selection、director report、VideoJob state、render report、quality report 全部 Schema-valid。
- provider=`codex-cli`，attempts 1–3，error=null，score>=85。
- 5–9 beats/scenes，首 hook、末 summary，state=`completed`，factual=`verified`。
- AI Draft/Script 没有 asset ID/path；最终素材全部来自 Registry，至少四张不同知识插图。
- Pink Pig/style profile/Composition/subtitle/TTS gate 全部通过。
- TTS segment 数与 scene 数一致。

媒体命令：

```powershell
ffmpeg -v error -i <005s-mp4> -f null -
ffprobe -v error -show_streams -show_format -of json <005s-mp4>
ffmpeg -i <005s-mp4> -af volumedetect -f null NUL
```

必须：1080x1920、30 FPS、H.264、AAC、25–60 秒、decode exit 0、`max_volume > -50 dB`，ffprobe 与 render report 一致。字幕 52–60px、最多两行、位于 y=1120..1580；content 位于 y=240..1040。

按每幕中点抽帧到外部 evidence root；Worker 只记录 hash/相对引用，不作主观审美通过。

完整回归：

```powershell
& $PinkPigPython -m pytest tests/director -q
& $PinkPigPython -m pytest tests/video -q
& $PinkPigPython -m pytest video_factory/tests -q
& $PinkPigPython -m pytest `
  tests/test_p1_candidate_cli.py `
  tests/test_p1_candidate_pipeline.py `
  tests/test_p1_candidate_media.py `
  tests/test_p1_candidate_render.py `
  tests/test_p1_candidate_delivery.py `
  tests/test_p1_candidate_inventory.py `
  tests/test_p1_candidate_state.py `
  tests/test_p1_final_audit.py -q
```

验收：Director 不低于 47、Video 恰为 273、Video Factory 恰为 5、legacy 方法数不减少且无失败。

失败不重跑 Provider，状态 `REAL_PROVIDER_MEDIA_OR_REGRESSION_FAILED`。全部通过后写 `READY_TO_REOPEN.txt` 和 `complete_pending_review`。

### [13/14] 重开 Codex、只读 Verify 与独立审核

Jovi 看到 `READY_TO_REOPEN.txt` 或 `BLOCKED.txt` 后重开 Codex；若两个 marker 均缺失，只能在 `REOPEN_NOT_BEFORE_UTC.txt` 截止时间之后重开，并先运行只读 `Status` 判断 Supervisor/Worker 是否死亡或卡住。

Luna 首先执行：

```powershell
powershell -File scripts/provider_qualification.ps1 `
  -QualificationProfile 005S `
  -Mode Verify `
  -RunManifest <external run_manifest.json>
```

Verify 必须只读，并复核 run_id/task_id/source freeze、one-shot counts、backup/quarantine/active cache、config/auth、六 dirty hash、index、raw temp、全部 reports 与 job artifacts。

并行启动三个只读 specialist：

1. Provider/State reviewer：Supervisor/lease/generation/Desktop/cache/smoke/acceptance/state/report。
2. Media/Pink Pig reviewer：逐幕抽帧、字幕、字体、插图、角色位置、TTS、音视频。
3. Git/Environment reviewer：source freeze、config/auth、cache backup、dirty/index、禁止面、命令次数。

Luna 复现所有 FAIL，再启动全新的 Final Reviewer。任何 reviewer 要求重跑 Worker/smoke/acceptance，必须拒绝。

Final Reviewer 只读返回 `APPROVED` 和证据摘要，不能写任何 marker。Luna 复现结论、计算 reviewer result SHA-256 后，才原子写外部 run-bound：

```text
FINAL_REVIEW_APPROVED.txt = final_review_approved:<run_id>:<review_result_sha256>
```

然后 Luna 执行一次 `Verify -Finalize`。失败为 `FAIL_REVIEW`，不得重跑 Provider。

### [14/14] 报告、Obsidian、Git 边界与停止

生成：

```text
reports/CODEX_PROVIDER_PRELAUNCH_AUDIT_005S.json
reports/CODEX_DESKTOP_QUIESCENCE_AUDIT_005S.json
reports/CODEX_PROVIDER_DETACHED_RUN_005S.json
reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005S.md
```

最终报告包含：

1. 正式阶段/产品阶段/Provider 资格三层状态；
2. 005 cache drift、005R Worker death 与 005S 新授权隔离；
3. source freeze、rehearsal、prelaunch review；
4. Supervisor/Worker armed、generation history 与 Desktop quiescence；
5. cache 健康分流、backup/quarantine/rollback hash；
6. 单次 smoke 和单次 acceptance 证据；
7. Script/Storyboard/Asset/State/Reports；
8. MP4/TTS/字幕/Composition/Pink Pig/抽帧；
9. 完整测试数量；
10. 三个 specialist 与 final reviewer；
11. config/auth/六 dirty/index/禁止面；
12. 未 commit/push、正式 Gate 未改变；
13. original cache backup 保留和回滚说明；
14. 下一任务。

`.gitignore` 精确例外：

```gitignore
!tasks/plans/2026-08-11-ai-director-phase2-resumable-provider-qualification-005s.md
!reports/CODEX_PROVIDER_PRELAUNCH_AUDIT_005S.json
!reports/CODEX_DESKTOP_QUIESCENCE_AUDIT_005S.json
!reports/CODEX_PROVIDER_DETACHED_RUN_005S.json
!reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005S.md
!reports/change_requests/AI-DIRECTOR-PHASE2-RESUMABLE-PROVIDER-QUALIFICATION-005S.json
```

Obsidian：

```text
04-落地状态与执行计划.md
07-AI-Director-Provider真实资格.md
08-AI-Director-Provider脱离桌面验收.md
09-AI-Director-Provider资格重试005S.md
```

写法：04/07/08 只追加新的 authoritative snapshot，不重写历史；08 明确 `WATCHDOG_READY` 修复在 005R 后完成、此前未经过真实 Worker；09 记录 005S 全部证据和当前分支/HEAD。Obsidian 写入失败必须终态为 `BLOCKED_OBSIDIAN_DELIVERY`，不得写成功标记。

最终检查：

```powershell
git diff --check
git diff --cached --quiet
git status --short --untracked-files=all
git check-ignore -q -- <六个005S交付文件逐个检查>
```

六个交付文件的 `git check-ignore` 预期 exit 1。六个 protected dirty 文件 hash 与 [1/14] 一致。没有 Provider 以外的禁止面修改。

## 6. 状态判定表

| 证据 | 最终状态 |
|---|---|
| 本地基线失败 | `BASELINE_BLOCKED` |
| Worker/Pester/Schema 失败 | `WORKER_CONTRACT_FAILED` |
| detached rehearsal 失败 | `DETACHED_REHEARSAL_FAILED` |
| prelaunch review 未通过 | `PRELAUNCH_REVIEW_FAILED` |
| fixture/job/run namespace 非 fresh | `BLOCKED_FRESH_EVIDENCE_REQUIRED` |
| 目标 stable job 目录已存在 | `BLOCKED_FRESH_JOB_REQUIRED` |
| live Worker 未 armed | `BLOCKED_WORKER_NOT_ARMED` |
| Supervisor 提前退出 | `BLOCKED_SUPERVISOR_DIED` |
| Worker generation 超限 | `BLOCKED_WORKER_RESTART_LIMIT` |
| Provider 子进程持续存活，不能安全 rollback | `BLOCKED_PROVIDER_PROCESS_ACTIVE` |
| smoke 结果无法判定 | `BLOCKED_SMOKE_OUTCOME_UNKNOWN` |
| acceptance 结果无法判定 | `BLOCKED_ACCEPTANCE_OUTCOME_UNKNOWN` |
| cache/journal 恢复歧义 | `BLOCKED_CACHE_RECOVERY_AMBIGUOUS` |
| Desktop 未关闭/不静默 | `BLOCKED_DESKTOP_NOT_QUIESCENT` |
| cache 不存在 | `BLOCKED_PROVIDER_CACHE_MISSING` |
| cache 路径为 reparse/越界 | `BLOCKED_PROVIDER_CACHE_PATH_UNSAFE` |
| cache hash/size/mtime 漂移 | `BLOCKED_PROVIDER_CACHE_DRIFT` |
| backup/quarantine/rollback 失败 | `BLOCKED_PROVIDER_RECOVERY` |
| 单次 smoke 失败 | `REAL_PROVIDER_BLOCKED_SMOKE` |
| 单次 acceptance 失败 | `PROVIDER_RECOVERED_ACCEPTANCE_FAILED` |
| 媒体/合同/回归失败 | `REAL_PROVIDER_MEDIA_OR_REGRESSION_FAILED` |
| 独立审核失败 | `FAIL_REVIEW` |
| Obsidian 交付失败 | `BLOCKED_OBSIDIAN_DELIVERY` |
| 所有真实证据与 final review 通过 | `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED` |

## 7. 成功后的下一步与剩余债务

005S 成功后只允许规划：

```text
006 Video Agent Orchestration
```

仍然不是 Feishu、Cron、自动运营或正式 P2 Gate。剩余债务必须写入报告：

- 正式 P0/P1/P2 Gate 未改变；
- OpenClaw 长期 Job 数据库、恢复、取消和调度仍属于后续正式路线；
- 真实 Provider 目前只有 Codex CLI，一个 Provider 通过不等于多 Provider 容灾；
- AI 热点仍需事件日期和独立来源合同；
- style quality 仍没有像素级自动审核；
- SVG-only pose fallback 仍存在；
- Feishu 接入、Cron 和自动运营尚未开始；
- original cache backup 在明确清理任务前保留，不在 005S 删除。

只有全部门禁通过，最终报告末尾写：

```text
AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED
```

任何失败都写最具体 BLOCKED/FAIL 状态。报告和 Obsidian 完成后立即停止，不进入 006。
