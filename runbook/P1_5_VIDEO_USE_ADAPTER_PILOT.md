# P1.5 — Video Use Adapter Pilot

## Gate

只有 P1 已通过且三条确定性主题成片验收完成后才可开始。

## 目标

将已有素材剪辑能力加入为独立支线，不改变主题生成主链。

## 执行顺序

1. 只读审查仓库、许可证和 commit。
2. 提炼数据合同：source inventory、word transcript、packed transcript、EDL、rendered output、self-review report。
3. 用 faster-whisper CUDA 替换强制 ElevenLabs 依赖。
4. 实现中文字幕分块。
5. 适配 30 FPS 和 NVENC。
6. 输出只能进入当前 job 目录。
7. 统一经过 VideoFactory 质量门禁。
8. 运行口播、屏幕录制、多 take 三类素材 Pilot。
9. 与手工剪辑耗时、错误和人工修改分钟数比较。

## 强制规则

- 不在词中切断；30–200ms 切点 padding；每个片段边界 30ms 音频淡入淡出；
- 字幕最后烧录；转录缓存；最多三轮自动修复；
- 原始素材只读；失败不影响主题生成主链。

## 成功条件

三种素材均成功，无明显音频爆音或词中切断；中文字幕安全；NVENC/CPU 均可；人工修改时间明显降低；故障不阻塞主流水线。
