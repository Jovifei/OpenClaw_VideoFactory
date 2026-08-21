# AI-DIRECTOR-PHASE2-LEGACY-CHROME-HOST-BASELINE-005W — Luna 闭环执行计划

## 1. 当前事实、任务目标和停止线

Jovi，005V 不能进入 Preflight 或真实 Provider。当前唯一阻断是当前未改代码树的 legacy contact-sheet 测试在 Windows Chrome 上失败：

    tests/test_p1_candidate_media.py::CandidateMediaTests::
      test_all_mascot_poses_are_deterministic_and_contact_sheet_is_png
    → mascot_contact_sheet_failed:2147483651:local_path_redacted
    → STATUS_BREAKPOINT (0x80000003)

当前本地证据：

| Gate | 结果 |
|---|---|
| 005V Pester 合同组 | 76 passed |
| Director / Video / Video Factory | 47 / 273 / 5 passed |
| legacy 锁定组 | 55 passed / 1 failed / 1 skipped / 13 subtests |
| 005V Provider 权限 | 全部未使用：无 Preflight、Worker、cache/auth、smoke、acceptance、MP4、Desktop handoff |

任务身份：

    task_id: AI-DIRECTOR-PHASE2-LEGACY-CHROME-HOST-BASELINE-005W
    mode: host_baseline_evidence_only
    external_root: E:/Claude_allow/Download/chrome-host-baseline-005w/
    maximum_targeted_contact_sheet_runs: 1
    maximum_full_legacy_runs: 1
    does_not_imply_real_provider_pass: true

005W 的唯一目标是在获准、干净且可归因的 Windows 主机上下文中，证明当前未改动树的 legacy contact-sheet 基线能否通过。它不修产品代码、不更换或配置 Chrome，也不消耗 005V 的任何一次性权限。

成功终态仅为：

    CHROME_HOST_BASELINE_PASS

它只允许后续另行规划和授权 005V 的本地 source-freeze 与 prelaunch review 重新进入；它绝不授权 005V Preflight、Worker、cache、smoke、acceptance、006、Feishu、Cron 或正式 P0/P1/P2 Gate。

## 2. 历史证据与强制边界

### 2.1 不可变历史

下列内容只读核验，绝不修改、删除、复用或重试：

    005T run_id: session_20260811T175916Z_43092
    005T state SHA-256:
    ffc27a599151dd649d428180f67900d74e095120c0f2c1075fae71b77ddff2de
    005T terminal ledger SHA-256:
    e72ad3787267162fe4e56b840f6e7f762ccc227eb637d3e45b1bf4db978554f3
    005T terminal status: BLOCKED_DETACHED_WORKER_DIED
    005T smoke / acceptance / MP4: 0 / 0 / 0

005V 的 BASELINE_BLOCKED 报告与 Change Request 同样保留；005W 不得把它改写为通过，也不能恢复或消耗它的单次执行配额。

正式阶段持续冻结：

    P0: not_started
    P1: blocked_by_P0
    P2: blocked_by_P1

### 2.2 允许写入

仅限下列路径：

    tasks/plans/2026-08-13-ai-director-phase2-legacy-chrome-host-baseline-005w.md
    reports/change_requests/AI-DIRECTOR-PHASE2-LEGACY-CHROME-HOST-BASELINE-005W.json
    reports/CHROME_HOST_BASELINE_005W.json
    reports/AI_DIRECTOR_PHASE2_LEGACY_CHROME_HOST_BASELINE_005W.md
    tasks/todo.md
    tasks/lessons.md
    handoff/codex/IMPLEMENTATION_BACKLOG.yaml
    .gitignore
    E:/Claude_allow/Download/chrome-host-baseline-005w/
    指定的 Obsidian 追加页面

只读输入仅为 src/factory/mascot.py、tests/test_p1_candidate_media.py、本地 Pink Pig SVG/Registry、005T/005V 计划和报告、项目规则与既有 Obsidian 路线记录。

### 2.3 禁止面

