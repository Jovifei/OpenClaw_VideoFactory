# 00 — 执行总览

## 阶段依赖

```text
PACKAGE → P0 → P1 → P2 → P3 → P4 → P5 → PRODUCTION
                    └→ P1.5 (optional)      └→ P4.5 (optional)
```

- PACKAGE：交付包结构和静态校验。
- P0：机器、OpenClaw、飞书、受控 lark-cli、Direct Codex CLI smoke 和权限。
- P1：人工主题到稳定MP4的确定性MVP。
- P1.5：P1 后可选的 Video Use 已有素材剪辑适配 Pilot，不阻塞 P2。
- P2：每日选题、飞书选择、12:00自动兜底和Cron。
- P3：4070S、ComfyUI、Whisper、NVENC。
- P4：参考视频分析和原创再创作。
- P4.5：P4 后可选的 OpenMontage 隔离 sidecar Pilot，不阻塞 P5。
- P5：可选剪映草稿。
- PRODUCTION：七天试运行后长期运行。

任何阶段失败，后续保持blocked。

上述 blocked 规则只适用于核心阶段依赖；P1.5 和 P4.5 是故障隔离的可选支线，其失败不阻塞主路线。

## Git与证据

推荐分支：`phase/p0-gate-correction`、`phase/p1-deterministic-mvp`、`phase/p2-topic-automation`、`phase/p3-gpu`、`phase/p4-reference-video`、`phase/p5-jianying`。

每阶段必须记录：任务ID、日期、Git commit、版本、命令、退出码、测试、日志、产物、限制、回滚和用户动作。禁止只写“完成”。

## 用户介入点

飞书授权、管理员权限、OpenClaw升级、驱动安装、模型下载、权限扩大、许可证疑问、超预算、剪映版本切换、抖音发布必须停下等用户。OpenClaw Codex Plugin OAuth 是 P1.5 以后可选研究，不得作为 P0 用户介入点。

## 回退链

```text
研究失败→换题
TTS失败→备用TTS
Whisper CUDA失败→CPU
ComfyUI视频失败→静态图
ComfyUI图片失败→SVG/Remotion
NVENC失败→CPU编码
角色失败→静态签名/不主动出场
剪映失败→MP4正常交付
飞书母版过大→预览版+本地路径
```
