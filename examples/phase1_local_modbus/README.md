# Phase 1 本地 Modbus 样例

该样例只使用本地已核验的事实卡，通过 `generate_video.py --local-brief`
进入现有 `video_factory` 渲染链。它不调用 Provider、网络、飞书或自动发布。

```powershell
& 'C:\Users\Admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe' `
  generate_video.py --local-brief examples/phase1_local_modbus/brief.json
```

输出位于 `dist/phase1_local/phase1_dee7aff68f9b03af/`，状态为
`pending_review` 时仍需 Jovi 人工审阅，不能视为自动发布许可或完整 Phase 1 通过。
