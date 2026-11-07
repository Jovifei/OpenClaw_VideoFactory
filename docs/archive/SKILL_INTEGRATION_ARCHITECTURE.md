# Skill 集成架构 V2

## 为什么拆成细粒度 Skill

“一键视频 Skill”适合演示，但无人值守生产需要：

- 每个阶段可重试；
- 中间结果可查看；
- 某个模型失败时可回退；
- 参考视频不能污染系统指令；
- 剪映故障不影响 MP4 成片；
- Codex 改模板时不能接管日常状态。

因此分阶段保持唯一事实来源：**Phase 1** 使用 job-scoped 本地工件和渲染报告，
不依赖 OpenClaw；**Phase 2** 才由 OpenClaw 保持每日任务、飞书消息、重试、
取消、恢复和通知的唯一长期状态。各 Skill 只完成自己的阶段。

Phase 1 的入口可以是 Jovi 主题、本地参考视频主题分析或 Jovi 明确授权的公开
主题研究。参考视频的主题提取不调用飞书，也不允许自动抓取受限平台；高级风格
再创作仍属于后续 Phase 4。

## 任务成果契约

Phase 1 的每个本地视频目录至少包含：

```text
topic_card.json
research.md
sources.json
script.json
storyboard.json
style_tokens.json
asset_manifest.json
voice.wav
captions.json
captions.srt
render_manifest.json
final.mp4
cover.png
publish_info.md
quality_report.json
```

可选：

```text
jianying_draft/
reference_report.json
reference_style.json
codex_change_report.md
```

## GPU 预算

4070 SUPER 默认规则：

- 同时只运行一个重 GPU 任务；
- Whisper 和 ComfyUI 不并发；
- AI 图片优先 1024 级别，再裁切/放大到竖屏；
- AI 视频只生成 2～4 秒片段；
- OOM 后降低分辨率、帧数或切换到静态图；
- 最终 H.264 使用 NVENC；
- 技术图使用 SVG/Canvas/HTML，不浪费扩散模型显存。

## 剪映边界

主产品是：

- 可播放的 `final.mp4`；
- 可编辑的字幕、音频和素材；
- 可选的剪映草稿。

剪映不是唯一渲染器。版本变化、弹窗或草稿格式变化时，视频仍然能按时完成。


## 角色系统

在 `script-storyboard-director` 产出结构化分镜后，`pink-pig-mascot-director` 负责：

- 判断本条视频是否适合加入小粉猪；
- 选择出场模式；
- 生成角色资产引用或选择已存在资产；
- 将角色摆放、尺寸和层级写入渲染合同；
- 在内容拥挤时降级为角标或不使用。
