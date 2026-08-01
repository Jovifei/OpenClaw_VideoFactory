# P0-SINGLE-GROUP-MEDIA-ROUTER-006：离线测试计划

运行器：Pester 3.4.0；测试文件：`tests/Test-SingleGroupMediaRouter.ps1`。这是纯离线契约测试，不调用真实 Feishu、模型、Gateway 或 GPU。

| 编号 | 验收断言 | 测试方式 |
|---|---|---|
| H1 | 普通文本进入 router | mock text message，验证 text route |
| H2 | TXT 先入库、后处理 | receipt 未完成前 analysis count 为 0 |
| H3 | PNG 入库前图像分析为 0 | pre-dispatch counter |
| H4 | MP4 入库前视频分析为 0 | pre-dispatch counter |
| H5 | 音频入库前转录为 0 | pre-dispatch counter |
| H6 | 入库失败不调用分析 | rejected receipt，analysis count 为 0 |
| H7 | receipt 成功只调一个正确 Agent | PNG 只产生 image-analyzer 一次调用 |
| H8 | analyzer 只收四类安全参数 | 仅允许 receipt_path/stored_path/job_id/analysis_policy |
| H9 | 原始 inbound 路径不可传递 | raw path 不出现在 analyzer 参数 |
| H10 | 多模态失败不回退文本模型 | 返回 `multimodal_model_unavailable`，不产生 fallback call |
| H11 | 其他 13 个 Agent 不受影响 | 14 总数减当前 router 为 13 |
| H12 | Binding 仍为 14 | 固定拓扑不变量断言 |
| H13 | 目标群消费者仍为 1 | 固定拓扑不变量断言 |
| H14 | 普通文本 Session 连续 | 同一 reply target 的连续 text route |
| H15 | 最终回复回原群 | `reply_target` 保持 same-group |

## 必须额外做的 runtime smoke（下一阶段）

离线测试不能证明以下三点：

1. scope deny 在真实目标 session key 上命中，并且 pre-reply media understanding 调用计数为 0；
2. text-only router 收到的 payload 不含原始图片像素；
3. OpenClaw 最终 tool policy 中确实没有 `read`/`exec`/直接媒体读取，且后置 Agent 只见 stored copy。

这些验证必须在用户批准配置写入范围后，用备份、配置 diff、Gateway 日志和可回滚 smoke 完成。Child Claude 的输出只能作为审计建议，不能替代上述证据。

## 既有回归

现有 `tests/Test-IngestInboundMedia.ps1` 已独立通过 32/32；本轮不修改入库脚本，不重新解释该结果为 Gateway 证明。
