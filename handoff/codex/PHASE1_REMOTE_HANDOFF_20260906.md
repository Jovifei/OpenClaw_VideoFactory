# 本地 Codex 接手：Phase 1 自动出片增量 012

## 先看结论

本轮完成了远端有界审核、社区方案复核、现有 Topic 入口的“一次渲染＋母版派生审阅资产”代码和测试。没有启动飞书，没有宣布 Phase 1 通过，没有替代 Jovi 看/听，没有改动本地 AGENTS。

交付分支：`codex/phase1-render-once-review-012`。基线为 main `4eb3d37e1464d6f55f0a6bbff5abad98dcc664be`；最终交付提交由分支实时解析并在用户收到的收据中记录。不要退回 c815/1961 等旧分支。远端通过 GitHub Git Data API 原子提交，终端 clone/fetch 因 DNS 未成功；不要将本轮称为 fresh clone 验证。

必读：`docs/PHASE1_REMOTE_AUDIT_20260906.md`、本文件、`reports/phase1/render_once_review_012_tests.json`，再读当前 START_HERE、PROJECT_STATUS、PRODUCT_PHASES、runbook/11 和相关源码/schema。旧 NEXT_AGENT_PROMPT_20260905 的固定旧分支以及“OpenMontage未vendor”不再是当前事实。

## 交付文件与行为变化

- `scripts/render_phase1_topic_visual.mjs`：CLI flags、TechnicalExplainer、E盘、本地 Chrome、aspect、layout/mascot 合同保留。只执行一次 renderMedia；保留 FFmpeg 去音轨；随后从最终 visual master 派生审阅图/片段。
- `scripts/lib/phase1_review_artifacts.mjs`：帧区间、fresh path 检查、SHA、FFmpeg 提取、ffprobe 解码帧数/流验证。
- `tests/video/phase1_review_artifacts.test.mjs`：Node 内建测试＋真实 FFmpeg 合成视频；无外部测试库。
- `docs/OPEN_SOURCE_SKILL_MATRIX.md`：修正 OpenMontage/MPT 的实际吸收状态；没有新增依赖或改变许可证。
- 审核报告、CR、测试 JSON 和当前交接。没有修改 SQLite、Gate 标准、模型、PNG、AGENTS 或现有 TTS。

报告维持 `visual.scene_timing[].still/clip.filename/sha256`，新增 source_visual_sha256、frame_range、frame_count、rendered_duration_microseconds。`clip.duration_microseconds` 仍是原始语义时长，量化后实际时长另字段；review clips CRF18 重编码，不声称无损，不替代母版。中点 PNG 是真实母版帧。

**重要行为变化：输出必须新鲜。** 用 `.../attempt_012_001/` 之类新 attempt 目录，output/report/stills/clips 均在一个 report root 内。旧文件/非空目录被拒绝。失败后保留证据，开新目录重试，不能清空旧候选。

## 已测与未测

本轮隔离增量 Node suite 25 passed / 0 failed / 0 skipped，包含真实 FFmpeg 抽取、3场景帧数16/18/26、PNG逐像素比对、路径/旧文件保护、短母版/额外音轨/坏文件拒绝、约900组非整帧边界枚举。Syntax checks 和 scoped whitespace check 见 JSON。

原合并的 502 passed 来自 CR 011，56 passed 来自 Jovi 的报告；都不是本轮重跑，不能相加。未运行完整 pytest、Remotion/Chrome/TTS、Windows盘符/junction实机、显卡 fallback、新进程 lifecycle、人审或 Gate。不要将 synthetic MP4 计为生产/原创性证据。

## 接手执行顺序

### 1. 保护用户工作区，取最新分支

在原仓库执行 `git fetch origin`、`git status --short --untracked-files=all`、`git diff --check`，记录 main 与交付分支 SHA。保护 Jovi 原有 AGENTS.md，禁止 reset/clean/stash/rebase/force push/删除远端分支。

