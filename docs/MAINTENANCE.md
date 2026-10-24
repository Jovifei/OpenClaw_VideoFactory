# 仓库维护与历史恢复

Updated: 2026-10-24

## 维护当前知识

需求、架构、路线、审核各维护一份权威文档。任务只维护 tasks/todo.md；交接只写目标、已完成、阻塞、关键路径和下一步。有效工程经验写入 tasks/lessons.md，避免逐轮追加完整复盘和多份“最新状态”。

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
