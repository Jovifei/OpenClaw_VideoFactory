# AI-DIRECTOR-PHASE2-PROVIDER-RECOVERY-QUALIFICATION-005 — Luna 执行计划

> 本计划由 `writing-plans` Skill 编写。Luna 执行时必须采用“主代理单写、子代理只读审核”的方式：Provider/cache 变更与真实命令只能由 Luna 串行执行；子代理不得修改 Codex 环境、仓库或 Obsidian。

## 一、目标、当前事实与成功边界

目标：在不修改 Video Factory 实现、不修改 Codex OAuth/Profile/model/config 的前提下，对已确认损坏的 Direct Codex CLI 派生模型缓存做一次可逆恢复，然后完成一次隔离 Provider smoke 和一次真实 AI Director 端到端资格验收。

当前真实状态：

```text
Phase 1.5 Composition / Pink Pig / Renderer       READY
Phase 2 本地 Script/Storyboard/Asset/Job 实现      COMPLETE LOCALLY
Remediation 004 生命周期与单 pipeline 修复         APPROVED
Direct Codex Provider 真实验收                     BLOCKED
```

004 已证明：

- `tests/director` 47 passed；`tests/video` 273 passed；`video_factory/tests` 5 passed。
- legacy 57 个测试方法保留，56 passed、1 Windows symlink skip、13 subtests。
- 唯一可调用视频链是 `generate_video.py -> video_factory.pipeline -> FFmpeg`。
- 非合同异常会原子写入 `failed`，Director 不再复用陈旧报告。
- fake-provider MP4 只证明本地实现；不能作为真实 Provider 证据。

003 已确认的 Provider blocker：

- 真实 `codex exec` 返回 `director_provider_failed`、exit code 1。
- 内容无关结构探针发现 `models_cache.json` 为合法 JSON，但 9/9 模型条目缺少 `base_instructions`。
- 项目代码不读取或修改该缓存；OAuth、Profile、模型选择和 OpenClaw 均未动。

正式阶段仍保持：

```yaml
P0: not_started
P1: blocked_by_P0
P2: blocked_by_P1
```

本任务成功后的最高允许产品状态：

```text
AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED
```

该状态只表示当前本机的 Direct Codex Provider 与真实 AI 视频链通过资格验收；不得写 `AI_DIRECTOR_PHASE2_READY`，不得修改 `PROJECT_STATUS.yaml`，不得声称正式 P2 Gate 通过。

后续顺序固定：

```text
005 Provider Recovery + Real AI Qualification
  -> 006 Video Agent Orchestration
  -> 007 Feishu 调用
  -> 008 自动运营
```

## 二、架构和执行决策

保持主链不变：

```text
Topic + verified factual brief
  -> CodexCliDirectorProvider
  -> DirectorScript
  -> StoryboardAssembler
  -> Registry AssetSelector
  -> existing run_job()
  -> Composition + Pink Pig gate
  -> TTS + subtitle + FFmpeg
  -> MP4 + reports + completed state
```

锁定决策：

1. 不修改 `generate_video.py`、`src/factory/director/`、`video_factory/`、Schema 或测试实现。真实验收暴露代码缺陷时，记录 `FAIL_IMPLEMENTATION` 并停止，另开修复任务。
2. 唯一允许的 Provider 环境写操作是对精确文件 `C:/Users/Admin/.codex/models_cache.json` 做哈希绑定的备份、隔离，以及允许当前已安装 Codex CLI 自动重建该派生缓存。禁止手工补字段。
3. 禁止修改或读取内容：`auth.json`、OAuth、Profile、模型选择、`config.toml`、OpenClaw Runtime。对这些文件只允许存在性、元数据和 SHA-256 对照。
4. 不登录、不升级 CLI、不下载模型、不传 `--model`、`--profile`、`--add-dir`，不用 `workspace-write`、`danger-full-access`、resume 或用户配置覆盖。
5. 只允许一个隔离 smoke 外层命令和一个真实端到端外层命令。应用内部既有最多三次结构化生成尝试可以发生，但必须由 `director_report.attempts` 如实记录；失败后不得人工再跑第二遍。
6. recovery smoke、真实 Provider、媒体渲染全部串行。任何子代理只能读，不得执行 Provider 或移动缓存。
7. 不 stage、commit、push、merge、reset、clean；不修改 OpenClaw、Feishu、Gateway、Binding、Cron、自动运营或正式 Gate。

