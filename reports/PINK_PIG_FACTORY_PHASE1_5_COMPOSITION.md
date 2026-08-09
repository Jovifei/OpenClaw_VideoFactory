# PINK_PIG_FACTORY_PHASE1_5_COMPOSITION_ENGINE

日期：2026-08-09
仓库：`E:/project/OpenClaw_VideoFactory`
分支：`codex/pink-pig-phase1-5-composition`
范围：只加固现有 `video_factory/`，不创建第二套 pipeline。

## 1. 完成事项

- 新增 `knowledge_illustration` Composition Contract：1080×1920 画布，brand `y=80..180`、content `y=240..1040`、subtitle `y=1120..1580`、signature `y=1760..1860`。
- 新增 `SubtitleLayoutEngine`：字幕 52–60px、左右 90px、最多两行；content/subtitle 重叠在渲染前以 `subtitle_overlap_content` fail-closed。
- Registry 注册五张本地 Modbus RTU 知识插图和透明 `pink_pig.signature.v1`；每张资产 SHA-256 已核对。
- 新增 Pink Pig quality gate，验证 Registry asset、style profile、character、skill、core action 和 signature。
- Storyboard/Timeline 增加可选 `layout_mode`、`subtitle_layout`、`character_position`、`content_region`，由现有 compiler 传播。
- 现有 renderer 增加 composition content overlay、signature overlay 和受合同约束的字幕样式；legacy `--config` 行为保持回归兼容。
- 新增四场景 `examples/pink_pig_modbus_demo/`，每幕使用不同知识插图。
- 更新仓库文档、任务记录、Obsidian 项目笔记和精确 `.gitignore` 例外。

上游 `Jovifei/ian-fenzhu-illustrations` 本轮按 Pink Pig skill 使用为 style DNA、persona 和 composition rules；它不是图片库。视频图片来自本仓库 Registry。

## 2. 修改文件

核心修改/新增：

- `schemas/video/composition.schema.json`
- `schemas/video/storyboard.schema.json`
- `schemas/video/timeline.schema.json`
- `video_factory/configs/compositions/knowledge_illustration.json`
- `video_factory/pipeline/composition.py`
- `video_factory/pipeline/pink_pig_quality.py`
- `video_factory/pipeline/subtitle.py`
- `video_factory/pipeline/renderer.py`
- `video_factory/pipeline/render_report.py`
- `video_factory/pipeline/storyboard.py`
- `video_factory/pipeline/asset_loader.py`
- `generate_video.py`
- `src/factory/assets/pink_pig/registry.json`
- `src/factory/assets/pink_pig/registry.schema.json`
- `src/factory/assets/pink_pig/README.md`
- `assets/pink_pig/signature.png`
- `examples/pink_pig_modbus_demo/{storyboard.json,job.yaml}`
- `tests/video/test_composition_schema.py`
- `tests/video/test_composition_failure.py`
- `tests/video/test_pink_pig_quality.py`
- `tests/video/test_mascot_and_subtitle.py`
- `tests/video/test_quality_report.py`
- `docs/PINK_PIG_PHASE1_ARCHITECTURE.md`
- `video_factory/README.md`
- `schemas/video/README.md`
- `tasks/todo.md`, `tasks/lessons.md`, `handoff/codex/IMPLEMENTATION_BACKLOG.yaml`

另外只更新了 legacy 示例的 Registry 版本引用（`examples/pink_pig_story_demo/storyboard.json`），并让 legacy manifest 忽略 Registry 保留的 `signature.png`，避免签名被错误当作第六场景。

## 3. 测试命令与结果

固定解释器：

```text
C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe
```

定向组合/字幕/Schema/质量测试：**90 passed**。
完整视频回归：

```text
python -m pytest tests/video -q       -> 273 passed
python -m pytest video_factory/tests -q -> 5 passed
```

离线/legacy 命令：

```text
python generate_video.py --job tests/video/fixtures/job_offline.yaml -> exit 0
python generate_video.py --config examples/pink_pig_demo/config.yaml -> exit 0
python generate_video.py --job examples/pink_pig_modbus_demo/job.yaml -> exit 0
```

`git diff --check` 通过（仅有 Windows 行尾提示，无 whitespace error）。旧合同 `storyboard_invalid` 已无残留；Director 专用 `director_storyboard_invalid` 不属于旧 Schema 合同。核心模块导入和 cloneable-path audit 通过；由于工作区含用户既有 dirty 文件且本轮未 commit，未声称 fresh Git clone smoke。

