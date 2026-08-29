# MoneyPrinterTurbo 文案草稿器设置与使用指南

一句话定位：把一个主题关键词变成多条候选旁白文案草稿，供人工审阅后进入现有原创 brief 流程——只产出文字，不触碰任何渲染链（TTS、素材、字幕、成片一律不经过 MoneyPrinterTurbo）。

对应变更请求：`PHASE1-MPT-SCRIPT-DRAFTER-002`、`PHASE1-MPT-CONFIG-FINALIZE-003`（见 `reports/change_requests/`）。

---

## 1. 前置条件

| 条件 | 要求 | 当前机器状态 |
| --- | --- | --- |
| 操作系统 | Windows 原生（PowerShell 或 Git Bash） | 已满足 |
| Python | 系统可用的 Python（运行仓库侧脚本） | 已满足 |
| MPT 克隆 | `external/MoneyPrinterTurbo/`（v1.3.5，commit `eb8c237`，MIT 协议，浅克隆，已被 `.gitignore` 排除） | 已就绪 |
| MPT venv | 独立 Python 3.12 虚拟环境 `external/MoneyPrinterTurbo/.venv` | 已就绪 |
| 配置文件 | `external/MoneyPrinterTurbo/config.toml`（gitignored，密钥只允许存在这里） | 首次配置后生成 |

当前机器已完成克隆与 venv 建设，直接从第 2 节开始即可。

## 2. 首次配置 / 密钥轮换流程

配置工具：`scripts/phase1_mpt_configure.py`。它把 LLM 提供商写入 `external/MoneyPrinterTurbo/config.toml`，固定为 OpenAI 兼容格式：

- `llm_provider="openai"`
- `openai_base_url="https://token-plan-cn.xiaomimimo.com/v1"`
- `openai_model_name="mimo-v2.5"`

### 密钥输入方式（按优先级）

1. **环境变量**：`MPT_LLM_API_KEY` 或 `MIMO_API_KEY`（前者优先）。
2. **管道输入**：`--stdin` 从管道读取密钥。
3. **本地文件**：`--key-file` 指向仓库之外的一个本地文件，内容为密钥。

安全规则：

- **禁止**把密钥作为命令行参数传入（会进 shell 历史和进程列表）。
- **禁止**把密钥粘贴到聊天、日志、issue 或任何会进 Git 的文件。
- 密钥只落盘到 `external/MoneyPrinterTurbo/config.toml`（gitignored）。
- 轮换密钥 = 用新密钥重跑同一条配置命令，旧值会被覆盖。

### 方式一：环境变量（PowerShell）

```powershell
$env:MPT_LLM_API_KEY = "<你的API Key>"
python scripts/phase1_mpt_configure.py
```

### 方式一：环境变量（Git Bash）

```bash
export MPT_LLM_API_KEY="<你的API Key>"
python scripts/phase1_mpt_configure.py
```

### 方式二：管道输入（PowerShell）

```powershell
"<你的API Key>" | python scripts/phase1_mpt_configure.py --stdin
```

### 方式二：管道输入（Git Bash）

```bash
printf '%s\n' "<你的API Key>" | python scripts/phase1_mpt_configure.py --stdin
```

### 方式三：密钥文件

```bash
# 文件放在仓库之外，例如 ~/.secrets/mpt_llm_key.txt，内容为单行密钥
python scripts/phase1_mpt_configure.py --key-file ~/.secrets/mpt_llm_key.txt
```

### 可选覆盖项

```bash
python scripts/phase1_mpt_configure.py --base-url "https://token-plan-cn.xiaomimimo.com/v1" --model "mimo-v2.5"
```

`--base-url` 与 `--model` 有默认值，通常无需显式指定；只有端点或模型变更时才使用。

## 3. 验证配置

**只看配置状态（不发请求）**：

```bash
python scripts/phase1_mpt_configure.py --status-only
```

**写入后立即做活探针（真实调用一次 chat completion）**：

```bash
python scripts/phase1_mpt_configure.py --verify
```

建议首次配置和每次轮换密钥后都跑一次 `--verify`，探针通过才算配置完成。

## 4. 日常使用

### 生成候选文案

```bash
python scripts/phase1_mpt_script_drafter.py --subject "I2C总线为什么要上拉电阻" --candidates 3
```