## 三、允许路径和交付物

执行前新增 Change Request：

```text
reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-RECOVERY-QUALIFICATION-005.json
```

它必须声明：

```json
{
  "id": "AI-DIRECTOR-PHASE2-PROVIDER-RECOVERY-QUALIFICATION-005",
  "mode": "provider_recovery_and_real_qualification",
  "does_not_imply_phase_pass": true,
  "does_not_authorize_project_implementation_changes": true,
  "does_not_authorize_oauth_profile_model_config_changes": true,
  "does_not_authorize_openclaw_or_feishu_changes": true,
  "does_not_authorize_commit_or_push": true,
  "maximum_isolated_smoke_commands": 1,
  "maximum_real_acceptance_commands": 1
}
```

仓库内允许写入：

- 本 Change Request、`tasks/todo.md`、本计划和 005 报告。
- `examples/ai_director_provider_qualification_005/` 下的 topic、verified factual brief 和 README；不得放人工 Storyboard。
- `.gitignore` 的精确跟踪例外。
- `handoff/codex/IMPLEMENTATION_BACKLOG.yaml`、`video_factory/README.md`、`src/factory/director/README.md` 的结果说明。
- 指定 Obsidian 页面。

仓库外允许写入：

```text
E:/Claude_allow/Download/codex-provider-recovery-005/<cache_sha256前16位>/
```

该目录只存本机备份、隔离缓存、临时 smoke 文件和本机 rollback journal，不进入 Git、报告正文或 Obsidian。原始缓存内容、原始 prompt/output/stdout/stderr 不得进入仓库。

005 交付：

```text
reports/CODEX_PROVIDER_ENVIRONMENT_AUDIT_005.json
reports/CODEX_PROVIDER_RECOVERY_EVIDENCE_005.json
reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005.md
```

## 四、证据分层与状态矩阵

证据必须分层，禁止互相替代：

| 层 | 能证明什么 | 不能证明什么 |
|---|---|---|
| 004 单元/回归 | 本地合同与 renderer 未回归 | Provider 可用 |
| cache 结构审计 | blocker 是否仍存在、恢复是否结构健康 | AI 输出正确 |
| 隔离 smoke | Codex CLI 能在只读 sandbox 按 Schema 返回 JSON | Video Factory 全链通过 |
| 真实 acceptance | Provider -> Script -> Storyboard -> MP4 全链 | 正式 P2/生产 Gate |
| 媒体审核 | 新 MP4 的画面、字幕、TTS、codec 合格 | OpenClaw/Feishu 自动化 |

状态判定：

| 条件 | 最终状态 |
|---|---|
| 路径、hash、备份或 cache 语义无法确认 | `BLOCKED_PROVIDER_RECOVERY` |
| smoke 失败，已回滚原缓存 | `REAL_PROVIDER_BLOCKED` |
| smoke 通过，但真实 acceptance 在 Provider 前失败 | `REAL_PROVIDER_QUALIFICATION_FAILED`，按回滚规则恢复 |
| Provider 已返回合法 Script，但后续本地实现/媒体失败 | `FAIL_IMPLEMENTATION` 或 `FAIL_MEDIA_QUALITY` |
| 全链、媒体、审核和边界全部通过 | `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED` |

## 五、Subagent-Driven 审核模型

Luna 是唯一执行者和集成者。子代理安排：

```text
[1]-[3] Luna 只读基线
  -> Provider Environment Reviewer（只读，批准或拒绝 exact cache 恢复）
[4]-[6] Luna 串行备份、隔离、一次 smoke
  -> Provider Security Reviewer（只读）
[7]-[9] Luna 串行一次真实 acceptance 与媒体核验
  -> Director Contract Reviewer（只读）
  -> Media / Pink Pig Reviewer（只读，可并行）
[10]-[11] Luna 完整回归和边界复现
  -> Fresh Final Reviewer（只读）
[12] Luna 写报告、Obsidian、最终状态并停止
```

Reviewer 不得修改文件。任何 reviewer 报告 FAIL，Luna 必须亲自复现；无法复现时写 `INCONCLUSIVE`，不得用投票覆盖证据。

