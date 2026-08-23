# 03 — Skill与外部仓库

`skills/`已位于workspace根，运行`openclaw skills check`即可，不重复安装本地Skill。

端到端视频任务先读取 `skills/video-production-chain/SKILL.md`。它只负责
串联本地 Skill 和交接合同，不创建第二套 renderer。

第三方仓库统一放`external/`，先检查LICENSE、README、SKILL、安装脚本和锁文件，写`reports/external/<repo>-review.md`，记录commit、许可证、权限、允许/禁止用途和回滚。

## 小粉飞猪

```powershell
git clone https://github.com/Jovifei/ian-fenzhu-illustrations .\external\ian-fenzhu-illustrations
git -C .\external\ian-fenzhu-illustrations rev-parse HEAD
```

审查后可安装给Codex，或由本地`pink-pig-mascot-director`读取规则。保留MIT/NOTICE。角色：低饱和雾粉、小鼻、小翅膀、认真冷静、承担拆装测修动作，不是贴纸。

个人 IP 门禁：粉色飞猪不是默认角色。只有 Jovi 在当前 brief 中明确要求时才启用；启用时必须使用 Jovi 提供且 receipt 绑定的原始资产包。仓库自制 PNG/SVG、AI 临时图、上游样例 JPG 和上游风格仓库均不是 Jovi 原始 IP 的替代品。缺少原始资产路径时失败关闭。

## Remotion

安装官方Skill；模板开发前必须读取。先固定模板和设计tokens，不每条临时换风格。

## video-podcast-maker

只吸收研究、脚本、TTS/timing、组件和验证，不接管任务状态。

## comfyui-mcp

只连`127.0.0.1:8188`。无人值守禁装节点/模型，只跑`comfyui/workflows/approved/`，输出限制在job目录，OOM回退。

## 剪映

Jovi 视频固定选择已审核并锁定版本的 `jianying-editor-skill` 作为剪映
编辑后端，同一任务不启用 CapCut Mate 或 JianYing MCP 双后端。默认只
生成 E 盘新草稿，不自动导出、不控制鼠标键盘；人工在剪映中试听、检查
画面与唯一字幕轨后导出。

外部候选的处理边界：

- `Hommy-master/capcut-mate`（Apache-2.0）只做未来隔离适配器评估；
- `hey-jian-wei/jianying-mcp` 只做研究候选，未通过单独的许可证、版本、
  权限和恢复审计前不得进入生产链；
- `luoluoluo22/jianying-editor-skill`（MIT）是当前唯一启用的编辑后端，
  本项目通过 `jianying-draft-exporter` 调用其固定版本。
