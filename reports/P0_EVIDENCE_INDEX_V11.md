# P0 evidence index V11

| Area | Evidence | Result |
|---|---|---|
| 016 authorization/boundary | `reports/change_requests/P0-INBOUND-CLAIM-CARD-ACTION-GATE-016.json` | Read-only; implementation not authorized |
| SDK entry/API | `plugin-entry-R9cUrV0y.d.ts:125-166`; `types-DaHgOqFX.d.ts:12067-12094,12298-12300` | Native plugin and `api.on` exist |
| Hook types | `hook-types-DQ9eTy2x.d.ts:144-235,551-555` | No raw Feishu callback field |
| Hook invocation | `dispatch-V82RCNJs.js:1301-1307,1501-1508` | Only plugin-owned Binding path invokes claim |
| Feishu transformation | `monitor.account-BE_Pfm_n.js:3411-3429,5634-5668` | Callback becomes ordinary synthetic text |
| Config/topology baseline | `reports/P0_CARD_ACTION_BASELINE_BEFORE.json`; `reports/P0_INBOUND_CLAIM_CONFIG_DIFF.json` | SHA/topology unchanged |
| Probe | `reports/P0_CARD_ACTION_PROBE.json/.md` | Not run; gate failed |
| Current offline regression | `reports/P0_INBOUND_CLAIM_CARD_ACTION_TESTS.json/.md` | Python 122/122; Pester 15/15, 46/46, 36/36; V2.8 4/4 + 88/88; MCP 2+3 tools, diagnostics 0 |
| Prior live sequence | `reports/P0_CURRENT_STATUS_V10.md`, `reports/P0_R3_TWO_MESSAGE_EVENT_20260720.json` | R3 old FAIL preserved; R4-R5 not run |

## Evidence classification

The SDK files are local static/runtime evidence. The user's Feishu-admin publication statement is not treated as local callback evidence. No offline or live card-action result is promoted to a pass.
