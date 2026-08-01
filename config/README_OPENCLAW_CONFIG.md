# OpenClaw配置应用规则

`openclaw.fragment.example.json5`不是完整配置，不得直接覆盖用户配置。

Codex必须：备份现有配置；运行`openclaw config schema`；查询字段；读取当前值；生成最小补丁；运行`config validate`和`doctor`；证明Gateway健康；保存补丁和回滚文件到`reports/openclaw_state/`。

飞书Channel优先通过`openclaw channels login --channel feishu`配置，不手写App Secret。