- 不改 mascot、任何测试、Chrome flags、SVG、Registry、Python 依赖或浏览器安装。
- 不使用 --no-sandbox、--disable-gpu、真实用户 Chrome profile、浏览器下载/升级、注册表或系统策略修改。
- 不运行 provider_qualification.ps1 任意 Mode、codex exec、Worker、Supervisor、smoke、acceptance 或 generate_video.py --topic。
- 不读取、移动或修改 models_cache.json、config.toml、auth.json；不启动/关闭/挂起 Codex Desktop；不产生 MP4。
- 不修改 PROJECT_STATUS.yaml、OpenClaw、Feishu、Gateway、Binding、Cron、Douyin、Git index/history。
- 不删除既有 .pytest-tmp-* 或 .test-tmp 目录；不把清理作为通过条件。
- B2 contact-sheet 至多一次，B3 完整 legacy 组至多一次；任何失败不以重跑掩盖。

## 3. Change Request 与 Luna 执行模型

### 3.1 Change Request

[1/9] 创建以下 Change Request：

    {
      "id": "AI-DIRECTOR-PHASE2-LEGACY-CHROME-HOST-BASELINE-005W",
      "mode": "host_baseline_evidence_only",
      "does_not_imply_real_provider_pass": true,
      "does_not_authorize_product_code_changes": true,
      "does_not_authorize_chrome_configuration_changes": true,
      "does_not_authorize_provider_cache_or_auth_access": true,
      "does_not_authorize_worker_start": true,
      "does_not_authorize_commit_or_push": true,
      "maximum_targeted_contact_sheet_runs": 1,
      "maximum_full_legacy_runs": 1,
      "execution_status": "prepared"
    }

CR 还必须固化允许路径、禁止面、005T hashes、005V 未消耗次数、external root 与最具体停止状态。

### 3.2 子代理规则

全部临时子代理固定：

    model: gpt-5.6-terra
    reasoning: xhigh
    禁止: sol

工作顺序：

    静态 Chrome/mascot 合同 reviewer
      + Git/证据 reviewer（只读、可并行）
      → 主 Luna 唯一执行 B2/B3
      → 主 Luna 复现 reviewer FAIL
      → 全新 final reviewer

Reviewer 不得启动 Chrome、Provider、Worker 或访问 cache/auth。完成的子代理立即结束；没有任何 reviewer 结论可替代主测试证据。

## 4. 九阶段实施

### [1/9] 冻结仓库与证据边界

读取 START_HERE_CODEX.md、PROJECT_STATUS.yaml、AGENTS.md、tasks/lessons.md、005T/005U/005U1/005V 计划、CR、报告与 Obsidian 03、04、05、07、08、10、11、12。

记录：

    git branch --show-current
    git rev-parse HEAD
    git diff --cached --quiet
    git diff --check
    git status --short --untracked-files=all

预期：

    branch = codex/ai-director-video-factory-phase2-001
    HEAD = 76180a59ea662bdf168d88baaeb777d3e8eb59ef
    index_empty_exit = 0

重新 hash 以下 six protected dirty 文件并与 005V 记录比较：

    PROJECT_STATUS.yaml
    reports/P0_ACCEPTANCE_MATRIX_V2.yaml
    scripts/analysis_request.py
    scripts/analyzer_mcp.py
    scripts/mcp_ingest_attachment.py
    scripts/media_action_ticket.py

同时重新核验 005T immutable hashes、005V BASELINE_BLOCKED 证据和其 Preflight、Worker、smoke、acceptance 均为 0。任一不符，写 INCONCLUSIVE_EXTERNAL_HOST_EVIDENCE 并停止，不运行 Chrome。

### [2/9] 静态 contact-sheet 合同审计

只读审查 mascot 模块与目标测试；记录 source/test/SVG 输入清单和 SHA-256。

必须保持：

    --headless=new
    --use-gl=angle
    --use-angle=swiftshader
    --hide-scrollbars
    --allow-file-access-from-files
    --no-first-run
    独立 --user-data-dir
    --window-size=1360,780
    本地 file:// SVG 输入
    30 秒 contact-sheet timeout

并证明不含 --no-sandbox、--disable-gpu、用户 profile、网络 URL、浏览器下载/安装/升级或第二条 renderer pipeline。

此阶段不得运行 Chrome。若静态合同偏离，写 LEGACY_CONTACT_SHEET_CONTRACT_FAILED，停止并另行规划产品修复；005W 不修。

