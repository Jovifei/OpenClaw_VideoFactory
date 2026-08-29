# MoneyPrinterTurbo 文案草稿器接入（选项 A，2026-08-29）

> Change Request: `PHASE1-MPT-SCRIPT-DRAFTER-002`（Jovi 批准）
> 结论：**已实现并实测跑通——一个主题关键词 → MiMo v2.5 → N 个候选旁白文案 JSON，供人工挑选后进入现有原创 brief 流程。**

## 交付内容

1. **适配器** `scripts/phase1_mpt_script_drafter.py`：对 vendored MoneyPrinterTurbo（v1.3.5，commit `eb8c237`，MIT，位于 gitignored `external/`）的 `cli.py --stop-at script` 做子进程封装：
   - 参数：`--subject`、`--candidates`（1–10）、`--paragraphs`、`--language`、`--timeout-seconds`（默认 120s，超时终止并记录）；
   - 输出：`dist/phase1_local/script_drafts/drafter_<时间戳>/candidates.json`，含全部候选、失败明细、`review_status=PENDING_HUMAN_REVIEW`；
   - 失败关闭：全部候选失败时退出码 1，不产出"成功"假象。
2. **LLM 提供商**：`token-plan-cn.xiaomimimo.com` 的 OpenAI 兼容接口（`/v1/chat/completions`），模型 `mimo-v2.5`。密钥取自本机 `MIMO_API_KEY` 环境变量，只写入 gitignored 的 `external/MoneyPrinterTurbo/config.toml`（已用 `git check-ignore` 验证不入库），从未回显、未进日志。
3. **配置加固**：MPT 的 whisper `model_size` 由默认 `large-v3`（运行时约 3GB 下载）改为 `small`；本次全程无模型下载。
4. **单测** `tests/phase1_local/test_mpt_script_drafter.py`：5 项通过（JSON 解析、候选落盘、全超时失败关闭、输入校验）。

## 真实运行证据

| 检查 | 结果 |
|---|---|
| 端点认证探测 | 无密钥 401 → 有密钥 OpenAI 格式 200（Anthropic 格式同样 200，未采用） |
| MPT 直连生成（看门狗主题） | 通过，两段中文旁白，任务 `f9ee0f8e…`，约 19s |
| 适配器真实冒烟（"I2C总线为什么要上拉电阻"，2 候选） | 2/2 成功（13.7s、10.7s），文案技术正确（开漏/上拉逻辑） |
| 单测 | `5 passed` |

详细证据：`reports/phase1/mpt_script_drafter_evidence_20260829.json`。

## 使用方式

```powershell
python scripts\phase1_mpt_script_drafter.py --subject "主题关键词" --candidates 3
# 产物：dist\phase1_local\script_drafts\drafter_<ts>\candidates.json
```

挑选修改某一候选后，把它作为原创 brief 的旁白输入，走既有 `run_local_brief() → run_job() → build_review_package()` 链；草稿本身不直接成片。

## 边界

- 不触碰 Remotion/剪映/FFmpeg 渲染链；不新增第二渲染器/编辑后端/TTS 后端；
- 无飞书、Cron、自动发布、模型下载；
- `PROJECT_STATUS.yaml` 与 Phase 1 人工审阅门禁不变；
- 回滚：删除适配器、测试、`external/MoneyPrinterTurbo`、草稿输出并还原 `.gitignore` 追加项即可。
