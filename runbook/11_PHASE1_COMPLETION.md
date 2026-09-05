# 11 — Phase 1 本地视频工厂正式收口 Runbook

Updated: 2026-09-05

## 目的

把已经存在的 Topic、Reference、SQLite Lifecycle、Director、Remotion/FFmpeg、Review Package、Acceptance/Gate 和近期参考重构成果统一为一次正式 Phase 1 验收。

当前状态是 `in_progress`，不是 `not_started`，也不是 `passed`。

本 Runbook 不授权飞书、OpenClaw Daily Runtime、Cron、自动发布或模型下载。

---

## 1. 基线确认

开始前：

```powershell
Set-Location E:\project\OpenClaw_VideoFactory
git fetch
git status --short --untracked-files=all
git rev-parse HEAD
git rev-parse origin/codex/phase1-reference-video-analysis-001
git diff --check
```

要求：

- 固定当前分支 `codex/phase1-reference-video-analysis-001`；
- 不 reset/clean/自动 stash/rebase/force push；
- 若远端前进，先读新提交，禁止回退；
- Runtime/参考原件/SQLite/私人审阅文件不进入 Git。

先读：

- `PROJECT_STATUS.yaml`；
- `docs/README.md`；
- `docs/CURRENT_ARCHITECTURE.md`；
- `docs/PRODUCT_PHASES.md`；
- `handoff/codex/PROJECT_HANDOFF_20260905.md`。

---

## 2. 不要重复实现已经存在的模块

不要重写：

- `src/factory/db.py`；
- `src/factory/phase1_cli.py`；
- `src/factory/phase1_local.py`；
- `src/factory/reference_video.py`；
- `src/factory/director/`；
- `video_factory/pipeline/`；
- `generate_video.py`；
- `src/factory/phase1_acceptance.py`；
- `src/factory/phase1_gate.py`。

只修当前证据暴露出来的兼容问题。

---

## 3. 先建立当前统一测试基线

历史测试数字来自不同阶段，不能混成一个假的“总通过数”。本轮先记录明确的 bounded suites：

```powershell
$py = 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe'

& $py -m pytest tests/phase1_acceptance -q
& $py -m pytest tests/phase1_local -q
& $py -m pytest tests/reference -q
& $py -m pytest tests/director -q
& $py -m pytest tests/video -q
& $py -m pytest video_factory/tests -q
```

再运行与当前 reference/remotion/jianying Change Request 相关的 focused tests。

根目录 `pytest` 如果仍被 vendor research dependency 或历史 Feishu/P0 环境套件阻塞，必须：

- 记录哪些 suite 非 Phase 1；
- 不把这些失败隐瞒；
- 也不允许它们阻止 bounded Phase 1 Gate；
- Gate manifest 明确列出真正参与资格判断的 suite。

---

## 4. 固定主题集合

### Modbus RTU

已有 baseline，不为了“看起来有新工作”重写。只需重新对齐当前 Schema、Review Package、Human Review 和 Prereview。

### Flash / Watchdog

当前已有：

- `examples/phase1_local_flash_watchdog/brief.json`；
- deterministic technical illustrations；
- mascot-free 修正版；
- 本地 MP4；
- 多轮 timing/Jianying 证据。

本轮要做的是选出**唯一最终候选**，不要把所有历史 v1/v2/v4 都送进 Gate。

### FreeRTOS

已有：

- `examples/phase1_local_freertos/brief.json`。

仍需完成：

- technical deterministic visuals；
- script/storyboard/asset selection；
- local narration；
- subtitle/timing；
- final MP4；
- quality report；
- review package；
- SQLite `PENDING_REVIEW`；
- Jovi Human Review；
- Prereview。

这应是当前最明确的代码/执行缺口。

---

## 5. Render Profile 对齐

不要假设所有 Job 都必须同一个分辨率。

Gate/Review 必须从当前 Job 的 profile 判断：

- `9:16` → 1080×1920；
- `16:9` → 1920×1080；
- 30 FPS；
- H.264/AAC；
- complete decode；
- profile-specific safe area / subtitle rule。

如果现有 acceptance Schema 仍硬编码单一 1080×1920，需要先在最小范围内修成 profile-aware contract，再重新跑相关测试。不要为了兼容横屏 reference/Jianying 实验而破坏竖屏 Douyin profile。

---

## 6. Lifecycle Evidence

必须用机器可解析 JSON 形成四类 fresh evidence：

1. `cancel`；
2. `retry`（先真实失败，再 retry，证明从正确 last completed state 恢复）；
3. `restart_recovery`（进程终止/新进程继续读 SQLite 和 Artifact 状态）；
4. `encoder_fallback`（NVENC → CPU 或明确的 CPU-only fallback contract）。

