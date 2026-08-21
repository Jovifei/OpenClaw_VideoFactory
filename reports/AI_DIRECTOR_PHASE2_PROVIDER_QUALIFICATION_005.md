# AI-DIRECTOR-PHASE2-PROVIDER-RECOVERY-QUALIFICATION-005

## 1. 真实状态

本轮从 `AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED` 开始。正式状态保持 P0 `not_started`、P1 `blocked_by_P0`、P2 `blocked_by_P1`。本轮未达到真实 Provider 资格，最终状态为：

```text
BLOCKED_PROVIDER_CACHE_DRIFT
```

## 2. 已完成阶段

- [x] [1/12] Change Request、分支/HEAD、index、六个 dirty 文件 hash 和基线测试冻结。
- [x] [2/12] 只读确认 npm Codex CLI 0.146.0、必需参数、cache shape、config/auth hash 和禁止面。
- [x] [3/12] 独立环境 reviewer 确认 `models_cache.json` 是模型列表派生缓存，并批准 exact-target/hash-bound/byte-exact rollback 方案。
- [ ] [4/12] 未完成：pre-move hash recheck 发现活动 cache 已漂移，未创建备份或 quarantine。

## 3. 基线证据

使用固定 workspace Python：

```text
tests/director: 47 passed
tests/video: 273 passed
video_factory/tests: 5 passed
legacy candidate/final-audit: 56 passed, 1 skipped, 13 subtests
```

index 为空。分支为 `codex/ai-director-video-factory-phase2-001`，HEAD 为 `76180a59ea662bdf168d88baaeb777d3e8eb59ef`。

## 4. Provider 只读审计

已确认：

- PATH 首选 npm Codex CLI，版本 `0.146.0`。
- `codex exec --help` 支持 `--ephemeral`、`--sandbox read-only`、`--skip-git-repo-check`、`--ignore-user-config`、`--output-schema`、`--output-last-message`、`-C` 和 stdin `-`。
- cache 是合法 JSON，顶层为模型列表结构，模型条目数为 9，`base_instructions` 缺失数为 9。
- `config.toml` SHA-256 为 `802f4237d7b7bd1d4eb08d54d4523338e2aa09dc563b43baf03c41e7140b4c1b`。
- `auth.json` SHA-256 为 `b5cfd4115b139d27df4a165a370692b2342ec9fa6d950150206525576c0cc946`。
- 官方 OpenAI Codex issue 将 `models_cache.json` 描述为模型列表缓存，并展示 `fetched_at/etag/client_version/models` 结构：[OpenAI Codex issue #32496](https://github.com/openai/codex/issues/32496)。

## 5. 阻塞证据

只读审计时 cache SHA-256 为：

```text
046b9dd60f2d0f1cf97c5b99195e2a5231799e6d8b98a8f0c54d30f9685d9ec3
```

只读环境 reviewer 随后再次读取时已观察到中间 hash：

```text
60d56ed239b4f23aaddcecba84daebe4dafe5068d94bd95135c10c672054eb22
```

在任何移动前重新核对时，SHA-256 已变为：

```text
98bb3e3ac1cc0417544a8f795940c2707b14b2007c9d097489f42440da5cc090
```

随后一次不调用 CLI 的只读复核又得到：

```text
89dc71bf54cb192dd1d8ccc4b9c511d5c920373674f338f6e4947d0fa4a2533f
```

文件大小由 215773 bytes 变为 215770 bytes。该变化不是 005 执行的：本轮没有复制、移动、删除或编辑 cache，也没有运行 `codex exec`。因此无法建立计划要求的 hash-bound backup。

最终只读复核再次得到 SHA-256：

```text
d0cc1bc450d2541ae63d059bf71f1e947c7e671244f7082e1458fa2f1f82d1c1
```

大小回到 215773 bytes；这再次确认目标仍由外部进程改变，不能作为稳定 hash-bound 目标。

## 7.1 授权恢复尝试后的新阻塞

用户授权继续后，重新执行了 [1/12] 基线：Director 47、Video 273、Video Factory 5、legacy 56 passed / 1 skipped。此前 PID 13596 子进程已退出，但 Codex Desktop 自动重新拉起新的 app-server PID 11968；随后只读复核得到新的 SHA-256：

```text
81c33af97ff7bca6aa01ef08a2ef1357ffa842dfe40888ca7df63b2595863230
```

该变化证明父桌面进程仍可重新建立 cache writer。没有执行备份、quarantine、smoke 或 Provider acceptance；当前仍为 `BLOCKED_PROVIDER_CACHE_DRIFT`。必须关闭或冻结父 Codex Desktop writer 后，才能重新从 [1/12] 建立新基线。

## 6. 未执行事项

以下命令和动作均为 0 次：

- isolated `codex exec` smoke：0
- 真实 `generate_video.py --topic-file` acceptance：0
- cache backup：未创建
- cache quarantine：未创建
- 005 real fixture、MP4、TTS、字幕、抽帧：未执行

## 7. 禁止面与用户文件

六个既有 dirty 文件 hash 未改变；`PROJECT_STATUS.yaml` 未修改。未修改 OpenClaw、Feishu、Gateway、Binding、OAuth、Profile、model、Cron，也未执行 commit、push、reset、clean 或正式 Gate。

## 8. 下一步

必须先关闭或冻结造成 cache 写入的外部 Codex/Desktop 进程，然后从新的授权运行重新执行 [1/12]–[3/12]，获得稳定 hash 后才能进入 [4/12]。不能使用本轮任一旧 hash 移动 cache，也不能重复猜测 Provider 修复。

下一轮重新获得稳定 cache hash 并完成 smoke/real acceptance 后，才可判断是否进入 `AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED`；本报告不声明该状态。

BLOCKED_PROVIDER_CACHE_DRIFT