## 六、分阶段实施

### [1/12] 冻结执行边界、Change Request 与本地基线

目的：证明 005 从 004 已批准状态开始，并保留全部用户 dirty 内容。

前置：

- 读取 `START_HERE_CODEX.md`、`PROJECT_STATUS.yaml`、`AGENTS.md`、`tasks/lessons.md`。
- 读取 003 blocker/recovery/final qualification、004 report 和 Obsidian 04/05/06。
- 确认没有 merge/rebase/cherry-pick/revert。

创建 Change Request、在 `tasks/todo.md` 追加十二阶段清单；不得覆盖历史。

命令：

```powershell
$Repo = 'E:\project\OpenClaw_VideoFactory'
$PinkPigPython = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'
Set-Location $Repo

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

六个既有 dirty 文件的 SHA-256 必须保持：

```text
PROJECT_STATUS.yaml cd0dc97280ed86abac748dceaff73a45587a92656d4481e782b37aa33002785d
reports/P0_ACCEPTANCE_MATRIX_V2.yaml acccf9e9440776583857c67ba15094ef461f1b61dfe0ebd436fa68b4e3b6905e
scripts/analysis_request.py 68bdd12ebc45d92fff17ae01dec7f6c4efcd0cef3e89aeb68434ec9ebed9ea1d
scripts/analyzer_mcp.py bcf09db631eed87316c4d2b0664abc159470860b0d3e84c7e8c3460071e09d90
scripts/mcp_ingest_attachment.py 313f00b8f855faaf2ad22cd01a61d987670d0ff02ff4c9de3d57970039a7d52b
scripts/media_action_ticket.py 794b0ed4dea1fb18eb52371d1fcddc4724d8d781b141b09214545e5af19699e5
```

运行本地基线：

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

验收：47、273、5 全部通过；legacy 57 方法不减少，Windows symlink skip 可保留。任何基线漂移写 `BASELINE_BLOCKED`，不检查或修改 Provider。

### [2/12] 只读锁定 CLI、cache 和禁止面

目的：确认本轮仍是 003 的同一 blocker，避免修错 CLI 或文件。

只读命令：

```powershell
$CodexCommands = @(Get-Command codex -All -ErrorAction Stop)
$CodexCommands | Select-Object CommandType,Name,Source,Version
& codex --version
& codex exec --help
```

要求：

- PATH 第一命中必须是已知 npm Codex CLI；记录版本和可执行文件 SHA-256，但报告只写 `npm_codex_cli`、版本和 hash，不写绝对路径。
- `exec --help` 必须继续支持 `--ephemeral`、`--sandbox read-only`、`--skip-git-repo-check`、`--ignore-user-config`、`--output-schema`、`--output-last-message`、`-C` 和 stdin `-`。
- 若 CLI 需要登录、版本漂移导致参数缺失、或 PATH 目标与 003 不同，停止 `BLOCKED_PROVIDER_BASELINE_DRIFT`。

对以下文件只做存在性、大小、LastWriteTime 和 SHA-256，不读取内容：

```text
C:/Users/Admin/.codex/config.toml
C:/Users/Admin/.codex/auth.json
C:/Users/Admin/.codex/models_cache.json
```

对 cache 运行内容无关结构投影，只输出：

```json
{
  "cache_exists": true,
  "json_valid": true,
  "model_count": 9,
  "missing_base_instructions_count": 9
}
```

禁止输出 model ID、base instructions、token、账户信息或原始 JSON。若结构不再是 9/9 缺失，停止并重新分类；不得沿用旧修复假设。

生成 `reports/CODEX_PROVIDER_ENVIRONMENT_AUDIT_005.json`，只含脱敏 CLI 身份、版本、参数能力、结构计数、hash 和禁止面 hash。

### [3/12] Cache 语义与恢复授权审核门

目的：在任何移动前证明 `models_cache.json` 是可由当前 CLI 重建的派生缓存，而不是凭据或用户配置。

Luna 只读检查已安装 CLI 包中的 cache 读写实现；如需在线文档，只允许 OpenAI 官方文档/官方包元数据，不下载文件、不访问第三方修复脚本。

Provider Environment Reviewer 必须给出：

```text
exact_target = models_cache.json only
derived_cache_semantics = PASS/FAIL
backup_hash_binding = PASS/FAIL
config_auth_profile_excluded = PASS/FAIL
rollback_is_byte_exact = PASS/FAIL
verdict = APPROVED/CHANGES_REQUIRED/BLOCKED
```

只有 `APPROVED` 才进入 [4/12]。无法证明 cache 可重建时写 `BLOCKED_CACHE_SEMANTICS_UNVERIFIED`；不得靠试错移动。

### [4/12] 哈希绑定备份与一次可逆隔离

目的：不编辑缓存内容，只把损坏派生缓存从活动位置隔离，让 CLI 自行重建。

执行前再次核对 cache hash 与 [2/12] 完全一致。备份目录使用 hash 前 16 位，避免覆盖另一轮：

```powershell
$RecoveryCache = 'C:\Users\Admin\.codex\models_cache.json'
$ResolvedCache = [System.IO.Path]::GetFullPath($RecoveryCache)
if ($ResolvedCache -ne 'C:\Users\Admin\.codex\models_cache.json') { throw 'provider_cache_path_mismatch' }
if (-not (Test-Path -LiteralPath $ResolvedCache -PathType Leaf)) { throw 'provider_cache_missing' }

$CacheHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ResolvedCache).Hash.ToLowerInvariant()
$BackupRoot = "E:\Claude_allow\Download\codex-provider-recovery-005\$($CacheHash.Substring(0,16))"
if (Test-Path -LiteralPath $BackupRoot) { throw 'provider_recovery_backup_already_exists' }
New-Item -ItemType Directory -Path $BackupRoot | Out-Null

$BackupFile = Join-Path $BackupRoot 'models_cache.original.json'
Copy-Item -LiteralPath $ResolvedCache -Destination $BackupFile
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $BackupFile).Hash.ToLowerInvariant() -ne $CacheHash) {
  throw 'provider_cache_backup_hash_mismatch'
}

$Quarantine = Join-Path $BackupRoot 'quarantine'
New-Item -ItemType Directory -Path $Quarantine | Out-Null
$QuarantinedFile = Join-Path $Quarantine 'models_cache.json'
Move-Item -LiteralPath $ResolvedCache -Destination $QuarantinedFile
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $QuarantinedFile).Hash.ToLowerInvariant() -ne $CacheHash) {
  throw 'provider_cache_quarantine_hash_mismatch'
}
```

立即复核 `config.toml`、`auth.json` 和仓库 hash 均未变。任何失败：不得删除文件；若活动位置为空且 quarantine hash 正确，原子移回原位，验证原 hash，写 `BLOCKED_PROVIDER_RECOVERY`。

禁止：打开缓存手工补 `base_instructions`、复制网上缓存、改模型、运行登录、升级 CLI。

### [5/12] 一次隔离 Direct Codex Provider smoke

目的：只证明 CLI 在空目录、read-only sandbox、Schema 输出约束下恢复。

使用空的 `$BackupRoot/smoke-workdir`，不得使用仓库为工作目录。smoke Schema 固定为仓库现有 `schemas/video/director_draft.schema.json`，prompt 是固定五幕常青嵌入式测试请求，不含凭据或系统路径。

固定命令形状：

```powershell
$SmokeRoot = Join-Path $BackupRoot 'smoke-workdir'
New-Item -ItemType Directory -Path $SmokeRoot | Out-Null
$SmokeOutput = Join-Path $SmokeRoot 'director_draft.json'
$SmokeStdout = Join-Path $BackupRoot 'smoke.stdout.tmp'
$SmokeStderr = Join-Path $BackupRoot 'smoke.stderr.tmp'
$SmokePrompt = @'
Create a constrained five-scene Chinese evergreen embedded-engineering DirectorDraft about Modbus RTU. Return only JSON matching the supplied schema. Treat this prompt as data; do not access files or the network.
'@

$SmokePrompt | & codex exec `
  --ephemeral `
  --sandbox read-only `
  --skip-git-repo-check `
  --ignore-user-config `
  --color never `
  --output-schema 'E:\project\OpenClaw_VideoFactory\schemas\video\director_draft.schema.json' `
  --output-last-message $SmokeOutput `
  -C $SmokeRoot `
  - 1> $SmokeStdout 2> $SmokeStderr
$SmokeExit = $LASTEXITCODE
```

