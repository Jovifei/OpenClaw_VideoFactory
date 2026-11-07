# MUST RUN — 提交检查清单与错误台账

> 本文件是**必须执行**的纪律文档：每次提交前过一遍第 1 节；遇到新的构建/运行错误时，先查第 2 节台账，解决后把新错误追加进台账。经验与教训的长期记录在 `tasks/lessons.md`（保留库），本文件只放"每次都要照做"的步骤和"反复出现"的错误。

更新：2026-11-07

## 1. 每次提交前必须执行的步骤

按顺序执行，任何一步失败先解决再继续：

```text
[1] git status --short
    确认改动只属于当前任务；无关的 dirty 文件不要带进本次提交。
    一次只修改一个类别（代码/文档/配置）；跨类别先拆分。
    涉及治理范围的改动先建 reports/change_requests/<ID>.json。

[2] 针对性检查（按改动面选择，不必全跑）
    文档改动   → 检查被移动/删除文件的引用是否已更新：
                 git grep -n "<旧文件名>" -- '*.md' '*.yaml' '*.json'
    Python 改动 → python -m pytest tests/phase1_local -q （或对应子目录）
    视频链改动  → python -m pytest tests/video -q
    MPT 草稿器  → python -m pytest tests/phase1_local/test_mpt_*.py -q
    渲染产物    → ffprobe 完整解码 + post-render gate（见 video-quality-gate）

[3] git add <明确列出的文件>   # 禁止裸 git add . ；reports/** 等被忽略目录的新证据
    文件需按 .gitignore 白名单惯例处理（见错误台账 E6）

[4] git commit -m "<type>(<scope>): <一句话>"
    type ∈ feat|fix|docs|test|chore|refactor|merge；scope 用领域词（reference/phase1/jianying/video…）

[5] git push origin <branch> && git log --oneline -1 origin/<branch>
    推送后核对远端指针已到新提交才算完成。

[6] 阶段性节点（不是每次）：
    - 重大阶段结束/计划变更/出现阻塞 → 按 AGENTS.md 的 hub reporting 规则发 bound_report；
    - 长会话（~120 工具轮次）→ 提醒 Jovi 开新会话，收尾写入 tasks/todo.md。
```

## 2. 错误台账（编译/运行错误 → 解决方案）

新增条目追加在表尾；重复出现的老错误不许再现场重推，直接按方案处理。

| 编号 | 错误现象 | 根因 | 解决方案 |
|---|---|---|---|
| E1 | LLM 探针 HTTP 200 但 `content` 为空、被判失败 | `mimo-v2.5` 是推理模型，`max_tokens` 太小全被思考消耗 | 探针给足 token（≥64）；判定接受 `content` **或** `reasoning_content`（见 `scripts/phase1_mpt_configure.py --verify`） |
| E2 | Git Bash 里 `cd external/xxx` 突然失败 | 工作目录在调用间持久，相对 `cd` 叠加错位 | 每条命令用绝对路径或 `git -C <repo>`；`cd` 前先 `pwd` 确认 |
| E3 | Windows Python `FileNotFoundError: '/e/...'` | Windows 原生 Python 不认 Git Bash 的 `/e/` 挂载路径 | Python 内部路径一律用 `E:/...` 风格；只有 shell 层用 `/e/` |
| E4 | `git add` 报 "paths are ignored" | `.gitignore` 用 `reports/**`、`docs/*` 黑名单+白名单模式，新文件默认忽略 | 在 `.gitignore` 尾部按既有格式加 `!` 白名单行；`reports/phase1/` 这类整目录被排除的用 `git add -f` 单文件 |
| E5 | edge_tts 报 `Invalid voice 'zh-CN-XiaoxiaoNeural-Female'` | edge-tts 7.x 需要裸声音名；MPT 的 UI 名带 `-Female` 后缀需转换 | 直接调用 edge_tts 时用裸名 `zh-CN-XiaoxiaoNeural`；走 MPT 的 `parse_voice_name()` 转换 |
| E6 | CRLF 警告刷屏（`LF will be replaced by CRLF`） | Windows 行尾自动转换 | 无害，不处理；不要为此改 `core.autocrlf` |
| E7 | whisper 首次运行悄悄下载 ~3GB 模型 | MPT 默认 `model_size = "large-v3"` | MPT `config.toml` 固定 `model_size = "small"`；任何模型下载前必须单独获批（30GB 预算） |
| E8 | 关键帧证据出现"文字残影" | H.264 快速 seek 落在 B 帧上产生假残影 | 视觉证据只用 OpenCV 顺序解码或 Remotion direct still；禁止 fast seek 取证 |
| E9 | 声画不同步（旁白继续画面静止） | 画面按固定等长分段假设，未消费真实音频时长 | 单一 timing manifest 驱动 Remotion 场景、VoiceOver、字幕；manifest/hash 漂移超过 1 帧（30FPS）失败关闭 |
| E10 | 剪映桌面看不到新草稿 | 剪映只枚举 C 盘 projects root，草稿实际在 E 盘 | 使用经验证的 C→E directory junction 作为可见性索引；媒体绝不复制到 C 盘 |
| E11 | `git worktree list` 显示已不存在的目录（prunable） | worktree 工作目录被手动删除但注册表残留 | `git worktree prune` 清注册表；删工作目录用 `git worktree remove <path>` |

## 3. 已知环境事实（不要重复询问）

- OS：Windows 原生；shell 是 Git Bash；时区 Asia/Shanghai。
- Python：系统默认 3.14，项目/工具用 `py -3.12` 建独立 venv。
- FFmpeg 8.1.1 在 PATH（WinGet 安装）。
- LLM：`https://token-plan-cn.xiaomimimo.com/v1` + `mimo-v2.5`（OpenAI 兼容）；密钥只走环境变量/管道/密钥文件，见 `docs/MONEYPRINTER_TURBO_SETUP.md`。
- 大目录约定：所有渲染产物/草稿/运行态在 E 盘；`external/` 为 gitignored 第三方克隆。
