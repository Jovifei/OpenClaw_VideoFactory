# Documentation Index — current truth first

本目录保存**当前产品文档**（按功能分组）与**历史归档**（`archive/`）。新 Agent 不得按文件修改时间或旧 P0/P1/P2 标签自行推断当前路线。

## 1. 当前事实优先级

发生冲突时按以下顺序判断：

1. `PROJECT_STATUS.yaml` — 当前阶段、已完成能力、已知缺口；
2. `docs/CURRENT_ARCHITECTURE.md` — 当前 Phase 1 技术架构与强制/可选链路；
3. `docs/PRODUCT_PHASES.md` — 产品阶段顺序与最终目标；
4. `handoff/codex/PROJECT_HANDOFF_20260905.md` — 当前分支深度交接、经验和下一步；
5. `runbook/11_PHASE1_COMPLETION.md` — Phase 1 收口执行步骤；
6. 当前源码、Schema、测试与真实运行证据；
7. 历史归档（`docs/archive/`）仅用于解释"为什么走到这里"，不得覆盖上述事实。

根目录 `START_HERE_CODEX.md` 是新 Codex/Agent 的第一入口；`MUST_RUN.md` 是每次提交前必须执行的检查清单与错误台账。

## 2. 活跃文档（按功能分组）

### 产品与阶段

| 文件 | 用途 |
|---|---|
| `PRODUCT_PHASES.md` | Phase 1 本地工厂 → Phase 2 飞书 → 后续增强（Canonical） |
| `PINK_PIG_CURRENT_POLICY.md` | 小粉飞猪当前资产与启用规则（Canonical） |

### 架构

| 文件 | 用途 |
|---|---|
| `CURRENT_ARCHITECTURE.md` | Topic/Reference → Script/Storyboard → Visual/Audio → MP4 → Review 的当前架构（Canonical） |

### 参考视频链

| 文件 | 用途 |
|---|---|
| `REFERENCE_VIDEO_ANALYSIS.md` | Phase 1 参考视频基础分析与 Phase 4 高级分析边界（Canonical） |
| `REFERENCE_TOOL_MATRIX.md` | 参考视频工具的采用状态（Canonical） |

### 安全

| 文件 | 用途 |
|---|---|
| `SECURITY.md` | 安全基线 |
| `SECURE_INSTALL_GUIDE.md` | 第三方 Skill 安装安全规则 |

### 外部集成

| 文件 | 用途 |
|---|---|
| `MONEYPRINTER_TURBO_SETUP.md` | 关键词 → 候选文案草稿器（MiMo v2.5）设置与密钥轮换 |
| `FEISHU_LARK_CLI_INTEGRATION.md` | 飞书 / lark-cli 集成（**Phase 2 专属**，Phase 1 不执行） |
| `OPEN_SOURCE_SKILL_MATRIX.md` | 已借鉴/采用/拒绝的开源项目与许可证边界（Canonical） |

## 3. 历史归档 `archive/`

以下文档是已完成时期的设计快照与决策记录，**只作审计追溯，不作为当前执行入口**；与第 1 节的当前文档冲突时，以当前文档为准：

| 文件 | 历史内容 |
|---|---|
| `ARCHITECTURE.md` | 2026-07 旧架构（被 `CURRENT_ARCHITECTURE.md` 取代） |
| `IMPLEMENTATION_PHASES.md` | 旧实施阶段定义（被 `PRODUCT_PHASES.md` 取代） |
| `INSTALL_ORDER.md` | 旧推荐安装顺序 |
| `SKILL_INTEGRATION_ARCHITECTURE.md` | Skill 集成架构 V2 |
| `HISTORY_AND_DECISIONS.md` | 2026-09 前的历史与决策日志 |
| `PINK_PIG_PHASE1_ARCHITECTURE.md` | Phase 1/1.5/Director 长篇历史设计（含旧分辨率与旧 IP 资产假设） |
| `PINK_PIG_MVP_PLAN.md` / `PINK_PIG_VIDEO_FACTORY_DESIGN.md` | 小粉飞猪早期 MVP 计划与设计 |
| `PHASE1_REMOTE_AUDIT_20260906.md` | 2026-09-06 远端审核与开源吸收记录 |

单次 Change Request 的历史实施计划（原 `docs/superpowers/`）已于 2026-11-07 清理删除；如需追溯，从 Git 历史查找（提交前的最后跟踪版本在 `0f3b5b9` 及更早）。

## 4. 当前产品的几个易混点

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

## 5. 当前完成定义

"实现了一个子链"与"Phase 1 完成"是两件事。

Phase 1 只有在以下全部成立时才完成：

- Modbus、Flash/Watchdog、FreeRTOS 固定主题取得统一 Prereview 证据；
- 至少一条用户有权处理的真实参考视频完成原创重构和人工原创性审核（若 Gate manifest 仍要求）；
- cancel / retry / restart recovery / encoder fallback 机器证据齐全；
- Jovi 对需要进入 Gate 的最终候选完成结构化人工审核；
- Acceptance Manifest、Boundary Audit、fresh bounded regression 完整；
- 独立只读审核通过；
- `phase1_gate.py` 正式运行并产生 `PHASE1_READY.json`；
- Gate 通过后才能把 `PROJECT_STATUS.yaml` 更新为 passed，并启动 Phase 2。

## 6. 文档维护规则（2026-11-07 起）

- 新增文档必须进入本索引的功能分组，并在文首标注更新日期；
- 文档被后续决策取代时，移入 `archive/` 并在本索引登记，不直接删除（Git 历史保留更完整的版本链）；
- 纯残留物（测试文件、旧交付压缩包、过期清单）直接删除，不归档；
- 归档文档的失效链接允许修复路径，但不得改写其历史结论。
