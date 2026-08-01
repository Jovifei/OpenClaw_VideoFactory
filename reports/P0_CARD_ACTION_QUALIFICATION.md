# P0 Card Action Qualification

## Result

`MOCK_ONLY_PASS_WITH_PRODUCTION_ADMISSION_BLOCK`

The local experiment supplied an official-SDK-shaped mock `card.action.trigger` event to the existing fail-closed Gateway boundary. It did not import the Feishu SDK, receive a real callback, contact Feishu, call an Analyzer, or enter an LLM path.

| Check | Result |
| --- | --- |
| Attachment ingress produces a ticket | Pass |
| Action is preserved | Pass |
| Operator is present and ticket-bound | Pass |
| Chat is present and ticket-bound | Pass |
| Ticket is consumed and replay rejected | Pass |
| Bounded analysis-request envelope is produced | Pass |
| Direct Analyzer invocation | Not present |

The focused qualification test passed 4/4. It labels this route `MOCK_ONLY`.

## Boundary against HIGH-025A-01

The mock confirms field/ticket preservation. It does **not** supply a real later signed text message or `reply_to_message_id`, and it cannot replace the durable two-message intent protocol. The production admission result is therefore `NOT_QUALIFIED_REPLY_TO_MESSAGE_ID_REQUIRED`; HIGH-025A-01 remains open for migration approval.

## Required real evidence

Only an OpenClaw-created durable `analysis_request` from a signed later text message with actual reply metadata can close this finding. A card action must not become an alternate analysis-intent route.
