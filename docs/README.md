# 当前文档索引

Updated: 2026-11-07 · 本索引合并 main 整合（2026-10-24 唯一职责表）与 2026-11-07 功能归档。

| 文件 | 唯一职责 |
|---|---|
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | 用户目标、输入输出、需求与验收 |
| [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) | 当前技术路线和代码职责 |
| [PRODUCT_PHASES.md](PRODUCT_PHASES.md) | 阶段顺序、下一步与完成门槛 |
| [PROJECT_REVIEW.md](PROJECT_REVIEW.md) | 本轮整合、验证、阻塞与审核入口 |
| [MAINTENANCE.md](MAINTENANCE.md) | 清理边界和历史恢复 |
| [HISTORY_AND_DECISIONS.md](HISTORY_AND_DECISIONS.md) | 当前有效的重要决定 |
| [OPEN_SOURCE_SKILL_MATRIX.md](OPEN_SOURCE_SKILL_MATRIX.md) | 开源采用、版本、许可证 |
| [PINK_PIG_CURRENT_POLICY.md](PINK_PIG_CURRENT_POLICY.md) | 品牌角色与原始素材 |
| [REFERENCE_VIDEO_ANALYSIS.md](REFERENCE_VIDEO_ANALYSIS.md) | 参考视频权利与原创分析 |
| [REFERENCE_TOOL_MATRIX.md](REFERENCE_TOOL_MATRIX.md) | 参考工具能力边界 |
| [MONEYPRINTER_TURBO_SETUP.md](MONEYPRINTER_TURBO_SETUP.md) | 可选文案草稿适配配置 |

执行入口：[START_HERE_CODEX](../START_HERE_CODEX.md)、[当前交接](../handoff/codex/CURRENT_HANDOFF.md)、[Phase 1 收口](../runbook/11_PHASE1_COMPLETION.md)、[当前任务](../tasks/todo.md)、[MUST_RUN](../MUST_RUN.md)（每次提交前必须执行的检查清单与错误台账）。

事实冲突先看 PROJECT_STATUS.yaml、当前需求/架构、源码/Schema 与真实证据；本目录文档与历史方案冲突时，以当前文档为准。

## 当前事实优先级

1. `PROJECT_STATUS.yaml` — 当前阶段、已完成能力、已知缺口；
2. `docs/CURRENT_ARCHITECTURE.md` — 当前 Phase 1 技术架构与强制/可选链路；
3. `docs/PRODUCT_PHASES.md` — 产品阶段顺序与最终目标；
4. `handoff/codex/CURRENT_HANDOFF.md` — 当前交接；
5. `runbook/11_PHASE1_COMPLETION.md` — Phase 1 收口执行步骤；
6. 当前源码、Schema、测试与真实运行证据；
7. 历史归档（下节）仅用于解释"为什么走到这里"，不得覆盖上述事实。

## 历史归档

两层归档，都只作审计追溯，不作为当前执行入口：

- **`docs/archive/`（2026-11-07 功能归档）**：旧 `ARCHITECTURE.md`（被 CURRENT_ARCHITECTURE 取代）、`IMPLEMENTATION_PHASES.md`（被 PRODUCT_PHASES 取代）、`INSTALL_ORDER.md`、`SKILL_INTEGRATION_ARCHITECTURE.md`、`PINK_PIG_PHASE1_ARCHITECTURE.md`（含旧分辨率与旧 IP 资产假设，勿复制为当前政策）、`PINK_PIG_MVP_PLAN.md`、`PINK_PIG_VIDEO_FACTORY_DESIGN.md`、`PHASE1_REMOTE_AUDIT_20260906.md`。HISTORY_AND_DECISIONS.md 已升级为"当前有效的重要决定"留在主目录。
- **Git 标签 `archive/pre-cleanup-20261023`（main 整理快照，56e9165）**：清理前的完整文档/任务/经验状态。恢复示例：`git show archive/pre-cleanup-20261023:tasks/lessons.md`。单次 Change Request 的历史实施计划（原 `docs/superpowers/`）已删除，从 Git 提交历史（`0f3b5b9` 及更早）查找。

## 当前产品的几个易混点

### 分辨率不是全局固定值

- Douyin/知识短视频可使用 `1080×1920` 9:16；
- Reference/Jianying 编辑任务可按 brief 使用 `1920×1080` 16:9；
- Gate 应验证 Job 的 render profile，而不是把某一个分辨率硬编码成全局产品定义。

### Jianying 不是 Phase 1 Gate 的唯一渲染器

Phase 1 的强制产品结果是**可复现、可解码、本地可审阅的 MP4 + evidence package**。剪映是可选的人工编辑/可编辑交付后端；草稿失败不能否定已经合格的本地 MP4。

### Pink Pig 不是任意生成的 mascot

`Jovifei/ian-fenzhu-illustrations` 提供 style/persona/composition 规范，不等于用户最终原始角色资产包。当前只有 Jovi 明确 opt-in 且提供原始资产 receipt 时才能启用个人 IP；否则保持 mascot off。

### AI Director Provider 不是 Phase 1 的硬门

Provider-neutral Director 代码存在，历史真实 Codex CLI Provider 曾受本机 cache 问题阻塞。当前 Phase 1 可以使用确定性/本地已验证输入闭环完成产品验收；不要重新把 Provider cache 修复升级成主线门禁。

## 文档维护规则

需求写入 `PRODUCT_REQUIREMENTS.md`，当前实现写入 `CURRENT_ARCHITECTURE.md`，未来顺序写入 `PRODUCT_PHASES.md`，审核证据写入 `PROJECT_REVIEW.md`；当前状态只在 `handoff/codex/CURRENT_HANDOFF.md` 与 `tasks/todo.md` 维护，不重复创建阶段总结或"最新版"文档。文档被后续决策取代时移入 `docs/archive/` 并在本索引登记；纯残留物直接删除；归档文档只修链接、不改历史结论。完整协作与收尾流程见 [MAINTENANCE.md](MAINTENANCE.md)，提交纪律与错误台账见根目录 `MUST_RUN.md`。
