# PINK-PIG-FACTORY-PHASE1-HARDENING-002

仓库：`E:\project\OpenClaw_VideoFactory`

范围：现有 `video_factory/` 的离线 Phase 1 合同加固。未进入 AI Director 实现、Feishu、OpenClaw、Gateway、Binding、OAuth、Cron 或 P0 Gate。

## 完成

- 新增结构化错误合同：`code`、`message`、`context`。
- 统一 Schema 错误码：
  `asset_registry_invalid`、`storyboard_schema_invalid`、
  `timeline_schema_invalid`、`video_job_invalid`、
  `video_job_state_invalid`。
- 将小粉猪风格规范外置到 `style_profile.json`，Registry 只保留引用。
- Registry 对 SVG-only pose 使用显式 fallback，loader 不再吞掉 Schema 错误。
- 新增 `VideoRenderJobState` 生命周期 Schema，覆盖 draft → completed/failed。
- 新增非 AI `Director.create_storyboard(topic)` 接口桩，当前 fail-closed。
- 新增真实 ffprobe/SRT/timeline 组合的 `render_report.json`。
- 放行架构文档、Change Request 和本任务报告的 Git 跟踪，同时保留原有 ignore 规则。

## 修改文件

本任务新增或修改的核心文件：

- `video_factory/pipeline/errors.py`
- `video_factory/pipeline/validation.py`
- `video_factory/pipeline/render_report.py`
- `generate_video.py`
- `src/factory/assets/pink_pig/registry.json`
- `src/factory/assets/pink_pig/registry.schema.json`
- `src/factory/assets/pink_pig/style_profile.json`
- `src/factory/assets/pink_pig/loader.py`
- `src/factory/director/__init__.py`
- `src/factory/director/director_contract.py`
- `schemas/video/video_job_state.schema.json`
- `schemas/video/README.md`
- `tests/video/test_error_contract.py`
- `tests/video/test_style_profile.py`
- `tests/video/test_video_job_state.py`
- `tests/video/test_director_contract.py`
- `tests/video/test_quality_report.py`
- 既有 Registry/Schema/Storyboard 测试中的旧错误合同断言
- `docs/PINK_PIG_PHASE1_ARCHITECTURE.md`
- `src/factory/assets/pink_pig/README.md`
- `video_factory/README.md`
- `.gitignore`
- `tasks/todo.md`
- `reports/change_requests/PINK-PIG-FACTORY-PHASE1-HARDENING-002.json`

## 测试

执行环境：

`C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe`

| 检查 | 结果 |
|---|---|
| `pytest tests/video -q` | **198 passed** |
| `pytest video_factory/tests -q` | **5 passed** |
| `generate_video.py --job tests/video/fixtures/job_offline.yaml` | **退出码 0** |
| `generate_video.py --config examples/pink_pig_demo/config.yaml` | **退出码 0** |
| 离线 MP4 `ffmpeg -v error -i ... -f null -` | **退出码 0** |
| 独立 ffprobe | **1080×1920 / h264 / 30fps / AAC / 12.5s** |
| `git diff --check` | **通过**（仅有既存 CRLF 提示） |
| 旧 `storyboard_invalid` / `schema_unknown` 代码扫描 | **无生产代码残留** |
| `docs/PINK_PIG_PHASE1_ARCHITECTURE.md` ignore 检查 | **未忽略** |

原有 158 项 video 测试未删除；当前总数为 198。

真实质量报告：

`dist/story_demo_offline/render_report.json`

报告与实际 MP4 一致：12.5 秒、1080×1920、h264、30fps、AAC 48kHz、5 条烧录字幕、5 个按场景顺序记录的 asset IDs。

## 阶段边界

- `PROJECT_STATUS.yaml` 在任务开始前已有修改；本任务未写入它。
- 正式状态仍为 P0 `not_started`，P1 仍 `blocked_by_P0`。
- 没有执行 Git commit、push、reset 或清理。
- 没有修改 OpenClaw、Feishu、Gateway、Binding、OAuth、Cron。

## 剩余债务

- AI Director 尚未实现；本轮仅提供接口桩。
- Video Job 生命周期没有持久化、转换执行器或重试引擎。
- `quality_checks` 目前是结构化人工检查合同，尚未做像素级自动审核。
- `question`、`warning`、`ending` 仍使用现有 render-ready fallback。
- Feishu 调用属于路线 004，自动运营属于路线 005。
- P0/P1 正式 Gate 尚未执行，也未因本任务获得晋级。

PINK_PIG_FACTORY_PHASE1_HARDENED
