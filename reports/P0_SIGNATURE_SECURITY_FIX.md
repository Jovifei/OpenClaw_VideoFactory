# P0 Signature Security Fix (024)

Status: `PASS_FAIL_CLOSED`

## Change

Both `ProjectFeishuGateway` and `OfflineFeishuGateway` now default to `verify_signature_required=True`.

- A missing verifier rejects ingress.
- A missing signature rejects ingress.
- A verifier exception rejects ingress.
- A wrong signature rejects ingress.
- Only a supplied verifier returning true allows the event to reach schema validation and de-duplication.

The message and card schemas now require `signature`, making absence invalid at the contract level as well as at the entry guard.

## Verification

| Case | Evidence |
| --- | --- |
| signature missing | `test_signature_is_fail_closed_and_replay_is_rejected` |
| signature wrong | project and offline gateway tests |
| signature correct | project message/card tests |
| replay | processed event becomes `duplicate`; consumed ticket becomes `ticket_invalid` |
| verifier omitted | `test_default_signature_policy_rejects_ingress` |

The production Feishu cryptographic verifier is intentionally not instantiated in this offline task. Its absence is safe: the Gateway rejects rather than warns or continues.