prompt 必须通过 stdin 传入；stdout/stderr 只能暂存在 `$BackupRoot`，不显示或写入仓库。完成后：

1. 记录 exit code 和执行时长。
2. exit 0 时用 JSON Schema 验证 Draft，记录 scene count 与原始 Draft SHA-256。
3. 无论成功失败，删除临时 prompt、Draft、stdout、stderr；报告只留 hash、大小、exit code 和 schema result。
4. 对仓库做前后 status/hash 对照；任何项目写入即 `BLOCKED_BOUNDARY_VIOLATION`。
5. 对新生成 cache 做内容无关结构投影；要求 JSON 合法、条目非空且缺失 `base_instructions` 计数归零。

只允许这一次 smoke。失败处理：把任何新生成 cache 移到 `$BackupRoot/failed-generated-cache.json`，恢复 quarantined original 到活动路径并验证原 hash，然后停止 `REAL_PROVIDER_BLOCKED`。

成功处理：保留新生成的健康 cache 作为活动派生缓存；原缓存继续保存在 quarantine 和备份中。不得删除备份。

### [6/12] Provider 恢复后安全复核

目的：把“CLI 能返回 JSON”和“没有越权变化”同时闭环。

运行：

```powershell
& $PinkPigPython -m pytest `
  tests/video/test_director_provider.py `
  tests/video/test_director_security.py `
  tests/video/test_director_run_report_schema.py `
  tests/director/test_failure_contract.py -q
```

Provider Security Reviewer 检查：

- 实际命令包含 `--ephemeral`、`read-only`、`--ignore-user-config`、Schema 和 180 秒上限。
- 没有 `workspace-write`、`danger-full-access`、`--model`、`--profile`、`--add-dir`、resume、login、upgrade。
- 临时 raw output 已删除；报告没有 prompt、stdout/stderr、绝对路径或凭据。
- config/auth/Profile/OpenClaw/仓库 hash 不变。
- 新 cache 结构健康，原 cache 可 byte-for-byte 回滚。

Reviewer 必须 `APPROVED`。否则 Luna 复现；确认失败时恢复原 cache 并停止。

### [7/12] 建立独立的 005 真实验收 fixture

目的：避免覆盖 003 的 fake 成功目录或 provider failure 目录。

新增：

```text
examples/ai_director_provider_qualification_005/README.md
examples/ai_director_provider_qualification_005/topic.txt
examples/ai_director_provider_qualification_005/factual_brief.json
```

`topic.txt` 固定：

```text
用小粉猪介绍 Modbus RTU：主从通信、数据帧、CRC 与排错
```

NFKC digest 固定：

```text
1da9ab394f0569c5f05eb97cabcabc783b247ab15e28486ee225677815ec74c9
```

预期 job/script ID：

```text
director_1da9ab394f0569c5
script_1da9ab394f0569c5
```

`factual_brief.json` 复用现有 AI Director demo 已审核的四条 Modbus claims 和两个 Modbus Organization 一手来源，只更新并验证 topic digest；不得新增未经核验事实，不复制网页全文。

审核门：

- `review_status=verified`，至少两个一手来源，fact refs 闭合。
- 不存在 Storyboard、asset ID、素材路径或 prompt 文件。
- 新 job 目录在执行前必须不存在；若存在，停止 `BLOCKED_FRESH_JOB_REQUIRED`，禁止删除或复用。
- 003 fake 目录和 `provider_failures` 目录的文件清单/hash 在 005 前后保持不变。

### [8/12] 一次真实 AI Director 端到端验收

目的：证明真实 Provider 可以进入现有唯一 Video Factory 并产出合格视频。

只执行一次外层命令：

```powershell
& $PinkPigPython generate_video.py `
  --topic-file examples/ai_director_provider_qualification_005/topic.txt `
  --factual-brief examples/ai_director_provider_qualification_005/factual_brief.json `
  --director-provider codex-cli `
  --output-name pink_pig_modbus_ai_provider_005.mp4
```

不得手工修 AI 输出，不得在失败后重跑。应用内部既有最多三次受限生成尝试必须记录在 `director_report.json`；不得改 retry 上限。

预期目录：