常用参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--subject` | （必填） | 主题关键词 |
| `--candidates` | 3 | 请求的候选条数 |
| `--language` | `zh-CN` | 文案语言 |
| `--paragraphs` | 2 | 每条候选的段落数 |
| `--timeout-seconds` | 120 | 单候选超时 |

### 产物结构

输出目录：`dist/phase1_local/script_drafts/drafter_<时间戳>/`

```text
dist/phase1_local/script_drafts/drafter_20260829_213516/
└── candidates.json
```

`candidates.json` 关键字段：

- `review_status`：固定为 `PENDING_HUMAN_REVIEW`——产物只是待审草稿，不是定稿。
- `subject` / `language` / `paragraphs` / `requested_candidates` / `successful_candidates`：请求与实际成功数。
- `candidates[]`：每条含 `candidate`（序号）、`script`（文案正文）、`duration_seconds`（该候选的 LLM 调用耗时，单位秒）。
- `failures[]`：失败候选及原因。
- `endpoint_host` / `mpt_version` / `mpt_commit` / `generated_at`：溯源信息。

### 挑选候选进入现有原创 brief 流程

1. 打开最新 `drafter_<时间戳>/candidates.json`，通读各 `candidates[].script`。
2. 人工挑选（可改写）一条，作为旁白文案的起点素材。
3. 按现有原创 brief 流程走后续环节——草稿器不替代 brief，也不触发任何渲染任务。
4. 未选中的候选留在原目录即可，无需删除；`PENDING_HUMAN_REVIEW` 状态由人工审阅环节消化。

### 单元测试

```bash
python -m pytest tests/phase1_local/test_mpt_*.py -q
```

覆盖 `tests/phase1_local/test_mpt_script_drafter.py`（5 项）与 `tests/phase1_local/test_mpt_configure.py`（3 项）。改动这两个脚本后必须先跑通再使用。

## 5. 安全边界

已做的加固与禁止事项：

- **密钥**：只允许存在 `external/MoneyPrinterTurbo/config.toml`；不进 Git、不进日志、不进聊天；不作为命令行参数传递。
- **whisper model_size**：已从 `large-v3`（约 3GB 运行时下载）固定为 `small`；**禁止**改回大模型，禁止任何未经批准的模型下载。
- **自动发布**：MPT 的 cross-post（TikTok/YouTube 自动发布）保持关闭；**禁止启用**。本仓库禁止自动发布抖音，同理禁止一切 MPT 自动发布通道。
- **成片链**：MPT 的 MoviePy 成片段**不使用**——草稿器以 `--stop-at script` 截断，只取文案；TTS、素材、字幕、成片全部走仓库既有链路（audio-subtitle-engine、remotion-layout-engine 等）。
- 不修改 MPT 上游代码与依赖；如确需修改，先走 `reports/change_requests/` 变更请求流程。

## 6. 故障排查

| 症状 | 可能原因 | 处理 |
| --- | --- | --- |
| 401 / 密钥无效 | 密钥错误、过期或未写入 | 用第 2 节方式重新输入密钥并 `--verify`；确认环境变量拼写（`MPT_LLM_API_KEY` / `MIMO_API_KEY`） |
| 请求超时 | 端点慢或网络问题 | 提高 `--timeout-seconds`（默认 120）；重试一次；仍失败则记录故障并停止，不做猜测性修改 |
| 全部候选失败 | 端点不可用、密钥失效或配额耗尽 | 先 `python scripts/phase1_mpt_configure.py --verify` 定位；查看 `candidates.json` 的 `failures[]`；当天可改用人工写稿，不阻塞主线 |
| `config.toml` 缺失 | 首次使用或文件被删 | 重跑第 2 节配置命令即可重建 |
| venv 缺失 | `external/MoneyPrinterTurbo/.venv` 被删 | 按 MPT 上游文档在 `external/MoneyPrinterTurbo/` 下重建 Python 3.12 venv 并安装其依赖；不自动下载任何模型 |

## 7. 回滚方式

配置层（不动代码）：

- 密钥轮换出错：用正确密钥重跑 `python scripts/phase1_mpt_configure.py --verify` 覆盖即可。
- 想彻底清除密钥：删除 `external/MoneyPrinterTurbo/config.toml`（gitignored，删了不影响 Git 仓库）。

代码层（脚本已入库）：

- 草稿器或配置脚本行为异常时，回退对应提交：`git log --oneline -- scripts/phase1_mpt_*.py` 找到引入提交（`666d6e3 feat(reference): add MoneyPrinterTurbo script drafter via MiMo`），用 `git revert` 生成回滚提交；回滚记录对应 `PHASE1-MPT-SCRIPT-DRAFTER-002` / `PHASE1-MPT-CONFIG-FINALIZE-003` 的偏离处理。

整体移除（极端情况）：

- 删除 `external/MoneyPrinterTurbo/` 目录（克隆本身被 gitignore 排除，删除不影响仓库完整性）。
- 清理 `dist/phase1_local/script_drafts/` 下的草稿产物。

任何验证偏离预期时立即回滚并停止，不做第二次猜测性修改。
