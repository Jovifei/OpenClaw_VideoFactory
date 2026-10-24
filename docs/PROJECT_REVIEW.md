# 主线审核与交付说明

Updated: 2026-10-24 · Phase 1 remains in_progress

## 用户目标

保留视频工厂，围绕 App、网页、原理图和硬件工程制作视频；后续可增加网页/App 操作入口。本轮任务是代码汇总、需求与技术路线对齐、过程文件精简。

## 分支整合

初始 main 为 f1d94e980526ab7d0a06faadf9c78596b09db565。本地 27 个功能分支，14 个未合入；origin 15 个功能分支，5 个未合入。去重为 14 个独有 SHA，归属五个末端线，独有提交并集 84。

| 合并末端（codex/ 前缀） | 原 SHA | 内容 |
|---|---|---|
| phase1-audio-closure-20260928 | 8ef828126892d30d541570f22b85742c94423478 | 音频、technical_cut、Flash/FreeRTOS 修复、CAN/I2C 与证据合同 |
| website-product-promo-revision-20260913 | ae49aad72c0dc3e0d08e9072c80b4b1a1775b8f9 | 网页产品演示模板、语音焦点与检查 |
| phase1-freertos-candidate005-20260927 | 1a3a56ace6e4f357c7d0170f50ee1040e9d5e66e | 额外候选记录和旁白截断失败结论 |
| phase1-flash-candidate-20260927 | fc3a978750ef5caa55bb013d0998f873acab4e78 | Flash 候选旁白失败记录 |
| phase1-davinci-feasibility-20261011 | 0f3b5b9c46a68009894a716c8800279e3a789875 | 可选 Resolve MCP 试验计划 |

早期分支通过祖先关系覆盖。任务/经验文档冲突保留有效内容后归纳；没有用旧运行代码覆盖新修复。

## 当前事实与缺口

- 主题/参考/产品演示、SQLite、旁白完整性、技术剪切、质量/人审框架已有实现；本轮对整合代码运行 bounded regression。
- 历史 Flash/FreeRTOS 截断候选保持 CHANGES_REQUIRED，不能因合并被标为合格。
- I2C 最近证据记录服务 AUTH 失败且无另一批准凭证来源，本轮不重试 provider；Candidate003 已终止，Candidate004/M6 受门禁约束。
- CAN/live topic、各主题最终媒体与精确 SHA 人审、统一 Prereview、Lifecycle 最终绑定、Manifest/Boundary/Gate 未闭合。
- DaVinci 最近只有 MCP 环境准备记录；本机 Resolve 连接、剪辑、导出 NOT_RUN/未证明。
- 网页/App 操作入口与通用工程内容模板是后续规划；Phase 1 仍为 in_progress。

## 清理与恢复

完整合并并纳入原工作区文档增量的清理前快照：56e9165580332542046e65be64e05fc3b59fe9aa，标签 [archive/pre-cleanup-20261023](https://github.com/Jovifei/OpenClaw_VideoFactory/tree/archive/pre-cleanup-20261023)。

本轮删除 273 份旧计划、提示、交接、重复状态/评审摘要和被取代架构；有效结论写回需求/架构/路线/交接/经验。保留代码/测试/机器证据引用材料、Phase 1 JSON、来源、权利、授权、许可证。不删除 Job、媒体、数据库、模型或其他工作区。

原 E:\project\OpenClaw_VideoFactory 的三份既存未提交文档保持原状，其增量已在归档保存并提炼。干净整合工作区：E:\project\worktrees\OpenClaw_VideoFactory\main-consolidation-20261023。

## 本轮验证与发布

本轮实际结果：
- Python 声明范围：643 passed、1 skipped、2 deselected、4 subtests passed。范围为 tests/phase1_local、phase1_acceptance、video、reference、director、openmontage、product-demo，加包 prereview 测试与历史必需报告存在性单项。
- 两个 deselected 是旧样片报告的绝对输出路径身份校验；已在原工作区实际路径独立运行，2 passed。23 个旧样片/报告复制到测试工作区时逐文件 SHA 校验，仅为 inherited 夹具，不能证明本轮重新渲染。
- Node：70 passed；包含产品输入、渲染入口、审阅派生产物和 review-still 合同。TypeScript typecheck 与 Remotion contracts 均通过。
- 最初的网页测试夹具落后于语音 cue/580px 布局改造：修正夹具、增加缺失 cue/失真拒绝行为覆盖，删除过时源码字符串断言；运行代码校验规则未放宽。
- 历史 P0 全套控制源码检查依赖外部 OpenClaw 安装文件，本轮环境不具备；该探索失败日志保留，不列入 Phase 1 已通过范围。
- 新工作区依赖复用既有包；缺失的已锁定 layout-utils 4.0.500 从 npm 官方 registry 下载至 E:/Claude_allow/Download，隔离到 E:/AI_Tools/Other/VideoFactoryVerification，不改原目录依赖和锁文件。

当前文档链接、canonical 路径、包清单与 1,509 项 checksum 已通过；初始 27 个本地和 15 个远端功能分支头全部为整合提交的祖先。清理前受跟踪文件 1,776 个，清理后 1,510 个，删除 273 份历史文件并新增 7 份当前文档/范围记录。Git 版本对应本交付文件的提交；最终远端精确 SHA 记录在实际推送回执中。日志保存在本工作区 ignored reports/consolidation-*。没有运行产品 Formal Gate、新 provider 请求或新的候选媒体生产。

## 发布与本地工作区

main 与 archive/pre-cleanup-20261023 已成功推送到 GitHub。该归档保存清理前全部历史；main 保留当前精简文档和完整实现。原工作区 dirty patch 已逐字节验证未变。整合工作区切换至 main 供审核，最终 SHA 以 GitHub main 和本文件对应提交为准。

GitHub 直连曾超时；使用本机已运行的网络通道完成本次 Git 请求，没有写入全局 Git 或系统网络配置。

## Jovi 审核顺序

1. [需求](PRODUCT_REQUIREMENTS.md)：视频工厂与工程内容范围。
2. [架构](CURRENT_ARCHITECTURE.md)：单一主链、音画合同、可选后端。
3. [路线](PRODUCT_PHASES.md)：Phase 1 收口优先，飞书/网页/App 分阶段进入。
4. 运行代码：音频完整性、technical_cut、网页模板例外的适用范围。

候选视频的人审须单独绑定真实媒体，不因本轮合并自动批准。Hub 本轮 revision 读取返回 WinError 10061，未成功上报；按约定保留本地记录并停止自动重试。
