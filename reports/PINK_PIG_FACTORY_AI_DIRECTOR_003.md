# PINK-PIG-FACTORY-AI-DIRECTOR-003

## 1. 完成事项

- 保留 `Director.create_storyboard(topic) -> Storyboard` 公共接口，并新增 `AIDirector`、`DirectorProvider` 与只读 `CodexCliDirectorProvider`。
- 新增受限 `DirectorDraft` 与脱敏 `DirectorRunReport` Schema；模型不能输出资产路径、`asset_id`、Registry、scene ID、order 或渲染参数。
- 新增确定性 context/prompt builder：NFKC topic、200 字符上限、固定 `pink_pig_director_v1`、Pink Pig Registry/style profile 和 evergreen 主线约束。
- Python 确定性注入 Storyboard ID、IP/Registry、scene ID/order、globals、narration duration intent 和终幕 transition；复用现有 compiler、asset selector、`run_job()`、字幕、音频、FFmpeg 与 render report。
- `generate_video.py --topic ... --director-provider codex-cli` 已接入，稳定目录为 `dist/director/<topic_sha16>/`，不创建第二套 pipeline。
- provider 使用参数数组、`shell=False`、`--ephemeral`、`--sandbox read-only`、`--skip-git-repo-check`、`--ignore-user-config`、180 秒超时和 256 KiB 上限；失败均 fail-closed。
- 完成离线 fake-provider、provider 安全、prompt injection、Schema/语义验证、重试、稳定 ID 与 topic pipeline 测试。

## 2. 公共接口和 Schema

- `src/factory/director/director_contract.py`：稳定基类接口，仍以 `NotImplementedError("director_not_implemented")` 作为未实现基类行为。
- `src/factory/director/ai_director.py`：`AIDirector(Director)`，Draft → Schema → 语义 → Storyboard Schema → 编译验证，最多三次尝试。
- `src/factory/director/provider.py`：`DirectorProvider` Protocol 与 Direct Codex CLI adapter。
- `schemas/video/director_draft.schema.json`：5–9 幕、固定 scope、八种合法 pose、固定 scene 字段、拒绝额外字段。
- `schemas/video/director_run_report.schema.json`：provider/version、prompt version、digest、尝试次数、验证状态、Storyboard SHA-256、编译时长、`factual_review_required` 和结构化 error。
- 统一复用 `code/message/context` 错误合同；不记录原始 prompt、原始模型输出、凭据或绝对路径。

## 3. 修改文件

主要新增/修改：

- `src/factory/director/{__init__.py,README.md,context.py,provider.py,ai_director.py}`
- `video_factory/configs/director_job.defaults.yaml`
- `video_factory/pipeline/validation.py`
- `video_factory/README.md`
- `generate_video.py`
- `schemas/video/{director_draft.schema.json,director_run_report.schema.json,README.md}`
- `tests/video/test_director_{contract,draft_schema,run_report_schema,context,provider,security,ai_director,topic_pipeline}.py`
- `docs/PINK_PIG_PHASE1_ARCHITECTURE.md`
- `.gitignore`
- `tasks/todo.md`
- 本报告及 `reports/change_requests/PINK-PIG-FACTORY-AI-DIRECTOR-003.json`

既有用户工作区中的 OpenClaw/Feishu/P0 记录保留原状，未被本任务清理或重写。

## 4. Fake provider 测试

固定 Python 定向集合结果：**56 passed**。

覆盖公共签名、Draft Schema、run-report Schema、context、prompt injection、provider 参数安全、CLI 错误、输出上限、空/超长 topic、非法 draft、重试耗尽、稳定 ID、Registry/IP/globals 注入、现有 `run_job()` 复用和 sandbox 清理。

## 5. 真实 Direct Codex CLI 证据

执行：

```text
python generate_video.py --topic "介绍 Modbus RTU" --director-provider codex-cli
```

最终工作目录：`dist/director/director_06b00f079b94d3e8/`。

- provider：`codex-cli`
- provider version：`codex-cli 0.146.0`
- attempts：`1`
- prompt version：`pink_pig_director_v1`
- Storyboard：7 scenes，Schema/semantic/storyboard validation 全部 pass
- compiled duration：51.6 秒
- `factual_review_required`：`true`
- report error：`null`
- 原始 CLI 诊断中发现 Draft Schema 的 `content_scope` 缺失 `type`；已修复 Schema 后重新通过。该修复未放宽 Draft 字段边界。

## 6. Storyboard / Timeline / MP4 / render report 证据

最终目录包含：`storyboard.json`、`director_report.json`、`video_job.yaml`、`storyboard.resolved.json`、`timeline.json`、`subtitle.srt`、`render_report.json`、`run_report.json` 和 `output.mp4`。

独立媒体检查：

- MP4：H.264，1080×1920，30/1，AAC，24 kHz，时长 51.600 秒。
- `render_report.json`：duration 51.6、fps 30.0、字幕 `burned_in`、cue_count 7、audio present、7 个按场景顺序保留重复的 Registry asset IDs。
- `ffmpeg -v error -i ... -f null -`：退出码 0。
- 独立 ffprobe 与 render report 的 duration、resolution、fps、codec、audio 字段一致。

离线 job 证据也重新生成：`dist/pink_pig_story_demo_offline.mp4`，12.5 秒，FFmpeg decode 退出码 0。

## 7. 完整测试命令、数量和结果

```text
python -m pytest tests/video -q
251 passed

python -m pytest video_factory/tests -q
5 passed

python generate_video.py --job tests/video/fixtures/job_offline.yaml
成功，生成 MP4、timeline、subtitle、run_report、render_report

python generate_video.py --config examples/pink_pig_demo/config.yaml
成功，legacy demo duration 5.9 秒，audio enabled
```

另执行了完整 MP4 decode、独立 ffprobe 和 `git diff --check` 检查。新增后 `tests/video` 为 251，超过 198 基线；legacy 为 5/5。

## 8. 禁止面前后 hash

- `PROJECT_STATUS.yaml` 执行前后 SHA-256 均为 `CD0DC97280ED86ABAC748DCEAFF73A45587A92656D4481E782B37AA33002785D`。
- OpenClaw、Feishu、Gateway、Binding、OAuth、Cron 及 P0/P1/P2 Gate 路径未纳入本任务修改；基线中已存在的用户工作区改动保持不变。
- 未执行 commit、push、reset、clean，未修改正式阶段值；本报告不构成正式 phase/Gate 通过。

## 9. Git ignore 跟踪验证

以下命令均按预期返回退出码 1，表示未被 ignore，且 `git status --short --untracked-files=all` 可显示：

```text
git check-ignore -q -- docs/PINK_PIG_PHASE1_ARCHITECTURE.md
git check-ignore -q -- reports/PINK_PIG_FACTORY_AI_DIRECTOR_003.md
git check-ignore -q -- reports/change_requests/PINK-PIG-FACTORY-AI-DIRECTOR-003.json
```

原有 `.gitignore` 规则未删除或重排，仅在末端增加精确例外。

## 10. 剩余债务

- AI 热点仍需要 factual brief、来源和事件日期合同。
- AI 输出仍需人工事实审核。
- VideoJob 生命周期数据库、转换执行器和重试引擎未实现。
- style quality checks 尚无像素级自动审核。
- 三个 SVG-only pose 仍使用 fallback。
- Direct Codex CLI 是当前首个 provider，尚无第二生产 provider。
- Feishu 调用属于 004；自动运营属于 005。
- 正式 P0/P1/P2 Gate 均未改变。

PINK_PIG_FACTORY_AI_DIRECTOR_003_COMPLETE
