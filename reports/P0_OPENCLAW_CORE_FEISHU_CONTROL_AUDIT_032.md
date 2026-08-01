# P0 OpenClaw Core Feishu Control Audit 032

## Result

`STATIC_CONTROL_METHOD_RESOLVED_SHADOW_VALIDATION_BLOCKED`

Installed OpenClaw is `2026.7.1`. Static inspection resolves a precise
target-scoped runtime control: `channels.stop` with `channel=feishu` and
`accountId=zhongshu`, followed by symmetric `channels.start`. It does not write
configuration. The isolated Shadow Gateway/RPC substrate starts and validates
the redacted fixture, but the Feishu plugin is not loaded (`0 plugins` and no
Feishu channel status). No Shadow Feishu stop/restore or WebSocket cleanup proof
exists, so the method is not promoted to a migration-ready contract.

## Static evidence

| Area | Finding | Proof layer |
|---|---|---|
| CLI | Gateway run/health/call and channel controls exist | installed CLI help |
| RPC schema | `channels.stop`/`channels.start` accept `channel` and optional `accountId` | installed schema |
| Core stop | Core aborts the selected account task, waits, then records stopped runtime | server channel bundle |
| Feishu start | `startAccount` invokes `monitorFeishuProvider` with account abort signal | Feishu channel bundle |
| WebSocket cleanup | abort path calls `close()` and removes the account client | Feishu monitor bundle |
| Reload | `channels.feishu` is a hot prefix that restarts the whole Feishu channel | reload-plan bundle |
| stop hook | Feishu has no separate `stopAccount`; Core abort/wait is the boundary | channel bundle |

Bundle fingerprints (basename only):

- `server-channels-Dr5TYlu-.js` SHA-256 `AFF723303533DD076CBB199D0E978C8D99C70531E9C32B1D1AE1997A9116A62A`
- `channels-hpSo8J3l.js` SHA-256 `D76B5C9310AAB46ABB1F30F328CC56655208883B59657A87EF4F39061097402F`
- `schema-BuOFpc7K.js` SHA-256 `B5B672DD1CE3579E2B030567EF192355374C052934CB4E252B793E08647D54AB`
- `channel-YrfEVd9X.js` SHA-256 `591AB289B89743C8C74E8E105AA5817062D08146219ECDAB2DEBCE7D10D994DE`
- `monitor-vUjP0O1m.js` SHA-256 `6F8A1663B72670C2E9D75D4F36A5FC87799BDFB8AF3229E4873980AB242141E8`
- `monitor.account-BE_Pfm_n.js` SHA-256 `5246B85122D1E9AFA0A95D70AF86171332C8E1D1FEC3703B0DBF450A259CBE40`
- `config-reload-plan-BfztHGEu.js` SHA-256 `68B50D5A3654459F30555F91CC5EA100C8F58808FAA5E675D2A9FBED629B3AFB`

The installed Feishu package reports `2026.6.6`; this is version drift only and
no upgrade was attempted.

## Candidate method decision

| Candidate | Static result | Shadow result | Decision |
|---|---|---|---|
| `ACCOUNT_LEVEL_DISABLE` | exact account-scoped stop/start exists | plugin not loaded | candidate only; blocked |
| `BINDING_LEVEL_DISABLE` | no independent runtime binding stop proven | not run | not selected |
| `CHANNEL_PLUGIN_DISABLE` | affects whole Feishu channel | not run | reject |
| `CONFIG_PATCH_PLUS_GATEWAY_RESTART` | possible but broader | not run | not selected |
| `FULL_GATEWAY_STOP_ONLY` | broad lifecycle only | not run | reject |
| `UNSUPPORTED` | contradicted by source audit | n/a | not applicable |

`channels remove` is not equivalent: it stops the account and writes
`enabled=false`; the Feishu reload prefix then restarts the whole channel.
`plugins disable` and `gateway stop` are broader than the target account.

## Shadow evidence and blocker

- Fixture config validation: exit `0`.
- Shadow Gateway: loopback port `19432` reachable; health CLI exit `0`.
- Feishu transport disabled; no real Feishu request, message, card, credential,
  production PID, log, or lease was used.
- Feishu plugin list and channel status did not expose Feishu; Gateway log said
  `0 plugins`.
- No account stop/restore or consumer-zero/one proof was run.

An earlier plugin-entry experiment emitted an automatic missing-plugin install
diagnostic. That entry was removed, Shadow state was cleared, and no install or
network path is accepted as evidence.

Required next proof is an isolated no-network load of the installed Feishu
plugin with transport still disabled, followed by account stop/start and
redacted runtime checks. Until then the final status is
`CORE_FEISHU_SHADOW_VALIDATION_BLOCKED`.

## Safety boundary

No production configuration, Core Binding, Agent, Cron, Gateway, zhongshu
runtime, OpenClaw secret, real Feishu connection, message, attachment, card,
commit, push, or tag was changed.
