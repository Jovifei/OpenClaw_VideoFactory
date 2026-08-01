# OpenClaw VideoFactory

Windows 原生的 OpenClaw 短视频工厂工程。项目由 OpenClaw 负责长期编排、飞书入口、任务状态和重试；本仓库提供安全的媒体入站、显式 Ticket 分析、分析器边界、测试、Runbook 和 P0 证据。

GitHub：<https://github.com/Jovifei/OpenClaw_VideoFactory>

## 当前状态

- 当前阶段：P0；`PROJECT_STATUS.yaml` 保持 `P0: not_started`。
- 已验证：TXT `text/plain` 显式 Ticket 分析、图片结果展示、视频基础分析和音频转录产物展示修复。
- 音频最新修复：`transcribe_audio` 的真实 `transcript.json` 使用顶层字段，展示层已按真实产物形状读取；修复后的真实 R4 群内复测已返回完整转录，R5/P0 Gate 仍未进入。
- 不自动发布抖音，不自动分析附件，不解析 DOCX/PDF 正文，不下载未批准的模型或节点。

## 开始阅读

1. 阅读 [`START_HERE_CODEX.md`](START_HERE_CODEX.md)、[`PROJECT_STATUS.yaml`](PROJECT_STATUS.yaml) 和 [`AGENTS.md`](AGENTS.md)。
2. 使用 Windows PowerShell 进入仓库目录。
3. 只按 P0 Runbook 执行预检，不跳过阶段门禁。

```powershell
Set-Location E:\project\OpenClaw_VideoFactory
powershell -File .\scripts\00_bootstrap_python.ps1
powershell -File .\scripts\00_package_check.ps1
powershell -File .\scripts\01_machine_preflight.ps1
```

## 媒体分析协议

附件先入库、隔离、校验哈希并生成 receipt；附件消息本身不触发分析。只有同一群组、同一发送者对该附件的后续明确命令，才允许消费一次性 Ticket：

```text
/vf image <new-ticket>
/vf audio <new-ticket>
/vf video <new-ticket>
/vf text <new-ticket>
```

Ticket 不应粘贴到外部聊天或重复使用。分析器只读取隔离副本，结果写入受控 `jobs/<job>/` 产物并由服务端格式化为有限长度的公开回复。

## 代码与验证

核心目录：

- `scripts/`：入站、Ticket、分析器 MCP 和安全边界。
- `src/`、`services/`：工程实现与受控服务接口。
- `skills/`：OpenClaw 本地 Skill。
- `schemas/`：事件、receipt、Ticket 和报告契约。
- `tests/`：离线回归与安全边界测试。
- `runbook/`、`tasks/`、`handoff/codex/`：执行顺序、计划和验收信息。
- `reports/P0_*.json|md`：筛选后的 P0 证据；敏感和冗长报告不发布。

媒体分析目标回归：

```powershell
& .\.venv\Scripts\python.exe -m unittest tests.test_analyzer_mcp tests.test_analysis_request tests.test_media_action_ticket tests.test_ingest_attachment_core tests.test_two_message_mcp_surface tests.test_two_message_flow tests.test_trusted_media_roots
& .\.venv\Scripts\python.exe -m py_compile scripts\mcp_ingest_attachment.py
```

当前目标回归为 170/170。项目 `.venv` 是否具备 `faster-whisper` 不能替代实际 Analyzer 运行时证据；模型安装和下载必须单独审批。

## 发布边界

`.gitignore` 排除个人环境、凭据、飞书入站媒体、jobs/receipt/Ticket 状态、输出物、模型、依赖缓存、实验和研究资料；`docs/`、产品/研究/归档文章及敏感报告也不进入仓库。只提交可复现的代码、模板、测试、Runbook、任务信息和脱敏 P0 证据。

系统不自动发布抖音；生产 Cron、Gateway 生命周期、OpenClaw 配置、模型下载和 P0/P1 Gate 都必须遵守项目授权边界。
