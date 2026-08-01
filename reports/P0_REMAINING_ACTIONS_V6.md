# P0 Remaining Actions V6

Status: `conditional_not_passed`. 008 round: `READY_FOR_REAL_CHANNEL_SEQUENCE`.

1. **User real-Channel sequence (R0-R5)** - PRIMARY. Send `P0_TEXT_ROUTER_TEST` (R0), then upload one fixture at a time (R1 TXT, R2 PNG ingress, R3 PNG analysis, R4 audio, R5 MP4), awaiting confirmation between each. This is the only path to unblock the real-Channel qualification and refresh the V2.5 Feishu evidence files.
2. **Real lark-cli outbound** - requires user authorization for an actual send (Markdown/PNG/TXT/MP4+cover). Dry-run evidence is captured; actual egress is `blocked_user_authorization_required`.
3. **ffmpeg PATH** - add `C:\ffmpeg\bin` to the system PATH in a maintenance window (or run the Gate with PATH augmented). The analyzer runtime works (uses absolute path); only the Gate's direct `ffmpeg -version` check fails. Not a P0 architecture blocker.
4. **SHA256SUMS.txt refresh** - regenerate after the 007/008 file additions (conditional; authorized separate step).
5. **OPENCLAW_EXISTING_AGENTS_REGRESSION.json V2.5 refresh** - update to reflect the 17-agent state (007 `verify_007_invariants.py` already proves the invariants).
6. **Codex CLI upgrade + smoke** - `DEFERRED_BY_USER_UNTIL_MAINTENANCE_WINDOW` (not faked as passed).
7. **Analyzer agent-exec gap** (finding) - the 3 analyzer agents have `exec.mode=deny`; production agent-level execution needs a deterministic analysis MCP tool (transcribe_audio, probe_video, analyze_image) OR the `image` tool allowed for the image analyzer OR the stored copy passed inline to the spawned session. P1 refinement / potential corrective CR. The real-Channel R3/R4/R5 tests will reveal whether the current path completes analysis end-to-end.
8. **`<target-id>` change tracking** - if the VideoFactory Feishu group is migrated, the `tools.media.*.scope` keyPrefix must be updated (P1 runbook item).
9. **P0 Gate** - run the final P0 Gate only when every required real-chain item (R0-R5 + real egress) is independently complete. Not done this round (prohibited).

No commit/tag/push, no PROJECT_STATUS update, no P1 work, no model download.
