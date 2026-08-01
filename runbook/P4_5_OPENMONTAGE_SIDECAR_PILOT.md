# P4.5 — OpenMontage Sidecar Pilot

## Gate

只有主系统 P1–P4 已稳定，并且用户明确批准实验环境和许可证评估后才可开始。

## 部署边界

`external/OpenMontage`、独立 Python venv、独立 Node 依赖、独立 `.env`；不接生产 Cron、不读取生产 Secret、不写主状态库。

## 只允许的 Pilot

- 一条 30 秒视频；零 API Key 或免费开放素材路线优先；
- 不下载本地视频模型，不使用真实客户或公司数据，不接抖音发布；
- 最终产物通过 VideoFactory artifact importer 进入统一质量门禁。

## 重点评估

Pipeline Manifest、Stage Director、Provider 评分、预算治理、Pre-compose Gate、Post-render Review、Backlot 可视化、参考视频分析质量、Windows 稳定性、依赖维护成本及 AGPL 产品化影响。

## 成功条件

仅当创意质量、素材检索、参考视频概念验证、质量审计或成本透明度显著优于主链时保留。不得因功能数量或 Star 数量直接纳入生产。
