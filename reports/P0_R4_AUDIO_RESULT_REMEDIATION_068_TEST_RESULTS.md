# P0-R4 音频结果展示修复（068）

状态：`PASS_OFFLINE_REPAIR_LIVE_RETEST_REQUIRED`

## 根因

真实 `transcribe_audio` 产物是已完成的 `transcript.json`，其 `transcript`、
`language`、`engine`、`device` 和 `model` 都在顶层。展示层错误读取不存在的
嵌套 `result`，因此把真实转录当成空结果。

## 修复

只修改 `scripts/mcp_ingest_attachment.py` 的音频展示读取：把已通过状态、工具名、
路径和文件名校验的完整文档交给现有有界格式化器。未修改 Ticket、receipt、Analyzer、
GPU、模型、MIME 或配置合同。

## 验证

- 修复前红测：真实顶层形状产生 `result_content_empty`；嵌套形状被错误接受。
- 修复后音频定向回归：3/3 通过。
- P0 目标回归：170/170 通过（29.071 秒）。
- `py_compile scripts/mcp_ingest_attachment.py`：通过。
- 直接加载这次真实完成的音频产物：`status=ready`，回复以“音频转录结果：”开头，
  长度 134，未泄露本地路径。

## 边界

项目 `.venv` 的 `faster_whisper` 导入检查失败，但这不是本次空回复的根因：真实
产物已证明某个 Analyzer 运行时完成了 faster-whisper CUDA 转录。未安装依赖、未下载
模型、未重放旧 Ticket。要取得修复后的真实 R4 证据，必须重新上传音频并使用新 Ticket。
