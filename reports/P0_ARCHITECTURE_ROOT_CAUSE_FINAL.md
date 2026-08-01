# Final root cause

The failure is not in the Analyzer, MCP, model, or GPU. The current core Feishu Binding normalizes source events before this project can deterministically verify raw event type, card action, operator, chat, action value, callback identity, reply target, or command message identity. A post-Binding prompt, command, Reply heuristic, synthetic card command, or `inbound_claim` cannot recreate those facts.

P0-018 therefore closes those routes and changes only the Channel boundary decision. Existing ingress, receipts, Analyzer contracts, GPU locking, and multimodal routing are retained.
