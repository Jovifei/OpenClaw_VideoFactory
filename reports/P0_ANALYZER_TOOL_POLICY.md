# Analyzer Tool Policy

The three binding-less analyzers now have one exact server-prefixed MCP allow entry each. Their generic file, process, shell, browser, network, media, and configuration capabilities are denied. The router retains only the ingest path and internal dispatch controls; it does not receive the three analyzer tools directly.

The policy was applied only after offline gates, config dry-runs, and a backup hash check. The post-apply config has 17 agents and 14 bindings; the router model and target-group media scope are unchanged.
