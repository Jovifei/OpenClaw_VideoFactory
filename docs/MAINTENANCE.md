# 仓库维护与历史恢复

Updated: 2026-10-25

## 维护当前知识

需求、架构、路线、审核各维护一份权威文档。任务只维护 tasks/todo.md；交接只写目标、已完成、阻塞、关键路径和下一步。有效工程经验写入 tasks/lessons.md，避免逐轮追加完整复盘和多份“最新状态”。

## 协作与收尾流程

当前约束：本轮只整理项目与流程，交付即停止。以下开发流程是以后重新授权时的工作方法，不自动启动。

| 步骤 | 负责人 | 必须留下的结果 |
|---|---|---|
| 1. 确认范围 | Jovi / 本地 Codex | 本轮目标、允许修改、停止点；读取 START_HERE、PROJECT_STATUS、当前需求和交接 |
| 2. 固定版本 | 本地 Codex | main / 工作分支完整 SHA、dirty 状态和保护记录；原工作区有修改时使用独立工作区 |
| 3. 规划或审核 | 同 Project 的远端 ChatGPT | 按准确 SHA 读取源码、需求和证据；列明已验证、静态发现、未验证与路线分歧 |
| 4. 授权内执行 | 本地 Codex；远端具备工具时亦可执行 | 仅已授权变更、真实测试、提交 SHA、交接文件；接收远端提交先核对 diff 和版本 |
| 5. 交付与结束 | 本地 Codex / Jovi | 分支、PR、测试与产物身份、待处理项、回退入口；更新唯一交接后停止 |

只有 Jovi 明确授权持续开发时，才进行“执行 → 测试 → 推送 → 远端审核”的循环。审核建议、路线图或旧聊天不构成新授权；收到停止指令就登记剩余项并结束，不自动修复、生成视频、反复等审核或进入下一阶段。

每次交接分别记录审核基线、执行源码、测试源码、交付提交；媒体产生时另记媒体 SHA 与人审，文档提交不能改写既有测试/媒体来源。远端不能读取时标 NOT_VERIFIED；静态审核不是本机运行或人审。PR 为草稿或有未闭合发现时保留待审，不合并冒充完成。

需求写入 PRODUCT_REQUIREMENTS，当前实现写入 CURRENT_ARCHITECTURE，未来顺序写入 PRODUCT_PHASES，审核证据写入 PROJECT_REVIEW，当前状态只在 CURRENT_HANDOFF / tasks/todo 维护。大方向改变由 Jovi 决定；不重复创建阶段总结和“最新版”文档。

## 历史恢复

完整合并后、清理前的快照为 `56e9165580332542046e65be64e05fc3b59fe9aa`，标签为 `archive/pre-cleanup-20261023`。Git 历史未改写，例如：

```powershell
git show archive/pre-cleanup-20261023:tasks/todo.md
git show archive/pre-cleanup-20261023:handoff/codex/PHASE1_AUDIO_AND_CLOSURE_HANDOFF_20260928.md
git log --all -- path/to/file
```

## 清理边界

旧计划、Agent 提示、过时交接、重复状态和审核摘要，在有效决定与未完成项归纳后移出主线。先检查代码、测试、Schema、脚本、机器报告和校验清单引用，再删除确切项目内文件。

必须保留：源码与测试、配置模板、运行技能、素材权利与来源、哈希/Gate/授权证据、兼容夹具、第三方 provenance 和许可证。日期早不等于无用，reports/ 中仍有测试直接读取的文件。

本轮不清理用户媒体、Job、SQLite、模型、环境、其他工作区或未提交工作。inventory.py 会利用报告引用形成产物保留理由；报告精简后不得据此自动删除媒体或任务。

机器证据按合同保留，临时日志留 ignored runtime；文件变动后同步刷新 FILE_MANIFEST.txt 与 SHA256SUMS.txt。旧文档的历史原路径从归档标签查回。
