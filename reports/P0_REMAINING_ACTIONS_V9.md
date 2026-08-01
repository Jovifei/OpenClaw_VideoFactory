# P0 Remaining Actions V9

1. Jovi must authorize the exact deterministic command adapter/source and the exact code write scope. The source must provide the original Feishu `command_message_id`, `chat_id`, and `sender_id`; model-rewritten text is not acceptable.
2. After authorization, implement and test the pending-intent contract, atomic one-shot consume, cancel/status, independent analysis request, and Analyzer gate.
3. Verify the supported runtime registration path and its minimal configuration diff. Do not add a Feishu Binding or consumer.
4. Run the approved offline and fake smoke tests, then stop for Jovi's real `/analyze-next image` command. No real attachment should be uploaded before the armed token is proven.
5. Keep the old R3 FAIL, do not run R4/R5 or the final P0 Gate, and do not enter P1 until all user-gated live evidence passes.
