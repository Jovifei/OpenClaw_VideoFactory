# Phase 1 收口步骤

Updated: 2026-10-24

本 Runbook 适用于当前本地视频工厂。只执行已有授权与依赖满足的工作包；本轮主线合并/文档清理不授权运行 Formal Gate。

## 1. 确认状态

先读 START_HERE_CODEX、PROJECT_STATUS、当前需求/架构/路线与 CURRENT_HANDOFF。核对当前工作区、Git SHA、dirty 文件和 Change Request，不能据历史任务编号或测试数推断产品通过。

```powershell
git fetch origin
git status --short --untracked-files=all
git rev-parse HEAD
git rev-parse origin/main
python scripts/factory.py phase1 --help
```

当前 Phase 1 为 in_progress；主链 SQLite + Remotion/FFmpeg，不依赖生产飞书/Cron。

## 2. 音频、事实与主题候选

核对事实来源/素材权利、source/aligned PCM、完整台词、实际 cue 和技术图。历史 Flash/FreeRTOS 截断候选保持失败，新候选须先满足音频质量审核与执行授权。不得通过裁尾、改状态或复用过期人审来满足时长。

topic_only_v1 要求 Flash/watchdog、FreeRTOS、I2C、不同 live topic；每条最终 MP4、质量包、结构化人审与 Prereview 绑定精确 SHA。

最近 I2C 为 I2C_BLOCKED:MPT_APPROVED_CREDENTIAL_UNAVAILABLE。没有新的批准凭证/方案决定，不重试 provider，不复活 Candidate003，不创建 Candidate004/M6。

参考模式保留 rights receipt、入库 SHA、analysis、original brief、difference report 和真实人工原创性审核。普通技术视频默认不启用个人角色；opt-in 时须原始资产 receipt。

## 3. 生命周期与 bounded regression

先 revalidate 已有 cancel/failed-retry/restart/fallback 的 hash、Schema、版本和实际语义；只有具体不兼容才补测。报告成功不代表最终媒体合格。

明确列出本轮测试套件、解释器和 Node 环境，保留失败日志。tests/video 中部分旧媒体测试要求 dist/story_demo* 和示例 MP4；应生成真实测试产物，或以 hash receipt 提供既有测试样片并标注 inherited，缺失时不能伪造通过。既有样片测试不等于本轮重新渲染。

当前代码回归、Node 产品合同、Remotion typecheck/contract、文档引用/包 checksum 分别记录。不要运行不相干的全仓 P0/vendor 环境测试并拿其计数替代 Phase 1 验收。

## 4. 单任务 Prereview

审核目标必须是实际最终媒体，不能用旧图、无声预览或另一个候选替换。用对应真实文件调用：

```powershell
python scripts/phase1_acceptance.py --database PATH_TO_DATABASE --job-id JOB_ID --review PATH_TO_REVIEW --output PATH_TO_PREREVIEW
```

先通过 --help 确认当前参数；上述大写项是待替换的真实路径/ID。必须解析输出的 ready 及质量/身份字段，不只看命令退出码。

## 5. 整阶段资格与 Formal Gate

前置：所需主题的人审明确 approved、Prereview ready、Lifecycle 齐全，Acceptance Manifest、Boundary Audit、fresh bounded regression 和独立只读审核都成立。任何 BLOCKED/NOT_RUN/CHANGES_REQUIRED 不得被写成 PASS。

只在前置齐全且获授权后，使用真实 manifest 执行一次：

```powershell
python scripts/phase1_gate.py --manifest PATH_TO_ACCEPTANCE_MANIFEST --output-dir PATH_TO_GATE_OUTPUT
```

真实生成 PHASE1_READY 后才单独更新 PROJECT_STATUS。失败保留证据，不猜测修改后连续运行 Gate。Phase 2 必须另外取得启动授权。

## 6. 交接

推送经过验证的精确 Git SHA，把当前目标、完成、阻塞、关键文件和下一步交给远端 GPT/Jovi 审核。远端讨论技术分歧并制定下一阶段计划；本地在已授权范围执行。历史逐轮记录从 archive/pre-cleanup-20261023 查回。
