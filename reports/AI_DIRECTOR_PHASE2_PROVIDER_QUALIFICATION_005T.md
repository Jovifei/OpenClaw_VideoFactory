# AI Director Phase 2 — 005T Provider Qualification

## 1. 结论

本次 005T 是独立于 005R/005S 的新资格运行。Preflight 通过，但唯一 detached
Supervisor/Worker 在 `WORKER_READY` 之前退出，未进入 Desktop quiescence、cache
隔离、smoke 或真实 AI Director acceptance。

最终状态：`BLOCKED_DETACHED_WORKER_DIED`

这不是 `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED`，也不是正式 P2 Gate。
`PROJECT_STATUS.yaml` 保持 P0 `not_started`、P1/P2 blocked。

## 2. 本地合同与独立审核

- PowerShell parser：0 errors。
- Pester 005R/005S/005T：39 passed，0 failed。
- Director：47 passed。
- Video：273 passed。
- Video Factory：5 passed。
- Legacy candidate：56 passed，1 skipped，13 subtests。
- Contract reviewer：APPROVED（当前冻结 hash）。
- Lifecycle reviewer：APPROVED（当前冻结 hash）。
- Security reviewer：APPROVED（当前冻结 hash）。
- 禁止命令静态扫描：clean。

冻结源码 hash：

| 文件 | SHA-256 |
|---|---|
| `scripts/provider_qualification.ps1` | `deb1ad5f29ae140786f945f515e65479186a76aae5dc94903ff31c11d51e40aa` |
| `scripts/lib/ProviderQualification.psm1` | `7ab8835cd22cbb76560bd03b5cfc7721ef0831162d4627a0c115b9647b791d6b` |
| `schemas/ops/provider_qualification_run.schema.json` | `8cc893aa9f534c1016a2993994e1aa6e803e8182a00b60facfea89aceba5abbe` |
| `tests/Test-ProviderQualification005T.ps1` | `5f910d7ce4ebd23368ee66e38c56bd8bc2237b50e1c685a7897c8e4e123e4700` |

## 3. Preflight 证据

Preflight exit code 为 0，确认：

- npm Codex CLI 0.146.0 与 required flags 可用；
- branch `codex/ai-director-video-factory-phase2-001`、HEAD `76180a59ea662bdf168d88baaeb777d3e8eb59ef`、index empty；
- 六个受保护 dirty 文件 hash 未变；
- media tool hash 与冻结合同一致；
- 005T external root 与 stable job 目录在启动前为空/不存在；
- cache 仅被读取并记录 hash/size/合法 JSON 计数，未移动或修改；
- config/auth 仅记录 hash，未写入。

Prelaunch review hash：`b973a5e2660c11e43bdd1fe6215a141f740b762396c0ee599e73581f01ea04cf`。
Source freeze：`aac8bdb6eb173e211bded9c9caaa4e76358479f4dfd35e2bf0b1eccb134e8c37`。

首次 Start 在创建 Worker 前因手工 source-freeze 路径规范化不一致而被
`PRELAUNCH_REVIEW_FAILED` 拒绝；未创建 Worker、未修改 cache。修正为脚本实际
Profile 路径后重新绑定 review/audit，随后唯一有效 Start 才消耗 Worker 额度。

## 4. Detached run 证据

Run：`session_20260811T175916Z_43092`

- state：`blocked`，revision 6；
- surfaced terminal status：`BLOCKED_DETACHED_WORKER_DIED`；
- nested sanitized state error：`WORKER_CONTRACT_FAILED` / `provider_qualification_state_schema_invalid`；
- Desktop absent samples：0；cache stable samples：0；
- cache mutation：false；backup/quarantine：未执行；
- smoke：not_started，attempt_count 0；
- acceptance：not_started，attempt_count 0；
- MP4、ffprobe、音频、字幕和抽帧：未生成/未执行；
- `Status` 已创建绑定的 readonly terminal ledger，避免 active lock 残留。

外部证据文件保持在 run root，报告只引用相对 artifact：

- `session_20260811T175916Z_43092/run_manifest.json`
- `session_20260811T175916Z_43092/source_freeze.json`
- `session_20260811T175916Z_43092/state.json`
- `session_20260811T175916Z_43092/BLOCKED.txt`
- `.qualification.terminal.session_20260811T175916Z_43092.lock`

## 5. 边界确认

- 未执行 `codex exec` smoke。
- 未执行真实 AI Director acceptance。
- 未移动、重写或删除 `models_cache.json`；未保留原始 cache backup，因为隔离未开始。
- 未修改 config.toml、auth.json、OAuth、Profile、model selection 或 Codex 配置。
- 未修改 OpenClaw、Feishu、Gateway、Binding、Cron 或 `PROJECT_STATUS.yaml`。
- 未 commit、push、merge、reset 或 clean。
- 六个既有 dirty 文件保留且 hash 未变；index 仍为空。

## 6. 真实状态与下一步

本次不能升级为真实 Provider 资格，也不能进入 006 Video Agent Orchestration。
005T 只消耗了本次的一次 Worker 启动授权；不得在同一 run 中重启 Worker、smoke
或 acceptance。下一步必须另行授权一个全新、独立 namespace 的 Provider
qualification retry，并先调查当前 Worker 在 ready 前退出的原因；不得复用本次
run 或 005R/005S 证据。

剩余债务：

- 真实 Provider 尚未通过；
- 无真实 MP4、media gate 或独立 final reviewer 证据；
- 正式 P0/P1/P2 Gate 未改变；
- Video Agent Orchestration、OpenClaw、Feishu、Cron 和自动运营均未开始。

BLOCKED_DETACHED_WORKER_DIED
