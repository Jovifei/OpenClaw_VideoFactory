# Prompt for the next Codex Agent — Phase 1 closure

复制下面内容给新的 Codex Agent。不要让它重新制定 Feishu-first 路线。

---

你现在接手：

`E:\project\OpenClaw_VideoFactory`

固定远端仓库：

`https://github.com/Jovifei/OpenClaw_VideoFactory`

固定当前分支：

`codex/phase1-reference-video-analysis-001`

你的任务不是重新规划项目，而是**把当前已经高度成熟的 Phase 1 本地视频工厂正式收口到 Gate**。

## 1. 开始动作

先执行：

```powershell
Set-Location E:\project\OpenClaw_VideoFactory
git fetch
git status --short --untracked-files=all
git rev-parse HEAD
git rev-parse origin/codex/phase1-reference-video-analysis-001
git diff --check
```

若本地落后远端，先安全 fast-forward/同步当前分支；如果工作树有用户未提交文件，保护它们，不得 reset、clean、自动 stash、rebase 或 force push。

## 2. 强制阅读顺序

完整阅读：

1. `START_HERE_CODEX.md`
2. `PROJECT_STATUS.yaml`
3. `docs/README.md`
4. `docs/CURRENT_ARCHITECTURE.md`
5. `docs/PRODUCT_PHASES.md`
6. `handoff/codex/PROJECT_HANDOFF_20260905.md`
7. `handoff/codex/CURRENT_BACKLOG.yaml`
8. `runbook/11_PHASE1_COMPLETION.md`
9. `docs/OPEN_SOURCE_SKILL_MATRIX.md`
10. `docs/REFERENCE_VIDEO_ANALYSIS.md`
11. `docs/PINK_PIG_CURRENT_POLICY.md`
12. `skills/video-production-chain/SKILL.md`
13. `tasks/todo.md` 最新 Phase 1 内容
14. 当前任务涉及的源码、Schema、测试、Change Requests

`docs/PINK_PIG_PHASE1_ARCHITECTURE.md`、旧 P0/P1/P2 报告和历史 Prompt 只作历史参考；与上面当前文档冲突时，不得采用旧结论。

## 3. 最终目标

Phase 1 必须完成两个可用用户路径：

### A. Topic → 自动视频

用户给主题，例如：

`FreeRTOS 优先级反转是怎么发生的？`

系统自动完成：

```text
verified factual input
→ script
→ storyboard
→ approved assets / deterministic technical visuals
→ narration
→ subtitle/timing/speech cues
→ Remotion/FFmpeg
→ final local MP4
→ quality report
→ review package
→ Jovi human review
```

### B. Reference → 分析 → 原创视频

用户给有权处理的本地 MP4 + rights：

```text
read-only ingest / SHA-256
→ ffprobe / scene / pace / optional cached ASR
→ abstract reference report
→ original brief
→ new script/storyboard/visuals/audio
→ new MP4
→ difference report
→ Jovi originality review
```

Phase 1 成功后才允许另开 Phase 2 飞书任务。

## 4. 你绝对不要重做的东西

已经有：

- SQLite Job/Event/Artifact/Stage Attempt：`src/factory/db.py`
- lifecycle：`src/factory/state.py`
- Phase 1 CLI：`src/factory/phase1_cli.py`
- topic/reference planning：`src/factory/phase1_local.py`
- reference analyzer：`src/factory/reference_video.py`
- Director：`src/factory/director/`
- video pipeline：`video_factory/pipeline/`
- renderer entry：`generate_video.py`
- Remotion technical visual：`remotion/`
- Human Review / Prereview：`src/factory/phase1_acceptance.py`
- Formal Gate：`src/factory/phase1_gate.py`

只有实际测试/证据出现兼容失败时，才允许最小修复。

禁止创建第二套 pipeline、第二个 state DB、第二个 all-in-one video backend。

## 5. 当前执行波次

### Wave 0 — 建立当前事实基线

不要复述旧的 `355 passed`、`360 passed`、`322 passed` 之类历史数字作为当前总结果。

用固定 Python（存在则优先）：

`C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe`

至少独立运行：

```powershell
python -m pytest tests/phase1_acceptance -q
python -m pytest tests/phase1_local -q
python -m pytest tests/reference -q
python -m pytest tests/director -q
python -m pytest tests/video -q
python -m pytest video_factory/tests -q
```