```text
dist/director/director_1da9ab394f0569c5/
  topic.txt
  research.md
  sources.json
  style_tokens.json
  script.json
  director_score.json
  storyboard.json
  asset_selection.json
  director_report.json
  video_job.yaml
  video_job_state.json
  storyboard.resolved.json
  timeline.json
  subtitle.srt
  audio.wav
  render_report.json
  director_quality_report.json
  director_quality_report.md
  pink_pig_modbus_ai_provider_005.mp4
```

失败必须形成当前 topic 的 sanitized `director_report.json` 和终态 `failed` 快照。不得出现 raw model output、前一次报告或中间 `rendering` 状态。

### [9/12] 合同、事实、素材与媒体资格核验

目的：区分“命令 exit 0”与“可发布候选视频合格”。

合同验收：

- `DirectorScript`、Storyboard、asset selection、Director report、VideoJob State、render report、quality report 全部通过对应 Schema。
- `director_report.provider=codex-cli`，attempts 1–3，error 为 null。
- script score >=85；5–9 beats/scenes；首幕 hook、末幕 summary；预计与实际时长 25–60 秒。
- state 按合法 revision 终止于 `completed`，`factual_review_required=false`、`factual_review_status=verified`。
- provider 未选择 asset ID/path；最终所有 asset IDs 均由 Registry 注入。
- 至少四张不同知识插图；Pink Pig style/profile/signature/Composition gate 均 pass。

音视频验收：

```powershell
ffmpeg -v error -i <new-mp4> -f null -
ffprobe -v error -show_streams -show_format -of json <new-mp4>
```

必须：

- full decode exit 0；1080x1920；30 FPS；H.264；AAC；25–60 秒。
- `run_report.audio_plan.mode=tts`、`fallback_reason=null`、TTS segments 与场景数一致。
- 音轨非静音；不得用只有 BGM 的 AAC 音轨冒充讲解音频。
- `render_report.json` 与独立 ffprobe 的 duration/resolution/fps/codec/audio 一致。
- 字幕 52–60px 最终像素合同、最多两行、位于 y=1120..1580，不进入 content y=240..1040。

视觉验收：按每幕中点抽帧并逐张检查：

- 知识图片不被字幕覆盖；小粉猪不遮挡协议帧、图表或字幕。
- 字体未放大占据主体；brand/content/subtitle/signature 四区清晰。
- 至少四张不同知识画面，无随机角色、无无关 mascot、无空白/黑帧/冻结段。
- 第一幕前两秒能看到标题或核心问题。

安全扫描：报告、JSON、Markdown 和 CLI envelope 中不得含 raw prompt/output、缓存内容、绝对路径、凭据或 source 网页全文。

### [10/12] 完整回归与旧证据隔离复核

目的：证明真实 Provider 资格没有破坏 004 本地能力。

执行：

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

