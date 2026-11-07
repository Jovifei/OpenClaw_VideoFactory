# 推荐安装顺序（Phase 1 本地优先）

本文件只定义未来批准后的安装顺序；本次产品阶段对齐不授权安装任何工具、模型或 Skill。

## 第一批：Phase 1 本地成片基线

1. Python、Node、Git、FFmpeg/ffprobe 和现有 NVIDIA 驱动。
2. 本项目本地 Skill 与 `video_factory` 的可复现依赖。
3. Remotion 官方 Skill（经过独立 source/license review 与明确授权后）。
4. 稳定 AI TTS、字幕和本地 job 工件合同。
5. 小粉飞猪最小资产包、FFmpeg/NVENC 与 CPU 回退。
6. 用户主题和用户本地参考视频的安全输入/原创边界。

这一批不配置飞书、不安装 lark-cli、不修改 OpenClaw、不注册 Cron、不自动下载模型。

## 第二批：Phase 1 可选已有素材适配

在基础本地成片稳定后，评估 PySceneDetect、faster-whisper、词级字幕与 Video Use
方法。原始素材只读，禁止默认使用 Cookie、下载器或第三方账号。

## 第三批：Phase 2 飞书安全与自动化

1. OpenClaw、飞书官方 `larksuite/cli`、最小权限机器人身份和目标会话 allowlist。
2. 单消费者、隔离 receipt、MIME/SHA、两消息分析意图、入站/出站幂等验证。
3. 非定时选题卡、自然语言选择、12:00 fallback、取消/恢复。
4. 通过 Phase 2 Gate 后才可注册生产 Cron。

## 第四批：Phase 3 GPU 增强

1. 自动发现既有 ComfyUI。
2. 经批准的 comfyui-mcp 或其他受控适配器。
3. 封面与背景图白名单 workflow、Real-ESRGAN、GPU 串行队列与 OOM 回退。
4. 在 30GB 新增模型总预算内锁定模型版本和哈希。

## 第五批：Phase 4 高级参考视频

1. 高级转录、切镜、关键帧与原创性检查。
2. 只有 Phase 2 已通过安全入站后，才评估飞书附件；否则只接 Jovi 提供的本地文件。
3. 风格参数、版权与相似度门禁。

## 第六批：Phase 5 剪映草稿与实验

优先评估 CapCut Mate API；只有确实需要本机剪映特效和自动导出时，才单独评估
`jianying-editor-skill`。剪映故障不得影响 MP4 主成片。OpenMontage 等实验只在隔离
环境运行；平台爬虫不进入默认流程。
