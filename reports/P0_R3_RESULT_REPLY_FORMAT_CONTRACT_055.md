# P0 R3 Image Result Reply Format Contract 055

## Trusted input boundary

Only the server-owned completed `analyze_image` result artifact is read. The Router never supplies a path, receipt, hash, attachment, model, Analyzer, or presentation content. The result artifact must be under the project jobs root, named `analysis.json`, and identify a completed `analyze_image` run.

## Stable mapping

| Analyzer data | User-visible field |
| --- | --- |
| `summary`, `description`, `content`, `text`, `result_text`, or `outputs[].text` | 内容概述 |
| `subjects`, `objects`, `scene`, `visual_features`, `composition`, or `colors` | 视觉要点 |
| `ocr`, `visible_text`, or `recognized_text` | Optional 识别文字 when available |
| `limitations`, `uncertainties`, `risks`, or `confidence` | 注意事项 |
| `conclusion`, `recommendation`, `suggestion`, or `advice` | 结论 |

The formatter emits a concise Chinese reply, normally 80–220 characters:

```text
图片分析结果：
- 内容概述：……
- 视觉要点：……
- 注意事项：……
- 结论：……
```

## Fail-closed presentation

If the completed result is missing, malformed, outside the server-owned jobs root, empty, or cannot be safely rendered, the public result is `presentation_failed` with a Chinese rendering error. An image result may never fall back to `媒体处理已完成。`.

Before publishing, the formatter removes internal paths, SHA-256 strings, Ticket-like values, message/chat/sender identifiers, control characters, and potential mentions. It never exposes raw model JSON.
