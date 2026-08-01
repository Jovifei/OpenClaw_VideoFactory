# P0-013 Fake Two-Message Smoke

The fake smoke creates a PNG attachment event, writes a quarantined receipt and route-binding digest, then sends a second text event with `reply_to_message_id` targeting that attachment. `create_analysis_request` returns `pending`; `analyze_image` reads only the quarantined copy and completes once. The test observes one analyzer runner call, unchanged ingress fields, and a completed request record. A second request returns `already_completed`; a standalone text event and an Analyzer call without a request are rejected.

Evidence: `tests/test_two_message_flow.py`, 2/2 passed. This is not live Feishu evidence and does not include a real message ID, real Reply metadata, or a real model/GPU call.
