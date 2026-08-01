# P0 Core Feishu Control Tests 032

Status: `PARTIAL_STATIC_AND_SHADOW_SUBSTRATE`; final qualification blocked.

| # | Check | Result |
|---:|---|---|
| 1 | OpenClaw version 2026.7.1 | PASS |
| 2 | Feishu package version recorded | PASS (2026.6.6) |
| 3 | gateway run help | PASS |
| 4 | gateway health command | PASS |
| 5 | gateway call command | PASS |
| 6 | channels.stop RPC | PASS (static) |
| 7 | channels.start RPC | PASS (static) |
| 8 | accountId in stop/start schema | PASS (static) |
| 9 | stop target scope | PASS (static) |
| 10 | stop aborts selected runtime | PASS (static) |
| 11 | stop waits for task | PASS (static) |
| 12 | stop writes no config | PASS (static) |
| 13 | Feishu receives abort signal | PASS (static) |
| 14 | WebSocket abort closes client | PASS (static) |
| 15 | WebSocket client removed | PASS (static) |
| 16 | Feishu reload is whole-channel | PASS (static) |
| 17 | channels remove mutates enabled | PASS (static) |
| 18 | plugin disable broader than account | PASS (scope review) |
| 19 | fake markers only | PASS |
| 20 | Shadow config validate | PASS (exit 0) |
| 21 | Shadow loopback port | PASS (19432) |
| 22 | Shadow Gateway health | PASS (exit 0) |
| 23 | Shadow state separation | PASS |
| 24 | Shadow Feishu plugin loaded | BLOCKED |
| 25 | Shadow Feishu channel status | BLOCKED |
| 26 | Shadow account stop | NOT RUN |
| 27 | Shadow account restore | NOT RUN |
| 28 | Shadow WebSocket cleanup | NOT PROVEN |
| 29 | Shadow consumer zero/one | NOT PROVEN |
| 30 | Independent control review | PASS (static review; runtime acceptance blocked) |
| 31 | Full Python suite | PASS (240/240) |
| 32 | Full Pester suite | PASS (101/101) |
| 33 | Schema suite | PASS (88/88) |
| 34 | Project venv `pip check` | PASS |
| 35 | `git diff --check` | PASS |
| 36 | Full legacy handoff scan | FAIL-BASELINE (130 pre-existing vendor/generated hits) |
| 37 | 032 changed-scope secret pattern scan | PASS (0 hits) |

No production command, Feishu message, attachment, card, configuration write,
commit, push, or tag was executed.
