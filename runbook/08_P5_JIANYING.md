# 08 — P5 剪映可编辑草稿

主交付始终是MP4/SRT/WAV/封面/素材/发布文案，剪映只增强。

Codex发现剪映路径、版本、草稿目录和CapCut Mate兼容性，写JIANYING_COMPATIBILITY。

优先CapCut Mate localhost API，备选jianying-editor-skill；一个任务一个后端。

每次新建草稿，不反复改用户已编辑草稿；导入视频、音频、字幕、封面和素材；记录轨道；不默认控制活跃桌面、不自动导出、不自动发布。

失败标记DRAFT_FAILED，但MP4仍PENDING_REVIEW，飞书说明成片可用。P5验收草稿可开、同步、路径有效、失败不阻塞、用户修改不被覆盖。
