# AI Director Phase 2 — Detached Provider Qualification 005R

## 当前结论

本任务没有完成真实 Provider 资格。当前证据状态为：

```text
BLOCKED_DETACHED_WORKER_DIED
```

产品代码仍处于 `AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED`；正式 `PROJECT_STATUS.yaml` 未修改，P0/P1/P2 Gate 未改变。

## 已完成的本地工作

- 新增并加固 Detached Worker、状态 Schema、Change Request、005R fixture 和 Pester 合同测试。
- Worker 现在使用隐藏 PowerShell、固定仓库/Python、Push-Location/Pop-Location cwd 隔离、Desktop quiescence 等待、稳定 hash 门、reparse/containment 拒绝、hash-bound backup/quarantine/rollback、单次 smoke/acceptance 标记和 active-run lock。
- Worker 状态链包含 `verification_passed → complete_pending_review`；默认 Verify 只读，只有独立 final review 写入 `FINAL_REVIEW_APPROVED.txt` 后 `-Finalize` 才能进入 `completed`。
- Worker 还提供只监测进程存活的 watchdog：非终态退出会写入结构化 `BLOCKED_DETACHED_WORKER_DIED`；watchdog 不终止 Desktop、不访问 cache、不执行 Provider。
- Worker 启动采用 `WATCHDOG_READY` 握手；watchdog 未成功启动时 Worker 在 30 秒内 fail-closed，不进入 Desktop/cache 阶段。
- Verify 会绑定 state/run_id/task_id，重新检查 state Schema、smoke 健康数据、实际 backup/quarantine hash、active cache hash、config/auth、六个 dirty 文件和 Git index。
- 报告绑定 `run_id`，并递归检查 raw stdout/stderr/draft 临时文件、配置/auth hash 变化和旧报告混用。
- post-acceptance 机器门已实现：Schema、30 FPS、25–60 秒、H.264/AAC、音量、render report 对照、字幕安全区、TTS segment、hook/summary、score、factual 状态、Registry 素材多样性和 Pink Pig/Composition 字段检查。

## 实际测试

| 命令 | 结果 |
|---|---:|
| `Invoke-Pester tests/Test-ProviderQualification005R.ps1 -PassThru` | 12 passed |
| PowerShell parser（入口和模块） | 0 errors |
| 禁止命令静态扫描 | clean |
| `pytest tests/director -q` | 47 passed |
| `pytest tests/video -q` | 273 passed |
| `pytest video_factory/tests -q` | 5 passed |
| legacy candidate/final-audit group | 56 passed, 1 skipped, 13 subtests |

## 独立审查

- Worker contract reviewers independently confirmed the earlier implementation gaps and then verified the subsequent hardening items (CLI re-lock, hash/boundary evidence, complete verification, watchdog and handshake). The last identified handshake issue was fixed and rechecked locally with parse/Pester/diff checks.
- A new real-provider final review was not performed because the single authorized Worker had already died; no second Worker was started.

## Worker 与 Provider 证据

唯一启动的 Worker：

```text
session_20260810T145823Z_60876
```

它在 Desktop 关闭交接前被终止；随后仅对该已停止 run 写入了 revision 3 的结构化 `blocked` 快照，`smoke_attempted=false`、`acceptance_attempted=false`。因此本任务没有执行：

- cache backup/quarantine 或恢复；
- `codex exec` smoke；
- 真实 AI Director acceptance；
- 新 MP4、ffprobe、字幕、TTS 或抽帧证据；
- `READY_TO_REOPEN.txt`、`FINAL_REVIEW_APPROVED.txt` 或 `completed` 状态。

005R 计划明确规定 Worker 死亡后不得在同一任务启动第二个 Worker。基于该不可重复执行合同，本报告不把离线测试或历史 fake MP4 升级为真实 Provider 证据。

对应的阻塞审计 JSON 为 `reports/CODEX_DESKTOP_QUIESCENCE_AUDIT_005R.json` 和 `reports/CODEX_PROVIDER_DETACHED_RUN_005R.json`；两者明确记录未发生 cache 操作、smoke、acceptance 或媒体产物。

## 边界确认

- 未执行 `codex exec`，未移动或修改 `models_cache.json`。
- 未修改 `config.toml`、`auth.json`、OAuth、Profile、模型或 Codex Desktop。
- 未修改 OpenClaw、Feishu、Gateway、Binding、Cron 或 `PROJECT_STATUS.yaml`。
- 未执行 commit、push、merge、reset 或 clean。
- 六个既有 dirty 文件保持原有边界；index 未用于本任务提交。

Obsidian 已更新：`04-落地状态与执行计划.md`、`07-AI-Director-Provider真实资格.md`，并新增 `08-AI-Director-Provider脱离桌面验收.md`。

## 剩余债务与下一步

- 需要 Jovi 另行明确授权后，才能开启新的资格任务/新的 detached Worker；不能在本 005R 中重启已死亡 Worker。
- 真实 Provider、真实 MP4、媒体质量和独立 final review 尚未完成。
- Provider cache recovery 仍必须保持 byte-exact、可回滚并与 Desktop 写入进程隔离。
- 在真实 Provider qualification 通过前，不进入 006 Video Agent Orchestration、Feishu、Cron 或正式 Gate。

BLOCKED_DETACHED_WORKER_DIED
