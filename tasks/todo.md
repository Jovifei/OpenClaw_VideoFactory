# 当前任务与下一步

Updated: 2026-10-24

## REPO-CONSOLIDATION-20261023

Change Request: reports/change_requests/REPO-CONSOLIDATION-20261023.json。

- [x] 确认继续视频工厂，内容涵盖 App/网页/原理图/硬件。
- [x] Fetch 并核清初始 27 个本地、15 个远端功能分支。
- [x] 合并五条末端线，覆盖 14 个独有分支头与 84 个独有提交。
- [x] 保留原工作区文档增量，归档 archive/pre-cleanup-20261023。
- [x] 归纳需求、架构、路线、交接、经验；按依赖筛选旧记录。
- [x] 完成 273 份历史文件清理；Python 643 passed/1 skipped/2 deselected，原目录身份校验 2 passed，Node 70 passed，Remotion typecheck/contracts 通过。
- [x] 当前文档链接、1,509 个 checksum、27 个本地/15 个远端功能分支祖先覆盖已核验。
- [x] main 与 archive/pre-cleanup-20261023 已成功推送；完成 GitHub 回执核对，交给 Jovi 审核。

Review: 本轮不代表 Phase 1 通过。原工作区三份未提交文件保留。Hub revision 读取 WinError 10061，未成功上报并停止自动重试。实际结果写入 docs/PROJECT_REVIEW.md。

## Phase 1 后续（原阶段门禁继续适用）

## P1-CONSOLIDATION-AUDIT-CLOSURE-20261024 — IN PROGRESS

Audit base: `8b5c142f6c469503a3644e4eafd6d54d785c577a`。远端反馈是读取通道阻塞、未完成独立源码审核，尚无已证实代码缺陷。

- [x] 读取用户提供的完整审核，固定基线，记录原工作区 staged/unstaged patch 与三份文件原始字节 SHA。
- [ ] WP0：恢复既有连接，释放包含源码 SHA、blob ID、路径和行范围的原始审核证据。
- [ ] WP1：补齐 R01—R10 映射，核查分支合并、逐项清理、动态引用、测试与许可证。
- [ ] WP2：仅修复已复现缺陷，保存 RED/GREEN 和兼容回归；不据审核假设盲改。
- [ ] WP3：只读核对已有批准素材、完整台词、源/对齐音频与 cue，登记可用项和真实阻塞。
- [ ] WP4—WP5：输入与既有授权齐全才生成新候选；人工视听、Prereview 和 Gate 均按原门禁。
- [ ] WP6：测试、原工作区保护复核、推送精确修复 SHA，释放执行证据并交回远端审核。

Review: 独立审核未完成；连接修复与本地离线源码审查并行。I2C 凭证、Candidate004/M6、模型/资源、人审及阶段提升边界保持原样。

## 待闭合产品项

- [ ] Flash/FreeRTOS 源对齐音频质量人审，再各生成一个批准的新候选；旧截断候选保持失败。
- [ ] I2C 等待有效批准凭证/方案决定，不重试 Candidate003，不自动创建 Candidate004。
- [ ] I2C 与不同 live topic 的同合同媒体、人审和 Prereview。
- [ ] 核对/绑定既有 lifecycle hash/Schema，准备 Manifest/Boundary/独立审计。
- [ ] 前置齐全且获授权后 Formal Gate，真实通过后单独更新 PROJECT_STATUS。
- [ ] 可选 DaVinci：官网下载/安装后，验证真实版本、桥接、隔离剪辑、导出；MCP 准备不是可用性证明。

历史详情：git show archive/pre-cleanup-20261023:tasks/todo.md。后续只维护当前清单和权威结论。
