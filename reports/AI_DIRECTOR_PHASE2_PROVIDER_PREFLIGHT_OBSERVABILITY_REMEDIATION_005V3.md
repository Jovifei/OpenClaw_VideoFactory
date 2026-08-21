# AI Director Phase 2 Preflight Observability Remediation 005V3

## 结论

本任务完成了本地 Preflight 错误可观测性与历史证据绑定修复，但最终边界审核不能宣称无条件通过：两个受保护 dirty 文件当前 SHA 与任务冻结基线不一致，且属于本任务开始前的用户变更，本任务没有覆盖、恢复或修改它们。

最终状态：

```text
BASELINE_BLOCKED
```

本报告不是 Provider、Worker、Codex smoke、真实 acceptance、MP4 或 Phase 2 Ready 证据。

## 当前阶段

产品能力线仍为 Phase 1.5 Renderer/Pink Pig READY、Phase 2 Local AI Director 已修复、Worker state/marker 合同已修复。005T 保持不可变终态 `BLOCKED_DETACHED_WORKER_DIED`；005W 只证明 Chrome/legacy 主机基线；005V2 唯一只读 Preflight 为 `PREFLIGHT_BLOCKED`，`unexpected_error`，计数器 1/1，Worker/smoke/acceptance/MP4 均为 0。

正式项目阶段未由本任务推进。`PROJECT_STATUS.yaml` 本任务未修改；当前工作树中的阶段文件存在既有用户 dirty 变更，不能作为本任务的阶段晋级证据。

## 本轮修复

- 新增 `provider_qualification_preflight_error.schema.json`，固定 `code/message/context`，gate/substep/reason 为枚举，禁止异常原文、路径、token、prompt、cache 内容、模型 ID 和完整命令行。
- 新增 `New-PQPreflightFailure`、`Get-PQStablePreflightReason`、`Get-PQPreflightFailureContext` 与实际 CLI 外层 envelope builder。
- Preflight gate 使用稳定授权、source freeze、freshness、Git、CLI、media、005T、cache、environment、Desktop 上下文。
- 新增诊断 profile `005V3`：只允许一次只读 Preflight；显式允许 metadata/hash/process probes，同时显式禁止 cache/config-auth mutation、Desktop control、Provider/OAuth/profile/model 变更、Worker、smoke、acceptance、commit/push。
- 005V2 CR 与报告的终态、命令次数、零 Worker/smoke/acceptance/MP4 事实现在以 hash-bound immutable evidence 纳入 005V3 source freeze。
- 新增 TestDrive 负向测试：全部非 Preflight mode 拒绝、授权字段缺失/false 拒绝、外层 CLI envelope、005V2 resolver 隔离、005V2 hash drift 和静态外部命令禁用。

## Source Freeze

当前只读 LoadOnly source freeze：

```text
a5970bccfde34a907f485ed76154048b6c227093783ac42600d298c20d2c266f
```

关键当前 hash：

```text
scripts/provider_qualification.ps1
76b871af8c0b8900caa4d5601329b6e7dff0a55d672f4c5cbe66fdb3179b9534
scripts/lib/ProviderQualification.psm1
793ba589c8fd846a17077bd3f65fdc3dc7c7ffa125ced7cf19044ec28cb52261
schemas/ops/provider_qualification_preflight_error.schema.json
e75e5e67819005f28de25ccb443aac049ded9fd4ac2d798f060e62561ff0c37d
tests/Test-ProviderQualification005V3.ps1
6a91d6e98388c03867b310ae871b017bad5616c3290af057d988002c97417a3d
```

005T immutable evidence digest remains `5e86bba919fa932da052bad055697d28a7d3e283961d770fec14f5dd6eea205f`; 005V2 immutable evidence digest is recomputed from the two repository bridge files and bound into the source freeze.

## 验证证据

- Pester 005R/S/T/U/U1/V/V3: **90 passed, 0 failed, 0 skipped**。
- Targeted 005V3: **11 passed**。
- Python: Director **47 passed**；Video **273 passed**；Video Factory **5 passed**。
- Legacy 非 Chrome 子集：**55 passed, 1 skipped, 1 deselected, 13 subtests**。完整 legacy 当前重跑唯一失败为既有 headless Chrome contact-sheet host error `mascot_contact_sheet_failed:2147483651:local_path_redacted`；005W 已以独立外部 session 证明完整组 **56 passed / 1 skipped / 13 subtests**，且本轮未修改 legacy 产品实现。
- PowerShell parser：entry/module 0 errors。
- JSON Schema meta-validation：error schema 通过，实际 envelope 通过。
- 禁止面扫描：无可执行 `codex exec`、`Stop-Process`、`taskkill`、`danger-full-access`、`workspace-write`、`--model`、`--profile`、login、upgrade、OpenClaw/Feishu/Gateway/Binding/Cron 调用。
- Source freeze 与诊断 CR 的 digest 已重新计算并一致。

