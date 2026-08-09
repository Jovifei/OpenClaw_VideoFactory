# PINK-PIG-FACTORY-RENDER-HARDENING-002

## 1. 完成事项

- 重新加载并执行 `skills/pink-pig-mascot-director/SKILL.md`，并在知识视频配置中启用 `mascot.mode: required`。
- 保留五张独立的 Modbus RTU 小粉猪知识插图，不再用单张猪图重复覆盖全片。
- 修复字幕根因：SRT/libass 使用 384×288 虚拟画布，原始 44/250 配置被放大并将字幕推到顶部；渲染器现在把最终 1080×1920 像素合同转换为 libass 坐标。
- 字幕固定在底部粉色安全区，最终字号约 44px，左右留白 90px，最多两行；交叉淡化期间字幕 cue 不叠加。
- 配置提供 `mascot.mode` 开关：`required`、`optional`、`off`；本次知识视频使用 `required`。
- 配置启用 `tts_with_offline_fallback`。本次实际使用 Edge TTS（输出 `audio_mode: tts`）；TTS 失败时才回退本地 BGM，并记录原因。
- 对 legacy/BGM 配置增加显式 `audio_normalize: true`，用 FFmpeg `loudnorm` 修复“有音轨但听不见”的情况。

## 2. 修改文件

- `video_factory/pipeline/renderer.py` — 字幕安全区、libass 坐标换算、音频增益参数。
- `video_factory/pipeline/renderer.py` — 增加可选 `loudnorm` 响度归一化。
- `video_factory/pipeline/subtitle.py` — 两行限制和 cue 去重叠。
- `video_factory/pipeline/mascot.py` — Pink Pig skill/style profile 安全加载与开关。
- `generate_video.py` — legacy config 接入 mascot、TTS fallback、字幕样式和音频增益。
- `schemas/video/video_job.schema.json` — mascot、subtitle style、audio gain 合同字段。
- `examples/modbus_rtu_illustrations/config.yaml`、`script.txt` — 知识视频安全配置与短字幕。
- `video_factory/README.md`、`.gitignore`、`tasks/todo.md` — 使用说明、跟踪例外和任务记录。
- `tests/video/test_mascot_and_subtitle.py` — skill 开关、字幕坐标换算、换场不叠字幕、音频增益和响度归一化测试。

## 3. 测试结果

定向测试：

```text
tests/video/test_mascot_and_subtitle.py
tests/video/test_render_contract.py
tests/video/test_director_topic_pipeline.py
20 passed (before the final audio-normalization assertion); the final
renderer-focused suite `test_mascot_and_subtitle.py` passed 8/8.
```

完整回归：

```text
python -m pytest tests/video -q       -> 259 passed
python -m pytest video_factory/tests -q -> 5 passed
python generate_video.py --config examples/pink_pig_demo/config.yaml -> exit 0
```

`git diff --check` 通过；未执行 commit、push、reset、clean，也未修改
OpenClaw、Feishu、Gateway、Binding、OAuth、Cron 或 `PROJECT_STATUS.yaml`。

## 4. 重制媒体证据

输出：`dist/modbus_rtu_illustrations.mp4`

- 五个独立画面，时长 23.400 秒。
- H.264，1080×1920，30 fps。
- AAC，24 kHz，单声道，23.381 秒；legacy demo 为 AAC 48 kHz。
- FFmpeg 完整解码退出码 0。
- 独立 `volumedetect`：Modbus 重制片 `mean_volume=-18.7 dB`、`max_volume=-1.6 dB`；legacy demo `mean_volume=-17.3 dB`、`max_volume=-10.7 dB`，不再是之前约 `-45.5 dB` 的近静音 BGM。
- 抽帧检查 `dist/qa_frames/frame_2_fixed.png`、`frame_8_fixed.png`、`frame_14_fixed2.png`：字幕位于底部粉色安全带，未覆盖中间插图；交叉淡化时仅显示一条字幕。
- 字幕文件：`dist/modbus_rtu_illustrations.srt`，5 个 cue，均不重叠。

## 5. Git ignore 跟踪验证

```text
git check-ignore -- docs/PINK_PIG_PHASE1_ARCHITECTURE.md -> exit 1
git check-ignore -- reports/PINK_PIG_FACTORY_RENDER_HARDENING_002.md -> exit 1
```

两份文件均可被 Git 发现；已有 ignore 规则未删除或重排。

## 6. 剩余债务

- 16:9 技术插图在 9:16 画布中仍保留上下粉色留白；若需要满屏竖版构图，应单独生成竖版 shot，不裁切当前知识图。
- 字幕的像素级遮挡检测尚未自动化，目前由安全区合同、两行限制和抽帧验收保证。
- TTS 依赖本机 Edge TTS；网络或 provider 不可用时使用 BGM fallback，不宣称已生成真人旁白。
- 本次仍是本地 Video Factory 渲染；不进入 Feishu/004、自动运营/005 或正式 P0/P1 Gate。

PINK_PIG_FACTORY_RENDER_HARDENING_002_COMPLETE
