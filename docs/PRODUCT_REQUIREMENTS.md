# 视频工厂产品需求

Updated: 2026-10-24 · Owner: Jovi

## 产品目标

让 Jovi 用较少人工组织工作，稳定产出有工程信息量、事实可追溯、视听可审核的原创短视频。内容覆盖 App、网页产品、嵌入式、原理图和硬件工程。

2026-10-23 用户确认继续视频工厂方向；后续可增加网页/App 操作入口。直接生成通用 App、网站、PCB 或生产硬件的工程平台不在本次扩展范围。

## 用户场景

1. 给技术主题和已验证事实，生成原创讲解视频。
2. 提供有处理权的参考 MP4，分析结构和节奏，重新创作脚本、旁白与画面。
3. 提供 App/网页真实截图、录屏及功能事实，制作产品演示。
4. 提供可信原理图、代码、实验和硬件素材，制作工程说明，区分仿真、实测与目标设计。

前三类已有不同程度实现；面向任意工程材料的通用自动化仍是规划目标，不能视为已验收。

## 需求与验收

| ID | 需求 | 验收依据 |
|---|---|---|
| R01 | 主题到脚本、分镜和视频 | 事实与来源绑定，输出原创 MP4、质量报告、审阅包 |
| R02 | 参考视频原创重构 | rights receipt、SHA、抽象分析、difference report、人工原创性审核 |
| R03 | 工程画面与旁白一致 | 波形、原理图、代码、公式真实可见且技术正确，不能用无关卡片代替 |
| R04 | App/网页产品演示 | 授权真实产品截图/录屏，焦点动作绑定旁白；产品模板只服务其适用内容 |
| R05 | 完整旁白与同步字幕 | source/aligned PCM/台词绑定，无裁掉有效尾音，字幕和动作按实测 cue |
| R06 | 按 Job 选择画布 | 9:16/1080×1920 或 brief 指定 16:9/1920×1080，默认 30fps、H.264/AAC |
| R07 | 可追踪、取消、重试、恢复 | SQLite Job/Event/Artifact/Stage Attempt、幂等键和 lifecycle 证据 |
| R08 | 可审核交付 | 最终媒体 SHA、来源、版本、质量结论、人工决定一致；失败如实返回 |
| R09 | 多入口复用生产链 | 后续飞书、网页/App 复用任务接口与 SQLite，避免第二渲染/状态系统 |
| R10 | 资源、品牌、发布受控 | GPU 重任务串行；模型下载须授权；角色 opt-in + 原始资产 receipt；人工发布 |

## 单条交付与整阶段完成

交付包含脚本/Storyboard、素材来源、Timeline、可解码 MP4、音频/字幕证据、质量报告、审阅包和任务状态。参考模式另含入库 receipt、rights、分析和差异报告。可选编辑工程不能代替本地 MP4。

机器合格后进入 PENDING_REVIEW；人工观看/试听结果绑定精确媒体 SHA。工程讲解视频不能代替真实板级验证或硬件认证。

当前 topic_only_v1 要求 Flash/watchdog、FreeRTOS、I2C 和一个不同的 live topic 有合格 Prereview 与明确批准的人审。legacy_topic_reference_v1 保留参考视频合同。Lifecycle、Acceptance Manifest、Boundary Audit、独立审核和 Formal Gate 齐全后才能提升阶段。

阶段执行顺序见 [PRODUCT_PHASES.md](PRODUCT_PHASES.md)，当前阻塞见 [PROJECT_REVIEW.md](PROJECT_REVIEW.md)。
