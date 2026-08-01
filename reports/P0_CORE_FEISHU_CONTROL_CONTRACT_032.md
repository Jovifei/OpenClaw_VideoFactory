# P0 Core Feishu Control Contract 032

## Final status

`CORE_FEISHU_SHADOW_VALIDATION_BLOCKED`

The exact control contract is resolved at the installed-source layer but is not
qualified for production because the no-network Shadow could not load Feishu.

## Resolved command shape (not executed on production)

```text
openclaw gateway call channels.stop --params '{"channel":"feishu","accountId":"zhongshu"}' --json
openclaw channels status --channel feishu --json
openclaw gateway call channels.start --params '{"channel":"feishu","accountId":"zhongshu"}' --json
openclaw channels status --channel feishu --json
```

This is account-runtime control, not configuration disable. `channels remove`,
`plugins disable`, and `gateway stop` are not substitutes because they operate
on broader scopes or mutate shared configuration.

## Qualification gate

A future isolated run must show Feishu loaded, zhongshu runtime active without
real transport, target stop with runtime false/consumer zero, WebSocket cleanup,
target restore, and non-target state unchanged. Required command-level scripts
remain uncreated until that gate passes.

No production action, real Feishu request, message, card, attachment,
configuration mutation, commit, push, or tag occurred.