并运行最新 RC/reference/remotion/Jianying Change Request 对应 focused tests。

如果 root `pytest` 被 unrelated vendor research dependency 或历史 Feishu/P0 环境 suite 阻塞：

- 如实记录；
- 明确哪些不是 Phase 1 Gate suite；
- 不隐藏失败；
- 不把 unrelated failure 当成 Phase 1 产品失败；
- 不通过简单相加构造一个虚假的总测试数。

产出一个新的 bounded regression JSON/Markdown，绑定当前 HEAD。

### Wave 1 — 三个固定主题统一收口

#### Modbus

已有 baseline。不要重做全部内容。

找到当前最佳最终候选，重新验证：

- MP4；
- quality report；
- review package；
- SQLite artifact hash；
- current Schema；
- Human Review；
- Prereview。

一次只把一个候选交给 Jovi 审阅。

#### Flash / Watchdog

已有 brief、technical assets、多轮 MP4/Jianying 证据。

必须：

- 只选择一个最终候选；
- 默认使用已经修正的 mascot-off 技术版本，除非 Jovi 明确给了原始 Pink Pig asset pack；
- 不混用 v1/v2/v4/v8 等不同候选的 evidence；
- 绑定 exact final MP4 SHA；
- Human Review；
- Prereview。

#### FreeRTOS

已有：

`examples/phase1_local_freertos/brief.json`

这是当前最明确的缺失成片工作。

你需要自己完成：

- factual validation；
- deterministic technical illustrations；
- script；
- storyboard；
- asset selection；
- TTS/narration；
- subtitle/timing；
- Remotion/FFmpeg render；
- final MP4；
- quality report；
- review package；
- SQLite PENDING_REVIEW；
- 给 Jovi 一个明确候选做 Human Review；
- review 后生成 Prereview。

技术事实图禁止使用不受控 text-to-image 作为事实画面。

### Wave 2 — Lifecycle qualification

生成 fresh machine-readable evidence：

1. cancel；
2. failed → retry；
3. restart recovery（真实新进程从 SQLite/Artifact 状态继续）；
4. encoder fallback（NVENC/CPU）。

每项必须包含真实 Job ID、timestamp、assertions、artifact hashes 和 status。

Markdown 自述不能代替机器 evidence。

### Wave 3 — Reference qualification

当前分支已有 RC high-pass reference reconstruction：

- corrected geometry；
- 9:16 Remotion visual；
- local narration；
- timing manifest；
- measured semantic speech cues；
- speech-cue-bound knowledge cards；
- post-render/all-frame quality evidence；
- optional Jianying draft。

先找出**唯一最新候选**，不要混合不同版本报告。

验证：

- report hashes；
- final media；
- source/output boundary；
- no source audio；
- no source frames as final assets；
- technical correctness；
- timing；
- Difference Report。

然后把 exact candidate 提供给 Jovi，让他实际：

- 看；
- 听；
- 判断音画质量；
- 判断原创性。

只有 Jovi 审过后，才写 Human Review approved/changes_required。

如果 Acceptance Manifest 仍要求严格 `local_reference` fixture，而当前 RC work 属于公开/reference research，不得偷换概念。此时停下来请求 Jovi 提供一条拥有权利的本地 MP4 + rights，再走标准 `create-reference` 路径。

Synthetic reference 只能用于测试，不能替代人工原创性验收。

### Wave 4 — Final acceptance

全部 Human Review 完成后：

1. 生成各 Job Prereview；
2. 生成 Boundary Audit；
3. 生成新的 bounded regression summary；
4. 生成 Phase 1 Acceptance Manifest，只引用最终候选；
5. 对所有引用 evidence 计算/验证 SHA-256；
6. 做 fresh clone / equivalent reproducibility check；
7. 新开独立只读 reviewer，审核：
   - branch/HEAD；
   - hashes；
   - candidate uniqueness；
   - no stale-version mixing；
   - Human Review binding；
   - no private path/reference leak；
   - no Feishu/OpenClaw/Cron side effect；
   - test scope honesty；
8. reviewer 通过后，Formal Phase 1 Gate 只运行一次。

Gate 成功：

`PHASE1_LOCAL_VIDEO_FACTORY_READY`

Gate 失败：

保留失败报告，状态：

