# 03 — Skill与外部仓库

`skills/`已位于workspace根，运行`openclaw skills check`即可，不重复安装本地Skill。

第三方仓库统一放`external/`，先检查LICENSE、README、SKILL、安装脚本和锁文件，写`reports/external/<repo>-review.md`，记录commit、许可证、权限、允许/禁止用途和回滚。

## 小粉飞猪

```powershell
git clone https://github.com/Jovifei/ian-fenzhu-illustrations .\external\ian-fenzhu-illustrations
git -C .\external\ian-fenzhu-illustrations rev-parse HEAD
```

审查后可安装给Codex，或由本地`pink-pig-mascot-director`读取规则。保留MIT/NOTICE。角色：低饱和雾粉、小鼻、小翅膀、认真冷静、承担拆装测修动作，不是贴纸。

## Remotion

安装官方Skill；模板开发前必须读取。先固定模板和设计tokens，不每条临时换风格。

## video-podcast-maker

只吸收研究、脚本、TTS/timing、组件和验证，不接管任务状态。

## comfyui-mcp

只连`127.0.0.1:8188`。无人值守禁装节点/模型，只跑`comfyui/workflows/approved/`，输出限制在job目录，OOM回退。

## 剪映

P5在CapCut Mate和jianying-editor-skill中二选一，同一任务不双后端。
