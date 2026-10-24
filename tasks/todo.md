# 当前任务与下一步

Updated: 2026-10-24

## P1-CONSOLIDATION-AUDIT-CLOSURE-20261024

基线 8b5c142；最终执行源码 10679a1；[PR #2](https://github.com/Jovifei/OpenClaw_VideoFactory/pull/2)。普通修复保持 SQLite/Remotion/FFmpeg 和 Phase 1 in_progress。

- [x] 读取远端完整反馈，固定 Git 对象/祖先，保护原工作区三份 dirty 文件、原始字节与 patch。
- [x] WP0 本地取证：189 份准确 SHA/blob/行范围源码快照；现有连接输出29—44可读、未截断。
- [ ] WP0 远端访问与独立审核：TLS EOF，workspace_info -32603，仍 NOT_VERIFIED。
  - 固定目标转发及官方新版独立客户端的有界测试均未建立对外连接；测试进程已停止，既有连接/账号/域名未改，远端复审仍阻塞。
  - 已在现有 Project 审核聊天发送一次 GitHub 源码复审请求，页面显示正在回应；PENDING_REMOTE_REVIEW，不重复发送，不视为本地连接恢复。
- [x] WP1：R01—R10 原文映射、合并/清理依赖、retention dry-run、来源/许可证、测试范围复核。
- [x] WP2：十项已复现问题修复；RED/GREEN、并发/旧 attempt/进程终止/回滚/migration 回归。
- [x] Python 684 passed、1 skipped、2 deselected、4 subtests passed；旧绝对路径身份另验2 passed。
- [x] Node81、类型/合同通过；冻结锁文件干净安装复验，JS/锁文件与最终源码相同。
- [x] WP3：两条现有真实 v7 音频只读完整性和身份/实测时长重验。
- [ ] WP3 人审：Jovi 选择稍后试听，先完成代码审查交付；不得代签或启动对应新候选。
- [ ] WP4—WP5：批准输入/人审/资源齐全才生成新候选；资格链与 Formal Gate 继续按门禁。
- [x] WP6 源码修复分支已推送、草稿 PR #2 已创建并附到本聊天。
- [x] WP6 交付文档、机器证据与 checksum 完成本地验证；GitHub 实际交付以 PR #2 和推送回执为准。远端独立复核仍待通道恢复。

Review: 机器审计见 reports/phase1/consolidation_audit_20261024.json。无真实媒体/Job/DB 清理，无 provider 重试或新 TTS，无真实人审批准和阶段提升。Hub WinError10061，未上报并停止自动重试。

## P1-ATTEMPT-RECOVERY-20261024

- [x] 临时夹具复现：旧 subject worker 覆盖新规划、QUALITY_CHECK 重试伪待审；延伸复现 VOICE/CAPTIONS 同类恢复缺陷。
- [x] 修复每次规划的六份输入/输出快照隔离、绑定交付消费者；保留旧任务兼容。
- [x] 修复本地 topic/reference 质量检查中断及 subject 已完成规划检查点恢复，不提前待审；损坏规划明确失败并允许显式重建。
- [x] focused 41 passed / 固定源码 bounded regression 684 passed、原工作区保护、清单、源码 10679a1 推送至 PR #2。

本包只修复生命周期；不运行 provider、TTS、生产候选或 Gate。Review: RED 3+2+2 项准确失败；focused 41 passed；六份规划文件绑定 hash 与 Job 身份，增量代码审阅无新增阻塞；固定源码 10679a1 完整回归 684 passed、1 skipped、2 deselected、4 subtests passed；远端独立复核仍待连接恢复。

## 保留的产品缺口

- Flash/FreeRTOS 历史截断候选保持失败；源音频人审恢复后才生成新 lineage。
- I2C 批准凭证/方案决定仍缺，Candidate003 不重试，M6/Candidate004 不自动启动。
- CAN/live topic、最终媒体人审、统一 Prereview 与 lifecycle 绑定、Manifest/Boundary/独立审计未闭合。
- DaVinci 属可选支线；官网安装、本机桥接/剪辑/导出尚未通过真实验证。
- Phase 2 飞书/Cron、后续网页/App 界面按阶段授权。

## 已交付的整合

8b5c142 已将五条末端线、84 个独有提交整入 main；273 份旧过程文档归档精简。旧任务与经验从 archive/pre-cleanup-20261023 按需读取。