### [3/9] 建立一次性、可归因主机根

创建全新 run：

    E:/Claude_allow/Download/chrome-host-baseline-005w/
      session_<UTC>_<random>/
        pytest-base/
        temp/
        chrome-profile/
        artifacts/
        sanitized/

执行前：

1. 验证 root/session 不存在，已有父路径不是 reparse point/junction。
2. 以 create-new 方式创建，禁止覆盖或复用。
3. 记录 Windows 主机类别、Python binary SHA-256、Chrome binary SHA-256/版本，以及 source/test/SVG hashes。
4. 仓库报告只记录 Chrome 版本/hash，不记录绝对路径、完整命令行、profile、用户目录、原始 stderr。
5. 将 TEMP/TMP 与 Chrome profile 固定到 session 内。

不能建立可写、非 reparse、可归因 run root 时写 CHROME_HOST_EXECUTION_BLOCKED 并停止。

### [4/9] 一次精确 contact-sheet 主机基线

这是唯一 B2 浏览器执行。它必须使用同一仓库 HEAD、相同 source/test/SVG hash、[3/9] 唯一 session，且不得先在其他环境预跑：

    $PinkPigPython = 'C:\\Users\\Admin\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\python.exe'
    $RunRoot = 'E:\\Claude_allow\\Download\\chrome-host-baseline-005w\\session_<utc>_<random>'
    $env:TEMP = Join-Path $RunRoot 'temp'
    $env:TMP = $env:TEMP
    & $PinkPigPython -m pytest tests/test_p1_candidate_media.py::CandidateMediaTests::test_all_mascot_poses_are_deterministic_and_contact_sheet_is_png -q -p no:cacheprovider --basetemp (Join-Path $RunRoot 'pytest-base')

成功条件：

- exit 0，且恰好 1 passed；
- contact sheet 是 PNG，尺寸恰好 1360×780；
- SVG pose/hash 与 deterministic 联系表断言通过；
- profile、temp 与 artifacts 都在 session root 内。

| 观察 | 强制状态与行为 |
|---|---|
| 再现 2147483651 / 0x80000003 | CHROME_HOST_STATUS_BREAKPOINT_BLOCKED；不重试、不改 Chrome/代码 |
| Chrome 启动失败、超时、主机策略拒绝或输出无法归因 | CHROME_HOST_EXECUTION_BLOCKED；停止 |
| Chrome 可运行但 PNG、尺寸或确定性合同失败 | LEGACY_CONTACT_SHEET_CONTRACT_FAILED；停止 |
| 单测通过 | 仅可进入 [5/9] |

raw stdout/stderr 只可暂存 session root。验证完成后删除 raw 文件；仓库只保留 exit、耗时、Chrome hash/version、flags 摘要、node id、PNG hash/尺寸或稳定错误码。

### [5/9] 一次锁定 legacy 完整组

仅当 [4/9] 通过时，运行一次完整组；使用同一 session 的独立 pytest 子目录，但不得再单独运行 contact-sheet：

    & $PinkPigPython -m pytest tests/test_p1_candidate_cli.py tests/test_p1_candidate_pipeline.py tests/test_p1_candidate_media.py tests/test_p1_candidate_render.py tests/test_p1_candidate_delivery.py tests/test_p1_candidate_inventory.py tests/test_p1_candidate_state.py tests/test_p1_final_audit.py -q -p no:cacheprovider --basetemp (Join-Path $RunRoot 'legacy-pytest-base')

唯一通过线：

    56 passed / 1 skipped / 13 subtests

任一失败、计数下降、超时或无法安全归因写 LEGACY_BASELINE_BLOCKED，停止；不得运行第二组或改测试维持数字。

### [6/9] 脱敏证据与清理

创建：

    reports/CHROME_HOST_BASELINE_005W.json
    reports/AI_DIRECTOR_PHASE2_LEGACY_CHROME_HOST_BASELINE_005W.md

JSON 至少包含 task_id、status、branch、head、contact_sheet.attempt_count/exit_code/png_sha256/width/height、legacy.attempt_count/passed/skipped/subtests，以及 provider_actions.preflight/worker/smoke/acceptance 均为 0。

