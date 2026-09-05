# Documentation Index — current truth first

本目录同时保存**当前产品文档**与**历史设计快照**。新 Agent 不得按文件修改时间或旧 P0/P1/P2 标签自行推断当前路线。

## 1. 当前事实优先级

发生冲突时按以下顺序判断：

1. `PROJECT_STATUS.yaml` — 当前阶段、已完成能力、已知缺口；
2. `docs/CURRENT_ARCHITECTURE.md` — 当前 Phase 1 技术架构与强制/可选链路；
3. `docs/PRODUCT_PHASES.md` — 产品阶段顺序与最终目标；
4. `handoff/codex/PROJECT_HANDOFF_20260905.md` — 当前分支深度交接、经验和下一步；
5. `runbook/11_PHASE1_COMPLETION.md` — Phase 1 收口执行步骤；
6. 当前源码、Schema、测试与真实运行证据；
7. 历史设计/报告仅用于解释“为什么走到这里”，不得覆盖上述事实。

根目录 `START_HERE_CODEX.md` 是新 Codex/Agent 的第一入口。

## 2. 当前必读文档

| 文件 | 用途 | 当前性 |
|---|---|---|
| `CURRENT_ARCHITECTURE.md` | Topic/Reference → Script/Storyboard → Visual/Audio → MP4 → Review 的当前架构 | Canonical |
| `PRODUCT_PHASES.md` | Phase 1 本地工厂 → Phase 2 飞书 → 后续增强 | Canonical |
| `OPEN_SOURCE_SKILL_MATRIX.md` | 已借鉴/采用/拒绝的开源项目与许可证边界 | Canonical |
| `REFERENCE_VIDEO_ANALYSIS.md` | Phase 1 参考视频基础分析与 Phase 4 高级分析边界 | Canonical |
| `REFERENCE_TOOL_MATRIX.md` | 参考视频工具的采用状态 | Canonical |
| `PINK_PIG_CURRENT_POLICY.md` | 小粉飞猪当前资产与启用规则 | Canonical |

## 3. 历史快照，不作为当前执行入口

### `PINK_PIG_PHASE1_ARCHITECTURE.md`

这是 2026-08-09 起形成的长篇 Phase 1/1.5/Director 历史设计记录。它包含大量当时正确、现在已经被后续决策覆盖的细节，例如：

- 全局固定 1080×1920；
- 早期把仓库内自制 Pink Pig PNG/SVG 当作可直接生产使用的角色资产；
- `jsonschema` / PyYAML 环境快照；
- 当时的分支名、测试计数、Renderer 最小修改方案。

**保留它是为了审计历史，不应从中复制当前默认分辨率、IP 资产政策或阶段状态。** 当前对应内容以 `CURRENT_ARCHITECTURE.md`、`PROJECT_STATUS.yaml` 和 `PINK_PIG_CURRENT_POLICY.md` 为准。

### `docs/superpowers/plans/*` / `specs/*`

这些是单次 Change Request 的实施计划。计划完成后仍保留，但只说明该任务当时的目标，不能证明整个产品阶段通过。

### 历史 P0/Feishu 文档

仓库里的 P0/P1/P2 历史报告、Gateway/Binding/OAuth/Feishu 调试记录属于未来 Phase 2 的安全证据库。当前 Phase 1 不应重新执行它们，也不能因为它们未闭环而阻塞本地视频工厂。

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

“实现了一个子链”与“Phase 1 完成”是两件事。

Phase 1 只有在以下全部成立时才完成：

- Modbus、Flash/Watchdog、FreeRTOS 固定主题取得统一 Prereview 证据；
- 至少一条用户有权处理的真实参考视频完成原创重构和人工原创性审核（若 Gate manifest 仍要求）；
- cancel / retry / restart recovery / encoder fallback 机器证据齐全；
- Jovi 对需要进入 Gate 的最终候选完成结构化人工审核；
- Acceptance Manifest、Boundary Audit、fresh bounded regression 完整；
- 独立只读审核通过；
- `phase1_gate.py` 正式运行并产生 `PHASE1_READY.json`；
- Gate 通过后才能把 `PROJECT_STATUS.yaml` 更新为 passed，并启动 Phase 2。
