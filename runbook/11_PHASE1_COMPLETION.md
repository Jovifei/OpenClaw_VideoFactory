# 11 — Phase 1 本地视频工厂收口 Runbook

## 目的

把已经存在的主题模式、参考视频模式、SQLite 生命周期、视频流水线和审阅包收敛成一次正式 Phase 1 验收。不要重写已有模块，也不要接入飞书。

## 1. 基线确认

- 分支、HEAD、工作树和远端一致；
- `PROJECT_STATUS.yaml` 仍为 Phase 1 `not_started`；
- `generate_video.py` 是唯一视频渲染入口；
- `scripts/factory.py phase1` 是本地 Job 控制入口；
- 不运行 Provider 恢复、OpenClaw、飞书或 Cron。

## 2. 固定输入集合

### 主题 Fixture

1. Modbus RTU；
2. Flash/看门狗；
3. FreeRTOS。

每项均需要验证 factual brief、原创脚本、5–9 场景 Storyboard、Registry 资产、TTS、字幕、MP4、质量报告和审阅包。

### 参考视频 Fixture

由 Jovi 提供一条拥有权利的本地 MP4，并同时提供 `reference_rights.json`。原文件只读，必须生成抽象报告和原创成片，禁止复用原音、水印或原镜头。

## 3. Job 执行

```powershell
python scripts/factory.py phase1 init-db
python scripts/factory.py phase1 create-topic --brief <brief.json>
python scripts/factory.py phase1 create-reference --video <video.mp4> --brief <brief.json> --rights <rights.json>
python scripts/factory.py phase1 run --job-id <control_job_id>
python scripts/factory.py phase1 status --job-id <control_job_id>
```

运行成功后 Job 必须为 `PENDING_REVIEW`。

## 4. Jovi 人工审阅

每个成片都必须创建独立的 `phase1_human_review` JSON：

```json
{
  "schema_version": "1.0",
  "control_job_id": "job-...",
  "render_job_id": "phase1_...",
  "reviewer": "Jovi",
  "decision": "approved",
  "reviewed_at": "2026-08-22T00:00:00Z",
  "reviewed_artifact_sha256": "...",
  "checklist": {
    "video_playable": true,
    "audio_clear": true,
    "subtitles_readable": true,
    "pink_pig_consistent": true,
    "technical_content_acceptable": true,
    "originality_acceptable": true
  },
  "notes": "..."
}
```

不要把未看过的视频标为批准。

## 5. 单 Job Prereview

```powershell
python scripts/phase1_acceptance.py `
  --database state/phase1_local/phase1_jobs.sqlite3 `
  --job-id <control_job_id> `
  --review <human_review.json> `
  --output reports/phase1/prereview/<name>.json
```

退出码 0 且 `status=ready` 才可进入总 Gate 清单。

## 6. 生命周期证据

分别形成机器可验证 JSON：

- cancel；
- retry；
- restart_recovery；
- encoder_fallback。

每份证据必须来自本轮实际执行，记录 Job ID、断言与时间。不得用文字报告代替。

## 7. Phase 1 Boundary Audit

确认：

- 未联系飞书；
- 未使用 OpenClaw Runtime；
- 未注册/运行 Cron；
- 未自动发布；
- Runtime 媒体、数据库、参考视频和审阅数据保持在忽略目录。

## 8. 正式 Gate

填写 `phase1_acceptance_manifest.schema.json` 对应的 Manifest 后运行：

```powershell
python scripts/phase1_gate.py `
  --manifest reports/phase1/phase1_acceptance_manifest.json `
  --output-dir reports/gates
```

通过条件：

- 退出码 0；
- `reports/gates/PHASE1_READY.json` 存在；
- 所有来源报告 SHA-256 匹配；
- 三个主题 Fixture、参考视频、生命周期和边界审计均通过。

Gate 只运行一次；失败后保留 `PHASE1_FAILED.json` 并停止。

## 9. 状态更新

只有 Gate 通过且获得单独授权时，才原子更新 `PROJECT_STATUS.yaml`。不得在同一任务中进入 Phase 2。