## 4. MP4、ffprobe 和 render report 证据

主证据：

- MP4：[dist/pink_pig_modbus_demo.mp4](../dist/pink_pig_modbus_demo.mp4)
- 工作目录：`dist/pink_pig_modbus_demo/`
- 报告：`dist/pink_pig_modbus_demo/render_report.json`
- 中间物：`timeline.json`、`subtitle.srt`、`run_report.json`、`storyboard.resolved.json`

`render_report.json` 与独立 ffprobe 一致：

```json
{
  "duration": 27.8,
  "resolution": {"width": 1080, "height": 1920},
  "fps": 30.0,
  "codec": "h264",
  "audio": {"present": true, "codec": "aac", "sample_rate": 48000},
  "subtitle": {"present": true, "mode": "burned_in", "cue_count": 4},
  "assets_used": [
    "pink_pig.knowledge_master_slave.v1",
    "pink_pig.knowledge_frame_layout.v1",
    "pink_pig.knowledge_serial_parameters.v1",
    "pink_pig.knowledge_summary.v1",
    "pink_pig.signature.v1"
  ],
  "subtitle_region": {"x": 90, "y": 1120, "width": 900, "height": 460},
  "layout_mode": "knowledge_illustration"
}
```

独立 `ffmpeg -v error -i ... -f null -` 对 Modbus MP4、offline MP4 和 legacy demo MP4 均 exit 0。抽帧复核确认插图完整位于 content 区，字幕位于下方 subtitle 区，底部保留小粉猪签名，未遮挡知识图。

## 5. Git ignore 跟踪验证

`.gitignore` 末端保留既有规则，并追加精确例外：

```gitignore
!docs/
docs/*
!docs/PINK_PIG_PHASE1_ARCHITECTURE.md
!reports/PINK_PIG_FACTORY_PHASE1_5_COMPOSITION.md
!reports/change_requests/PINK-PIG-FACTORY-PHASE1-5-COMPOSITION-ENGINE.json
```

`git check-ignore -q -- docs/PINK_PIG_PHASE1_ARCHITECTURE.md` 的实际退出码为 **1**；`git status --short --untracked-files=all` 可看到架构文档和本 Change Request/报告路径。

## 6. 禁止面确认

执行前后的控制面 SHA-256 快照一致；本任务没有写入 OpenClaw、Feishu、Gateway、Binding、OAuth、Cron 或 `PROJECT_STATUS.yaml`。以下文件在执行开始前已经是用户 dirty 内容，本轮保留且未清理：

```text
PROJECT_STATUS.yaml                         CD0DC97280ED86ABAC748DCEAFF73A45587A92656D4481E782B37AA33002785D
reports/P0_ACCEPTANCE_MATRIX_V2.yaml        ACCCF9E9440776583857C67BA15094EF461F1B61DFE0EBD436FA68B4E3B6905E
scripts/analysis_request.py                 68BDD12EBC45D92FFF17AE01DEC7F6C4EFCD0CEF3E89AEB68434EC9EBED9EA1D
scripts/analyzer_mcp.py                     BCF09DB631EED87316C4D2B0664ABC159470860B0D3E84C7E8C3460071E09D90
scripts/mcp_ingest_attachment.py            313F00B8F855FAAF2AD22CD01A61D987670D0FF02FF4C9DE3D57970039A7D52B
scripts/media_action_ticket.py              794B0ED4DEA1FB18EB52371D1FCDDC4724D8D781B141B09214545E5AF19699E5
```

未执行 commit、push、reset、clean；未进入 AI Director、Feishu 或 P0 Gate。

## 7. 剩余债务

- 当前只实现 Composition Engine，AI Director 003 的既有本地接口不在本轮扩展。
- 生命周期持久化、状态转换执行器和重试引擎尚未实现。
- style quality checks 仍是结构化/人工规则，尚无像素级自动审核。
- question、warning、ending 三个 SVG-only pose 继续 fallback 到 normal。
- TTS 网络关闭时示例使用可验证 BGM fallback；需要真实旁白时仍需单独配置和验收。
- Feishu 接入属于 004，自动运营属于 005；正式 P0/P1 状态未改变。
- 当前工作区仍有用户既有未提交内容；本轮未 commit/push，因此 fresh-clone 验证要在用户授权提交后单独执行。

PINK_PIG_FACTORY_PHASE1_5_READY