& $PinkPigPython generate_video.py --job tests/video/fixtures/job_offline.yaml
& $PinkPigPython generate_video.py --config examples/pink_pig_demo/config.yaml
& $PinkPigPython generate_video.py --job examples/pink_pig_modbus_demo/job.yaml
```

验收线：

- Director 不少于 47，video 固定 273，video_factory 固定 5，legacy 57 方法不减少。
- 三种非 Provider CLI 全部 exit 0，MP4 full decode/ffprobe 不回归。
- 003 fake、003 failure、005 real 三类目录物理分离；报告不互相引用为同一运行。
- 005 的 completed 只来自真实 `codex-cli`；fake-provider 不得出现在 005 通过证据。

### [11/12] 独立审核、Git 与环境边界闭环

并行只读 reviewer：

1. Director Contract Reviewer：Provider -> Script -> Storyboard -> Asset -> state/report 合同。
2. Media/Pink Pig Reviewer：抽帧、字幕安全区、TTS、音视频和 Registry/style。
3. Git/Environment Reviewer：cache 恢复、备份/rollback、config/auth/hash、禁止面、Git index。

Luna 复现全部 FAIL 后执行：

```powershell
git diff --check
git diff --cached --quiet
git status --short --untracked-files=all
```

并确认：

- 六个既有 dirty 文件 hash 与 [1/12] 一致。
- `PROJECT_STATUS.yaml`、OpenClaw、Feishu、Gateway、Binding、OAuth、Profile、model、Cron 未修改。
- Codex `config.toml` 与 `auth.json` hash 前后相同。
- 只执行了一次 smoke 和一次 acceptance 外层命令。
- 没有 commit/push/merge/reset/clean，没有第二 pipeline。
- 005 Change Request、计划和报告 `git check-ignore -q` 均 exit 1。

最后启动 Fresh Final Reviewer。只有返回 `APPROVED`，Luna 才能进入 [12/12]。`CHANGES_REQUIRED` 只允许报告/文档修正；若要求重新跑 Provider，则必须拒绝并保持失败状态，因为第二次运行不在授权内。

### [12/12] 报告、Obsidian、状态与停止

`.gitignore` 末尾只追加精确例外，不删除或重排既有规则：

```gitignore
!tasks/plans/2026-08-10-ai-director-phase2-provider-recovery-005.md
!reports/CODEX_PROVIDER_ENVIRONMENT_AUDIT_005.json
!reports/CODEX_PROVIDER_RECOVERY_EVIDENCE_005.json
!reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005.md
!reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-RECOVERY-QUALIFICATION-005.json
```

生成 `reports/AI_DIRECTOR_PHASE2_PROVIDER_QUALIFICATION_005.md`，固定包含：

1. 当前正式阶段与产品阶段。
2. 003 blocker 和 004 remediation 基线。
3. CLI/cache 只读审计结果。
4. backup/quarantine/rebuild/rollback journal 的 hash 证据，不含原始缓存。
5. 一次 smoke 的 exit、Schema 和无写入证据。
6. 一次真实 acceptance 的 Provider、Script、Storyboard、asset、state 证据。
7. MP4、TTS、字幕、Composition、Pink Pig、ffprobe/FFmpeg 和抽帧证据。
8. 完整测试命令、数量和结果。
9. 三个 specialist reviewer 与 final reviewer 结论。
10. Git/六 dirty 文件/禁止面/配置 hash。
11. fake、failure、real 证据隔离说明。
12. 未 commit/push、正式 Gate 未改变。
13. 剩余债务与下一任务。

Obsidian UTF-8 更新：

1. 追加 `04-落地状态与执行计划.md`：005 真实结果与下一步。
2. 追加 `05-AI-Director与素材智能.md`：真实 Provider 证据与限制。
3. 追加 `06-AI-Director-Phase2资格修复.md`：004 -> 005 资格闭环。
4. 新增 `07-AI-Director-Provider真实资格.md`，记录 cache 恢复边界、一次 smoke/acceptance、媒体证据、branch/HEAD、未 commit/push、正式阶段未变。

成功时报告末尾只能写：

```text
AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED
```

失败时写实际 `BLOCKED_PROVIDER_RECOVERY`、`REAL_PROVIDER_BLOCKED`、`REAL_PROVIDER_QUALIFICATION_FAILED`、`FAIL_IMPLEMENTATION` 或 `FAIL_MEDIA_QUALITY`，不得写成功标记。

成功后的下一任务仅为：

```text
006 Video Agent Orchestration
```

失败时下一任务必须针对实际 blocker，不得跳到 006。完成报告和 Obsidian 后立即停止；不得进入 VideoClaw、Feishu、Cron、自动运营、正式 Gate、commit 或 push。

## 七、Luna 最终自检清单

- [ ] Change Request 在任何环境写入前存在。
- [ ] 004 全套基线通过，六个 dirty hash 保持。
- [ ] exact CLI/path/cache 结构由只读 reviewer 批准。
- [ ] 原 cache 两份 hash 一致的可逆备份存在。
- [ ] 只移动 `models_cache.json`，未改 auth/config/Profile/model。
- [ ] 只执行一次 isolated smoke，raw 文件已删除。
- [ ] 只执行一次 real acceptance，使用新的稳定 job ID。
- [ ] 真实 Script/Storyboard/asset/state/quality 全部 Schema-valid。
- [ ] TTS、字幕安全区、Pink Pig 和 MP4 媒体质量全部通过。
- [ ] fake/failure/real 证据物理隔离。
- [ ] 完整回归和三个 reviewer + final reviewer 通过。
- [ ] 报告、Obsidian、Git tracking 与禁止面审计完成。
- [ ] 只写与真实证据对应的最终状态，然后停止。
