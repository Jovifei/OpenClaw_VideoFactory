# 01 — 包体与机器预检

## A. 放置目录

```powershell
Set-Location E:\project\OpenClaw_VideoFactory
Set-ExecutionPolicy -Scope Process Bypass
Test-Path .\START_HERE_CODEX.md
Test-Path .\skills
Test-Path .\scripts
Test-Path .\config
```

全部必须为True。

## B. 项目本地Python bootstrap

```powershell
powershell -File .\scripts\00_bootstrap_python.ps1
powershell -File .\scripts\00_bootstrap_python.ps1 -Apply
```

只创建 `.venv` 并安装 `requirements-bootstrap.txt`。

## C. 包体检查

```powershell
powershell -File .\scripts\00_package_check.ps1
```

预期：退出0；生成`reports/package_check.json`和`.md`；无密钥；无嵌套`工作区/skills`；14个本地Skill可解析；`factory.py`为fail-closed；SHA清单一致。

失败时重新解压原ZIP，不得修改清单掩盖问题。

## D. Git

```powershell
git status
```

未初始化：

```powershell
git init
git checkout -b phase/p0-preflight
git add .
git commit -m "chore: import VideoFactory V2.4 handoff"
```

已有仓库时保留历史并创建新分支。

## E. 机器预检

```powershell
powershell -File .\scripts\01_machine_preflight.ps1
```

检查E盘空间、Node、Python、OpenClaw、Codex、FFmpeg、NVENC、NVIDIA、ComfyUI和剪映候选。预检只记录，不安装。

## F. 阻塞

立即停止：目录不对、E盘可用空间明显不足、GPU/驱动不可识别、OpenClaw配置损坏、密钥进入Git、需要管理员权限而用户未同意。

## G. Codex输出

```text
reports/PREFLIGHT_REPORT.md
reports/DECISION_GAPS.md
reports/IMPLEMENTATION_PLAN_LOCKED.md
config/versions.lock.yaml
```

只写真正无法自动发现的缺口，不重复询问已确认条件。
