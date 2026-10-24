# OpenClaw VideoFactory

为 Jovi 制作工程知识与产品演示视频：主题、工程素材或授权参考视频 → 原创脚本/分镜 → 可审阅 MP4 与质量证据。

内容覆盖 **App、网页、嵌入式、原理图和硬件工程**。用户已确认继续视频工厂方向，后续可增加网页/App 操作入口。当前是 **Phase 1 本地视频工厂，in_progress，正式 Gate 尚未通过**。

| 要了解什么 | 当前文档 |
|---|---|
| 用户需求与完成标准 | [产品需求](docs/PRODUCT_REQUIREMENTS.md) |
| 技术路线、模块、可选后端 | [当前架构](docs/CURRENT_ARCHITECTURE.md) |
| 阶段顺序与依赖 | [产品路线](docs/PRODUCT_PHASES.md) |
| 合并、测试、当前阻塞 | [审核与交付说明](docs/PROJECT_REVIEW.md) |
| 新 Codex 接手 | [START_HERE_CODEX.md](START_HERE_CODEX.md) |
| 专题与维护规则 | [文档索引](docs/README.md) |

## 生产主链

```text
主题 / 工程素材 / 授权参考视频
→ 事实与权利核验 → 脚本 / 分镜 / 技术视觉
→ TTS / 字幕 / 实测语音 cue
→ Remotion + FFmpeg → MP4 + 质量报告 + 审阅包
→ Jovi 审核 → 条件齐全后进入阶段 Gate
```

SQLite 保存 Job、事件、阶段尝试和产物身份。主题/参考任务、取消重试、技术画面、网页产品演示、旁白完整性和审阅合同已有实现；单条候选或代码测试不能代替整阶段验收。

剪映是可选编辑交付层；DaVinci MCP 尚处兼容性试验，真实本机剪辑导出未证明。后续飞书、网页/App 入口复用现有生产链。

## 历史和维护

旧过程文档已归纳，完整版本从 [archive/pre-cleanup-20261023](https://github.com/Jovifei/OpenClaw_VideoFactory/tree/archive/pre-cleanup-20261023) 按原路径查回。运行证据、权利、测试夹具、许可证按依赖保留。详见 [维护规则](docs/MAINTENANCE.md)。
