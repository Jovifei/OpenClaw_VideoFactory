# 02 — Phase 2：OpenClaw、Direct Codex CLI 与飞书配置（V2.5）

> 这是 **Phase 2 飞书自动化** Runbook，不是当前 Phase 1 本地视频工厂的启动步骤。
> 在 Phase 1 中不得运行本文件的配置、Gateway、飞书、lark-cli 或 smoke 命令；
> 需要进入 Phase 2 时仍须取得 Jovi 的单独授权。

## 1. 捕获状态

```powershell
powershell -File .\scripts\02_capture_openclaw_state.ps1
```

保存Schema、配置验证、doctor、Gateway、channels、skills、cron和security audit。

## 2. OpenClaw版本

飞书官方Channel要求2026.5.29+。版本不足时先写升级/回滚计划，用户同意后执行`openclaw update`并重跑验证。

## 3. 配置规则

绝不覆盖整份`openclaw.json`。先：

```powershell
openclaw config schema > .\reports\openclaw_state\config_schema.json
openclaw config get agents.defaults.workspace
openclaw config get tools.exec.mode
```

对每个字段：Schema→当前值→最小补丁→备份→应用→`config validate`→`doctor`→`gateway status`→保存回滚。

目标：workspace根目录、Asia/Shanghai、exec auto、cron启用、loopback。不要在未验证前设置全局tools.allow。

## 4. Direct Codex CLI

`video-factory` 使用稳定的 OpenClaw Default Runtime 即可。OpenClaw Codex Plugin 状态为 `deferred_optional_not_blocking`；P0 不运行 `/codex` 命令，不排查 Plugin OAuth，不修改 Profile、auth order、模型或 Runtime。

在项目根目录分别运行 Direct Codex CLI 只读和 workspace-write smoke。用执行前后全工作区 SHA-256 清单证明第一条零变化、第二条只产生 `reports/codex_cli_smoke.txt`。生成 `reports/CODEX_CLI_SMOKE.json` 和 `.md`。

## 5. OpenClaw官方飞书Channel

```powershell
powershell -File .\scripts\04_setup_openclaw_feishu.ps1
powershell -File .\scripts\04_setup_openclaw_feishu.ps1 -Apply
```

向导选择中国大陆飞书域、WebSocket。安全：DM allowlist，只允许用户open_id；群allowlist，只允许固定chat_id；群默认需@机器人；禁止`allowFrom:["*"]`。

完成：

```powershell
openclaw gateway restart
openclaw gateway status
openclaw channels status
openclaw logs --follow
openclaw pairing list feishu
```

飞书发送`/status`、小文件和短视频。

## 6. 安全ID

open_id通过DM日志或pairing获得；群chat_id格式`oc_xxx`。只存本机安全配置，不进Git。

## 7. 官方lark-cli

OpenClaw Channel是主入站；lark-cli负责复杂Markdown、附件、视频和可选文档操作。

```powershell
powershell -File .\scripts\03_install_lark_cli.ps1
powershell -File .\scripts\03_install_lark_cli.ps1 -Apply
powershell -File .\scripts\05_configure_lark_cli.ps1 -CheckStatus
```

需要新应用配置时用`-StartAppConfiguration`。授权URL必须原样展示并生成二维码，不得同轮阻塞让用户看不到链接。默认bot身份；个人Drive/Docs才需要user OAuth。

## 8. smoke test

先生成无敏感信息的 `p0-file-test.txt`、`p0-image-test.png`、`p0-video-test.mp4`。然后：

```powershell
powershell -File .\scripts\05_feishu_smoke_test.ps1 -TargetKind direct -TargetId "ou_xxx"
```

确认后加`-Apply`。测试Markdown、图片、文件、视频+封面、幂等、非法目标和重复调用。

## 9. 双重消费

OpenClaw Channel唯一主入站；`lark-cli event`只做诊断或明确fallback。入站消息以`message_id`唯一约束。

## 10. P0证据

生成：`reports/CODEX_CLI_SMOKE.json`、`FEISHU_SINGLE_CONSUMER_TEST.json`、`FEISHU_INGRESS_TEST.json`、`FEISHU_EGRESS_TEST.json`、`OPENCLAW_EXISTING_AGENTS_REGRESSION.json`、`SKILL_VISIBILITY.json`，再运行 P0 gate。

P0 要求：单消费者与消息去重；TXT/PNG/MP4 真实入站；receipt/hash/quarantine；lark-cli Markdown/PNG/TXT/MP4 真实出站与幂等；原有 Agent/Binding/Cron 回归；无 VideoFactory 正式 Cron。P0 不要求 OpenClaw Codex Plugin OAuth、`/codex status`、`/codex models` 或 OpenAI Codex Runtime。
