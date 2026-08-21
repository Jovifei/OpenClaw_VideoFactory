# AI Director Phase 2 Legacy Chrome Host Baseline 005W

## 当前结论

当前产品线仍为 AI_DIRECTOR_PHASE2_LOCAL_REMEDIATED。正式项目线仍为：

    P0: not_started
    P1: blocked_by_P0
    P2: blocked_by_P1

005V 曾在本地基线处停止为 BASELINE_BLOCKED，没有执行 Preflight、Worker、Provider cache/auth、codex exec、smoke、acceptance、Desktop handoff 或 MP4。005W 只验证该基线阻断是否属于当前 Windows Chrome 主机上下文；它不是 Provider 资格。

## 005T 不可变边界

- Run: session_20260811T175916Z_43092
- State SHA-256: ffc27a599151dd649d428180f67900d74e095120c0f2c1075fae71b77ddff2de
- Read-only terminal ledger SHA-256: e72ad3787267162fe4e56b840f6e7f762ccc227eb637d3e45b1bf4db978554f3
- Status: BLOCKED_DETACHED_WORKER_DIED
- Smoke / acceptance / MP4: 0 / 0 / 0

005T、005U、005U1 和 005V 历史报告没有被重写或复用。

## 主机合同

静态审查确认 src/factory/mascot.py 仍使用本地 SVG、独立 Chrome profile、headless=new、ANGLE/SwiftShader、allow-file-access-from-files、no-first-run、1360×780 和 30 秒超时；未发现 no-sandbox、disable-gpu、网络 URL、浏览器下载/升级或第二 renderer。

本次固定输入：

- mascot.py SHA-256: 0bfe19a151c38ccc7b9a0e0b920e2fb821cefadd5ef0a3c389b5eb83b4e6196e
- test_p1_candidate_media.py SHA-256: de72adab0495a9239e1c6f06d8ee71042a7ac182718cdd8b94855bafab1179d0
- Chrome version: 151.0.7922.110
- Chrome binary SHA-256: 1c8a72b0e6b5a4dd1de5ce42a7b11460753d8941baebda208360475f31eb17d2

## 一次性运行证据

外部 session 标识为 session_20260813T135342Z_005w。仓库不保存外部绝对路径、原始 stderr、完整命令行、Chrome profile 或用户目录。

### 目标 contact-sheet 测试

唯一一次目标专测结果：

    1 passed in 1.62s
    exit code 0

测试内部断言了 PNG 签名、1360×780 尺寸、八个 Pink Pig pose 和 deterministic contact-sheet 合同。测试使用 TemporaryDirectory，因此 PNG 在测试结束时自动清理；报告明确记录为“测试断言通过、PNG 未保留”，没有伪造 PNG hash。

### Legacy 完整组

在目标专测通过后，完整组只运行一次：

    56 passed, 1 skipped, 13 subtests passed in 50.95s
    exit code 0

完整组包含其既有 contact-sheet 测试；这被记录为一次完整组执行，不作为第二次独立目标专测。没有再次单独重试目标测试。

## 安全与 Provider 隔离

本任务中以下计数均为零：

    Preflight: 0
    Supervisor/Worker: 0
    Codex smoke: 0
    Real acceptance: 0
    codex exec: 0
    MP4: 0
    cache/config/auth access: 0

只写入计划、005W Change Request、脱敏报告、待办和允许的外部 session root。没有修改产品代码、测试、Chrome、PROJECT_STATUS.yaml、OpenClaw、Feishu、Gateway、Binding、Cron、Git index/history。

目标测试和完整组的 raw 日志已在验证退出码和稳定结果后从外部 session 删除；只保留脱敏结果、输入 hash 和测试计数。

## 当前阶段与后续门

当前证据已经通过两个 specialist reviewer 和一个全新 final reviewer：

    CHROME_HOST_BASELINE_PASS

Final reviewer: APPROVED_FOR_005V_LOCAL_GATE_REENTRY

该结论只允许另行重新冻结 005V source closure、重跑本地全回归并重新进行 prelaunch review。它不自动执行 005V Preflight/Worker，更不能进入 006。

唯一允许的路线仍是：

    005W final approval
      → fresh 005V local source-freeze / prelaunch review
      → separately authorized 005V Preflight
      → one Worker / one smoke / one acceptance
      → real MP4 and media review
      → AI_DIRECTOR_PHASE2_REAL_PROVIDER_QUALIFIED
      → separately plan 006 Video Agent Orchestration