每份记录：

- schema/version；
- job_id；
- started_at/completed_at；
- actual assertions；
- source artifact hashes；
- status；
- 无绝对私有媒体路径。

不要用 Markdown 自述替代机器 evidence。

---

## 7. Reference Candidate 收口

### 已有成果

当前分支已经有：

- safe reference analysis；
- RC high-pass 9:16 reconstruction；
- corrected geometry；
- local narration；
- timing manifest；
- measured speech cues；
- speech-cue-bound knowledge-card animation；
- post-render checks；
- Jianying visible/manual-review branch。

### 当前必须做

1. 确定最新唯一候选（不要混用 v5/v6/v8 报告）；
2. 将它映射到当前 standard Review Package / Human Review contract；
3. Jovi 实际看画面、听音频并判断 originality；
4. 形成 `phase1_human_review`；
5. 生成 Prereview；
6. 若它属于公开 reference research 而最终 Gate manifest 明确要求 `local_reference` fixture，则另用一条 Jovi 授权本地 MP4 + rights 跑一遍标准路径；
7. synthetic reference 只能做测试，不能替代人工原创性证据。

---

## 8. Jianying

Jianying 草稿链已经有实现证据，但 Phase 1 Gate 的强制产品结果仍是：

`local MP4 + quality report + review package`

所以：

- 草稿可作为额外人工 review 方式；
- Jovi 可以在剪映中试听、检查、导出；
- 自动导出保持关闭；
- 草稿失败只阻塞 editable-delivery branch，不应推翻已经合格的本地 MP4；
- 不把剪映变成唯一 renderer。

---

## 9. Human Review

每个进入最终 Gate 的候选必须有结构化人工审阅。

最少检查：

- video playable；
- audio clear；
- subtitles readable / timing acceptable；
- technical content acceptable；
- visual composition acceptable；
- originality acceptable；
- Pink Pig consistency（只有 mascot-enabled brief 才要求；mascot-off 不应被此字段错误阻塞）。

人工审核必须绑定最终 MP4 SHA-256。

Jovi 未看过/未听过的候选不得写 `approved`。

---

## 10. 单 Job Prereview

```powershell
& $py scripts/phase1_acceptance.py `
  --database state/phase1_local/phase1_jobs.sqlite3 `
  --job-id <control_job_id> `
  --review <human_review.json> `
  --output reports/phase1/prereview/<name>.json
```

退出码 0 且 `status=ready` 才能进入 Acceptance Manifest。

如果现有 Prereview 工具与新 profile/mascot-off contract 不兼容，先写最小失败测试再修。

---

## 11. Boundary Audit

必须确认：

- `no_feishu = true`；
- `no_openclaw_runtime = true`；
- `no_cron = true`；
- `no_automatic_publish = true`；
- private runtime stays ignored；
- no credentials / raw reference media in Git；
- no second all-in-one video backend；
- no unapproved model/node download。

---

## 12. Acceptance Manifest

Manifest 只引用**最终选择的证据**，不把整个 `reports/` 历史目录全塞进去。

至少包含：

- Modbus Prereview；
- Flash/Watchdog Prereview；
- FreeRTOS Prereview；
- Reference Prereview；
- cancel evidence；
- retry evidence；
- restart recovery evidence；
- encoder fallback evidence；
- boundary audit；
- bounded regression summary；
- human-review hashes。

所有文件都带 SHA-256。

---

## 13. Independent Read-only Audit

正式 Gate 前再开一个独立 Agent，只读审核：

- current branch / HEAD；
- manifest file hashes；
- selected candidate uniqueness；
- human review binding；
- no stale v5/v6/v8 mixing；
- no Phase 2 side effects；
- no false test aggregation；
- no absolute/private path leakage。

发现问题先修证据，再重新生成 manifest；不要直接改 Gate 让它通过。

---

## 14. Formal Gate

确认所有人工审核和独立 review 完成后，正式 Gate **只运行一次**：

```powershell
& $py scripts/phase1_gate.py `
  --manifest reports/phase1/phase1_acceptance_manifest.json `
  --output-dir reports/gates
```

成功：

- exit 0；
- `reports/gates/PHASE1_READY.json`；
- 所有来源 SHA 匹配。

失败：

- 保留 `PHASE1_FAILED.json`；
- 停止；
- 不伪造/覆盖失败证据；
- 创建新的 remediation task。

---

## 15. Phase Promotion

只有 Gate 通过后，才单独更新：

```yaml
product_phases:
  PHASE_1_LOCAL_VIDEO_FACTORY:
    status: passed
```

然后停止当前任务。

**不要在同一任务直接开始飞书 Phase 2。**
