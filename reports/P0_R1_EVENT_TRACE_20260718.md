# P0 R1 Event Trace — FAILED

真实 `p0-file-test.txt` 于 2026-07-18 22:25:32（Asia/Shanghai）进入现有飞书群，并成功下载。Router 在同一 VideoFactory Session 中调用了一次 `ingest__ingest_attachment`。

失败发生在确定性入库的大小校验层：Router 参数声明 `size_bytes=67`，Channel 实际文件为 55 字节，MCP 返回：

```text
status=rejected
error_code=size_mismatch
quarantined=false
analysis_allowed=false
```

没有生成 receipt，没有调用任何 Analyzer，也没有继续分派。Gateway 记录原群 `queuedFinal=true, replies=1`，并向原群返回失败说明。

结论：`R1_FAILED:ingest.size_mismatch`。按照验证协议立即停止，不猜测修复，不要求继续上传。代码、配置、Agent、Binding、Cron、模型、Tool Policy 和 Gateway 均未修改。
