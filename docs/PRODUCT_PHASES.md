# 产品路线与执行顺序

Updated: 2026-10-24

## Phase 1：本地视频工厂（当前）

目标：主题或授权参考视频能产出原创、完整、可恢复、可审核的本地 MP4。工程内容涵盖 App、网页、原理图、嵌入式与硬件，继续复用同一生产链。

| 顺序 | 工作包 | 执行前提 | 完成判据 |
|---|---|---|---|
| 1 | 主线与文档整合 | 用户已授权 | 独有实现进入 main；需求、路线、验证、历史归档清楚 |
| 2 | 事实/音频准备 | 核对当前输入与审批 | 各主题 source-aligned 台词/音频证据及所需音频质量人审 |
| 3 | 主题候选收口 | 每次新候选有执行授权、依赖合格 | Flash、FreeRTOS、I2C、不同 live topic 的最终媒体、质量包、hash-bound 人审 |
| 4 | 生命周期与单条资格 | 既有证据优先复用 | cancel/retry/restart/fallback hash/Schema 核对，Prereview ready |
| 5 | 整阶段资格 | 必须的人审全部 approved | Acceptance Manifest、Boundary Audit、独立审计、bounded regression |
| 6 | Formal Gate | 所有前置闭合且获授权 | 真实生成 PHASE1_READY，再单独更新阶段状态 |

当前依赖：最近 I2C 记录为 I2C_BLOCKED:MPT_APPROVED_CREDENTIAL_UNAVAILABLE。新的批准凭证来源或方案决定前，冻结 provider 重试、M6、Candidate004。本轮清理不会解除门禁。

topic_only_v1 与 legacy_topic_reference_v1 同时保留；实际提供参考任务时验证完整 rights/analysis/originality 合同。阶段实现与验收不能混同。

## Phase 2：飞书与受控自动化

前提：Phase 1 正式 passed，再获阶段授权。

OpenClaw 官方飞书入站 → 候选卡/选择 → 幂等任务 → 取消/恢复 → 审阅包受控交付。先完成无调度验证，再启用 Cron。08:30 候选、12:00 合格兜底按来源、去重、配额/fallback 执行，每日最多一条；附件两消息分析协议保持强制。

完成条件：真实入站/交付、重复消息和恢复测试、固定目标白名单、质量与运行证据合格。最终抖音仍由 Jovi 人工发布。

## 后续：操作入口与工程模板

在合格生产链上分阶段设计和验收：

- 网页操作台：任务、素材/权利、状态、取消/重试、MP4 预览与精确 SHA 审核。
- App 入口：复用服务接口，先由 Jovi 确认平台和离线需求，再选框架。
- 工程模板：真实 App/网页演示、原理图逐层讲解、信号/代码/实验对照、硬件实拍；每类有真实材料和技术审阅。
- 增强能力：ComfyUI、WhisperX、可编辑工程、DaVinci，先独立兼容性验证再扩大采用。

这些是未来能力，不代表已有操作台、App、自动 EDA 或硬件生产能力。具体顺序在阶段启动时确认。

## 长期协作

远端 ChatGPT 在同 Project 规划、审核技术方向和下阶段方案；本地 Codex 在授权范围执行、测试、推送精确 SHA 与交接证据。有分歧先用源码/试验证据讨论，再提出需要 Jovi 决定的选项。Git 合并、聊天认可或测试通过不自动提升阶段。