失败时写最具体状态，并省略不曾执行项目。禁止写 raw stderr、完整路径、profile、prompt、cache/auth 内容、token、完整 Chrome 命令行或私人截图。

仅在确认 session 位于 allowed root 且不是 reparse point 后，删除 raw stdout/stderr、临时 profile 与临时截图；保留脱敏 manifest、PNG hash/metadata 与清理结论。清理失败写 INCONCLUSIVE_EXTERNAL_HOST_EVIDENCE，不能宣称完全通过。

### [7/9] 独立审查

并行两个只读 Luna xhigh reviewer：

1. Chrome/legacy reviewer：核验 source/test/SVG hashes、flags、一次性次数、PNG 1360×780、完整 legacy count 和无 --no-sandbox/浏览器修改。
2. Git/evidence reviewer：核验 005T/005V immutable evidence、six dirty hashes、index、报告脱敏、run-root containment、Provider actions=0 与禁止面。

主 Luna 必须复现所有 FAIL。全部通过后启动全新 final reviewer；唯一允许关闭结论：

    APPROVED_FOR_005V_LOCAL_GATE_REENTRY

它不得被写成 Provider pass、Phase 2 Ready、正式 Gate pass 或 006 ready。

### [8/9] 文档与路线校正

仅追加、不重写历史：

- tasks/todo.md：005W 清单、真实 Chrome host 状态和 005V 已建立但仍 BASELINE_BLOCKED。
- tasks/lessons.md：受管 Chrome STATUS_BREAKPOINT 是主机基线证据问题，不能误报为 Provider/产品逻辑失败。
- handoff/codex/IMPLEMENTATION_BACKLOG.yaml：005W 状态及成功后的唯一依赖。
- Obsidian 04、05、07、10、11、12：追加当前链条并修正 005V 尚未建立的过时说法。
- 新建 14-AI-Director-Legacy-Chrome主机基线005W.md：记录证据层级、状态、005T 不可变性、005V 未消耗次数与下一步。

在 .gitignore 末端只追加：

    !tasks/plans/2026-08-13-ai-director-phase2-legacy-chrome-host-baseline-005w.md
    !reports/CHROME_HOST_BASELINE_005W.json
    !reports/AI_DIRECTOR_PHASE2_LEGACY_CHROME_HOST_BASELINE_005W.md
    !reports/change_requests/AI-DIRECTOR-PHASE2-LEGACY-CHROME-HOST-BASELINE-005W.json

### [9/9] 最终边界审核与停止

执行：

    git diff --check
    git diff --cached --quiet
    git status --short --untracked-files=all
    git check-ignore -q tasks/plans/2026-08-13-ai-director-phase2-legacy-chrome-host-baseline-005w.md

确认：

- index 空、six protected dirty hashes 与 [1/9] 一致；
- 005T run/state/ledger/report 和 005V report/CR 未改变；
- PROJECT_STATUS.yaml、OpenClaw、Feishu、Gateway、Binding、Cron 未被改动；
- 未调用 Provider、Worker、cache/auth、MP4；
- B2 至多一次、B3 至多一次；
- 005W plan、CR、reports 可被 Git 跟踪；
- 所有子代理已经结束。

最终状态只能是：

    CHROME_HOST_BASELINE_PASS
    CHROME_HOST_STATUS_BREAKPOINT_BLOCKED
    CHROME_HOST_EXECUTION_BLOCKED
    LEGACY_CONTACT_SHEET_CONTRACT_FAILED
    LEGACY_BASELINE_BLOCKED
    INCONCLUSIVE_EXTERNAL_HOST_EVIDENCE
    FAIL_REVIEW

## 5. 005W 后的唯一顺序

    005W CHROME_HOST_BASELINE_PASS
      → 单独授权 005V local source-freeze / full-regression / independent-prelaunch-gate re-entry
      → 仅在 005V CR 获得新的本地预启动批准后，才考虑一次 Preflight
      → Worker/Desktop/cache/smoke/acceptance/media/final review
      → AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED
      → 才可单独规划 006 Video Agent Orchestration

005W 失败则只针对最具体失败状态新建任务；绝不通过重跑 005V、重试 Chrome、改变 Chrome sandbox 或提前进入 006 绕过该门。