独立审查：

- Security/Leakage Reviewer：`APPROVED_FOR_005V3_LOCAL_GATE`。
- Contract Reviewer：`CHANGES_REQUIRED`，唯一当前阻断为诊断 CR 的 protected boundary 仍绑定冻结的 `PROJECT_STATUS.yaml` / `scripts/analysis_request.py` SHA，而工作树存在既有 drift；该 reviewer 未要求覆盖用户文件，故本报告保持 `BASELINE_BLOCKED`。

## 保护边界

分支仍为 `codex/ai-director-video-factory-phase2-001`，HEAD 仍为 `76180a59ea662bdf168d88baaeb777d3e8eb59ef`，index 为空，`git diff --check` 通过。四个 protected dirty 文件与冻结 SHA 一致：`reports/P0_ACCEPTANCE_MATRIX_V2.yaml`、`scripts/analyzer_mcp.py`、`scripts/mcp_ingest_attachment.py`、`scripts/media_action_ticket.py`。

以下两个文件当前不匹配任务给定基线，但本任务没有修改：

```text
PROJECT_STATUS.yaml
expected cd0dc97280ed86abac748dceaff73a45587a92656d4481e782b37aa33002785d
current  76fb81f8d9e32aca3fa73fe547deff8961ea130bd6e8d3e043179b03d5900acd

scripts/analysis_request.py
expected 68bdd12ebc45d92fff17ae01dec7c6f4efcd0cef3e89aeb68434ec9ebed9ea1d
current  68bdd12ebc45d92fff17ae01dec7f6c4efcd0cef3e89aeb68434ec9ebed9ea1d
```

该漂移阻止本轮写 `AI_DIRECTOR_PHASE2_PREFLIGHT_OBSERVABILITY_REMEDIATED` 作为无条件边界通过标记；不得用本任务覆盖用户变更来消除它。

## 未执行与禁止面

本轮没有执行 Preflight、Start、Supervisor、Worker、Rehearse、Status、Verify、`codex exec`、smoke、acceptance、cache quarantine/rebuild、MP4、Desktop 操作或真实 Provider。没有读取 cache/config/auth 内容，没有修改 `PROJECT_STATUS.yaml`、005T 外部 run/ledger/report、OpenClaw、Feishu、Gateway、Binding、Cron；没有 commit、push、stage、reset 或 clean。

诊断 CR `AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-DIAGNOSTICS-005V3` 保持 `prepared_pending_diagnostic_review`，诊断 JSON 标记 `NOT_PERFORMED`，因此没有消耗新的 Preflight 计数器。

## 文档

新增 Obsidian 页面：

`E:/AI_Tools/Obsidian/Data/notes-personal/codex_memory/03-项目记忆/OpenClaw_VideoFactory/17-AI-Director-Provider预检可观测性修复005V3.md`

既有 Obsidian 页面未被重写；部分既有页面因当前文件锁/权限未能追加，本报告不伪称已更新。

## 下一步

先处理受保护 dirty 文件的外部边界确认，并由全新只读 Final Reviewer 确认当前代码合同。只有 Jovi 另行授权，才可执行一次 005V3 只读诊断 Preflight；其结果只能是具体 `PREFLIGHT_DIAGNOSTIC_BLOCKED:<gate>:<reason>` 或 `READY_FOR_005V4_REAL_PROVIDER_QUALIFICATION_PLANNING`。在此之前不得执行 Worker、Provider、smoke、acceptance、MP4、006、Feishu 或 Cron。

`BASELINE_BLOCKED`

## 005V3 诊断执行附录（2026-08-15）

Jovi 已明确授权执行一次、且仅一次 005V3 只读诊断 Preflight。实际命令为：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/provider_qualification.ps1 -QualificationProfile 005V3 -Mode Preflight
```

结果：进程退出码 `1`，脱敏错误合同为：

```json
{
  "code": "provider_qualification_preflight_failed",
  "message": "Provider preflight stopped.",
  "context": {
    "stage": "preflight",
    "gate": "cache_snapshot",
    "substep": "json_parse",
    "reason": "cache_unhealthy",
    "exit_code": null
  }
}
```

当前终态为 `PREFLIGHT_DIAGNOSTIC_BLOCKED:cache_snapshot:cache_unhealthy`。诊断计数为：Preflight `1/1`，Worker `false`，Provider `false`，smoke `0`，acceptance `0`，MP4 `0`。未执行 Worker、Provider、cache mutation、Desktop 操作、smoke、acceptance 或 MP4；未重试该命令。

该次结果已同步到 `reports/CODEX_PROVIDER_PREFLIGHT_DIAGNOSTIC_005V3.json` 与对应 Change Request 的 `result` 字段。005V3 不构成真实 Provider 通过、Phase 2 Ready 或 006 授权。