`PHASE1_COMPLETION_BLOCKED:<exact_reason>`

禁止修改 Gate 标准来“凑通过”。

## 6. Render profile

不要再把一个全局分辨率写死到所有任务。

Job-scoped profile：

- vertical / Douyin knowledge: 1080×1920, 9:16；
- landscape / reference-edit: 1920×1080, 16:9 when requested；
- 30 FPS；
- H.264/AAC where audio is required；
- profile-specific safe area / subtitle contract。

当前 `phase1_quality_report.schema.json` 已支持竖屏和横屏，也支持 Pink Pig `pass/off`。不要回退旧 Schema。

## 7. Pink Pig

当前 production policy：

- mascot default off；
- `Jovifei/ian-fenzhu-illustrations` = style/persona source，不等于最终角色图库；
- Jovi explicit opt-in；
- enabled 时必须 Jovi-owned original asset pack + receipt；
- repo-created PNG/SVG、AI temp art、upstream sample 不能冒充 final IP；
- mascot-required 但缺资产 → fail closed；
- normal technical video → mascot-off 可继续。

不要为了“品牌统一”重新启用已经证明不匹配用户 IP 的历史 mascot 图。

## 8. Jianying

Jianying 是 optional editable/manual-review branch。

Phase 1 mandatory：

`local MP4 + quality report + review package`

Optional：

`visual-only MP4 → jianying-editor-skill → Jovi manual review/export`

禁止自动导出、自动发布。Jianying 失败不推翻核心 MP4。

## 9. Open-source策略

遵守 `docs/OPEN_SOURCE_SKILL_MATRIX.md`：

- VideoClaw：借 stage-artifact / user intervention / recoverable workflow，不引入第二套 backend/state DB；
- Remotion：使用当前官方 skills/best practices；
- video-podcast-maker：只借方法，当前 CC BY-NC 4.0，不随意复制代码/模板进未来商业路径；
- PySceneDetect：reference scene analysis；
- faster-whisper：optional reference ASR；
- ComfyUI/WhisperX/OpenMontage 等不作为当前 Gate blocker；
- 不增加 n8n/LangGraph/Temporal。

## 10. Phase 1 期间禁止

- Feishu；
- Gateway/Binding/OAuth；
- Cron；
- automatic topic scheduling；
- automatic Douyin publish；
- unapproved model/node download；
- second pipeline / DB / orchestrator；
- historical Codex Provider cache recovery as the main task；
- fake Human Review；
- stale evidence mixing；
- fake aggregate test totals。

## 11. Git / remote

继续当前分支，不创建新分支。

可以自行完成、测试、commit、push 到：

`codex/phase1-reference-video-analysis-001`

每次 commit 前：

- focused tests；
- `git diff --check`；
- secret/private-path scan；
- only scoped files staged。

不要 commit：

- `dist/` runtime output；
- SQLite runtime DB；
- private reference MP4；
- model/cache；
- credentials；
- private Human Review with local sensitive path。

## 12. Obsidian

每个真实停止点更新：

`E:\AI_Tools\Obsidian\Data\notes-personal\codex_memory\03-项目记忆\OpenClaw_VideoFactory\`

至少：

- `04-落地状态与执行计划.md`
- `06-Phase1本地视频工厂收口.md`

记录 exact HEAD、当前候选、证据、Jovi 决策、剩余 blocker。

不要写 Token、私有参考视频内容、raw prompt、raw model output。

## 13. 允许找 Jovi 的情况

尽量自己执行，不要不断问用户。

只有这些需要停：

1. 一个确定的 final candidate 已经准备好，需要 Jovi 看/听；
2. 需要 Jovi 的授权本地 reference MP4；
3. mascot-required 任务需要 Jovi 原始 Pink Pig asset pack；
4. 许可证、模型下载、预算需要人工授权；
5. 出现有最小复现的真实 blocker；
6. Formal Gate 已得到结果，需要批准 phase promotion。

Routine implementation、测试、报告、JSON 对账、Git 提交/推送由你自己完成。

## 14. 停止汇报格式

每次真正停止时只汇报：

- current branch / HEAD / remote relation；
- completed work；
- exact tests/evidence；
- exact candidate/job/hash；
- one required Jovi action（如果有）；
- remaining blockers；
- Obsidian update；
- commit/push status。

不要只输出“计划已完成”。