推荐为交付分支创建一个新的 E 盘 worktree，不改变原工作区。worktree 必须不存在；已存在时读取/确认，不自动删除。如果 main 又前进，普通 merge 最新 main，冲突按 scoped 修改解决，不回退。

### 2. 先测增量和现有合同

在 worktree：

```powershell
node --check scripts/render_phase1_topic_visual.mjs
node --check scripts/lib/phase1_review_artifacts.mjs
node --test tests/video/phase1_review_artifacts.test.mjs
python -m pytest tests/video/test_phase1_topic_visual.py tests/video/test_phase1_post_render_check.py tests/video/test_phase1_subject_media.py tests/phase1_local/test_phase1_subject_delivery.py -q
```

再复用 CR 011 的真实 bounded suites，至少一次统一收集：

```powershell
python -m pytest tests/phase1_local tests/phase1_acceptance tests/video tests/openmontage -q
```

先检查实际本机解释器、依赖及测试集合；不自动安装新模型。root pytest 的 unrelated vendor/P0 失败必须记录，但不能混进 Phase 1 总数；不要多轮相加。若缺 ignored 历史 demo，则按既有 CR011 恢复权限处理，不能偷标 pass。读取 remotion/package.json 后执行其中原有验证脚本，不凭空发明 npm命令。

### 3. 实机双 aspect 测试

沿用现有 create-subject/subject-media 路径及 CLI --help，不建新 pipeline。复用已批准的 TTS/timing，不切换后端。选择新 attempt root，验证横竖两种 profile：

- 一次 renderMedia 的最终 master 可解码，H264/30FPS、没有音轨；
- stills/clips 数量及 SHA 和 Python verifier 一致；片段逐个可解码且帧数覆盖 master、不漏不重；
- 所有 entry.source_visual_sha256 等于 visual.sha256；
- 原 post-render check 和 contact sheet 仍通过；
- 音频合成后的最终可听 MP4 与原 subject delivery/review package 合同一致；
- 测量完整耗时、FFmpeg派生成本和内存，不声称先验2倍加速。

保存失败与成功的原始报告，不混候选。实机回归绿后可正常 merge 到最新 main 并 push；该代码合并不意味着 Phase 1 promotion。

### 4. 真正的下一内容 blocker

I2C 78/85 不能通过加入“工程/配置/时间”等关键词作弊解决。先用已有研究 brief 和失败候选做来源绑定的编辑评审；不绕过预算/不降低85门槛。主题特定视觉必须真的呈现接线/信号/时序，不能把文字卡换标题当 system_diagram。只扩展当前 script/scene schema/Remotion lineage，事实来源和技术边界都要可追溯。完成一条可听候选后再交 Jovi 看/听。

### 5. 资格收口

当前 `topic_only_v1` 要 Flash、FreeRTOS、I2C、一个不同 live topic；按当前 Gate/schema 运行，不强塞旧 reference prerequisite。legacy_topic_reference_v1 留给 Topic＋Reference 联合资格。Reference 架构保持，不能误称已人审通过。

随后补真实 cancel、failed→retry、独立新进程 restart recovery、encoder fallback；不是填四个 passed JSON。所有人审以 exact final MP4 SHA 绑定。候选/manifest/boundary/fresh bounded regression 齐后，独立只读审核，再执行一次 Formal Gate。仅 Jovi 批准后进入后续阶段，Phase 2 飞书不得顺带实施。

## 停止与回报

只有需要 Jovi 看/听已准备好的唯一候选、授权参考或原始IP资产、批准下载/预算/阶段，或已最小复现的本机阻塞时才询问。其余实施、测试、修复、commit/push 自行完成。更新 tasks/todo 与用户 Obsidian 两份项目状态文档；远端执行环境无该本机目录，本轮未声称已更新。

回报 exact branch/HEAD、与最新 main 关系、scoped测试命令与结果、job/candidate/SHA、未解决项、commit/push、人审所需单一动作。不要只写“全部已完成”。
