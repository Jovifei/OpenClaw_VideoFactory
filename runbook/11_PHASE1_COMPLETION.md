# 11 — Phase 1 本地视频工厂收口 Runbook

## 目的

把已经存在的主题模式、参考视频模式、SQLite 生命周期、视频流水线和审阅包收敛成一次正式 Phase 1 验收。010 当前目标是 `topic_only_v1`，而非删除旧参考视频能力；不要重写已有模块，也不要接入飞书。

## 1. 基线确认

- 分支、HEAD、工作树和远端一致；
- `PROJECT_STATUS.yaml` 仍为 Phase 1 `in_progress`，且没有任何 passed 结论；
- 旧 fixture 仍通过 `generate_video.py` 渲染；010 local-subject 通过 `src/factory/phase1_cli.py` 的 `factory.py phase1` 控制入口生成经验证的 subject-media / review package；
- 不运行 Provider 恢复、OpenClaw、飞书或 Cron。

## 2. 固定输入集合

### 010 topic-only Fixture

1. Flash/看门狗；
2. FreeRTOS；
3. I2C；
4. 一条与以上 control job 不重复的 live topic。

每项均需要验证 factual brief、原创脚本、5–9 场景 Storyboard、Registry 资产（小粉飞猪仅 opt-in）、TTS、字幕、16:9 audible preview、质量报告和审阅包。Jianying 草稿仅等待 Jovi 最终人工审阅，禁止自动导出。

### 保留的参考视频 Fixture（legacy_topic_reference_v1）

由 Jovi 提供一条拥有权利的本地 MP4，并同时提供 `reference_rights.json`。原文件只读，必须生成抽象报告和原创成片，禁止复用原音、水印或原镜头。它保留为 legacy scope 能力；不再是 010 topic-only scope 的前置条件。任何在 topic-only manifest 中实际提供的 reference job 仍必须完整通过。

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

每个 audible preview 都必须创建独立的 `phase1_human_review` JSON：

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

不要把未看过的视频或未听过的 audible preview 标为批准；010 的最终 Jianying 审阅、导出和抖音发布均是 Jovi 人工操作。

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
- 当前 scope 所需主题 Fixture、live topic（仅 `topic_only_v1`）、参考视频（legacy 或 topic-only 中实际提供时）、生命周期和边界审计均通过。

Gate 只运行一次；失败后保留 `PHASE1_FAILED.json` 并停止。

## 9. 状态更新

只有 Gate 通过且获得单独授权时，才原子更新 `PROJECT_STATUS.yaml`。不得在同一任务中进入 Phase 2。
