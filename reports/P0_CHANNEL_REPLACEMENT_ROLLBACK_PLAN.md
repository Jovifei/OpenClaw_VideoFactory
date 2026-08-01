# Rollback plan

During an authorized maintenance window, stop the project Gateway, restore the backed-up core Binding/configuration, start the prior Gateway, and verify exactly one Feishu consumer plus one reply path. Do not run both consumers concurrently. Preserve event IDs and receipts; do not replay callbacks or re-run Analyzer jobs during rollback.
