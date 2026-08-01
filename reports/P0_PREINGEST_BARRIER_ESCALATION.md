# P0 pre-ingest barrier escalation

Required response: `GLOBAL_CHANGE_APPROVAL_REQUIRED`

## Why this cannot be a project-only change

The first executable attachment-processing decision occurs in the installed OpenClaw core, before the project script. Its `get-reply-CknL88Yv.js` reply path calls `applyMediaUnderstandingIfNeeded` when `hasInboundMediaForUnderstanding` detects the Channel-supplied media fields. The project has no active pre-agent handler. OpenClaw's supported solution is the `inbound_claim` plugin hook; it carries `metadata.mediaPath`, `metadata.mediaPaths`, `metadata.mediaType`, `metadata.mediaTypes`, `messageId`, `senderId`, `conversationId`, and the resolved `agentId` before agent routing.

Workspace plugins live under `<workspace>/.openclaw/extensions`, but the installed documentation states that workspace-origin plugins are disabled by default. This host has an exclusive global `plugins.allow` list and no enabled `hooks` section. Therefore activation requires changing `C:\Users\Admin\.openclaw\openclaw.json` and restarting the Gateway. Both are explicitly prohibited in the current authorization.

## Exact proposed change (not applied)

Files to add under the project:

```text
E:\project\OpenClaw_VideoFactory\.openclaw\extensions\video-factory-preingest-barrier\package.json
E:\project\OpenClaw_VideoFactory\.openclaw\extensions\video-factory-preingest-barrier\openclaw.plugin.json
E:\project\OpenClaw_VideoFactory\.openclaw\extensions\video-factory-preingest-barrier\index.mjs
E:\project\OpenClaw_VideoFactory\tests\Test-PreIngestModelBarrier.ps1
```

Required global configuration patch:

```diff
--- C:\Users\Admin\.openclaw\openclaw.json
+++ C:\Users\Admin\.openclaw\openclaw.json
@@ plugins.allow
   "codex",
-  "tavily"
+  "tavily",
+  "video-factory-preingest-barrier"
@@ plugins.entries
+"video-factory-preingest-barrier": {
+  "enabled": true,
+  "config": {
+    "agentId": "video-factory",
+    "channel": "feishu",
+    "chatId": "<DEDICATED_GROUP_ID_FROM_EXISTING_CONFIG>",
+    "projectRoot": "E:\\project\\OpenClaw_VideoFactory",
+    "inboundRoot": "E:\\project\\OpenClaw_VideoFactory\\media\\inbound",
+    "maxBytes": 5242880
+  }
+}
```

Required plugin behavior, expressed as an exact contract for `index.mjs`:

```javascript
api.on("inbound_claim", async (event, ctx) => {
  const media = event.metadata ?? {};
  if (ctx.agentId !== "video-factory" || event.channel !== "feishu" ||
      event.conversationId !== config.chatId) return;
  const paths = Array.isArray(media.mediaPaths)
    ? media.mediaPaths.filter((value) => typeof value === "string" && value.length > 0)
    : typeof media.mediaPath === "string" ? [media.mediaPath] : [];
  if (paths.length === 0) return; // ordinary text-only chat reaches the model
  if (paths.length !== 1) return { handled: true, reply: { text: '{"error_code":"unsupported_attachment_count"}' } };
  // Use the one Channel-provided MediaPath verbatim. Never rebuild it from a name.
  // Obtain only the Channel-provided filename/type metadata; fail closed if absent.
  // Invoke scripts/07_ingest_inbound_media.ps1 through a fixed executable and argument array.
  // Pass MessageId, AccountId, ChatId, SenderId, ContentType, InboundRoot and ProjectRoot literally.
  // Return { handled: true, reply: { text: "TXT_INGRESS_OK|PNG_INGRESS_OK|MP4_INGRESS_OK" } }
  // only after success; otherwise return a structured failure code with no body/path/secret.
});
```

The implementation must use `definePluginEntry`, a manifest with `id: "video-factory-preingest-barrier"` and `activation.onStartup: true`, a fixed `powershell.exe -NoProfile -NonInteractive -File` argument array, bounded timeout, JSON-only script result handling, and no shell interpolation. It must reject missing Channel filename metadata rather than guessing from a staged path. It must not read, OCR, decode, transcribe, summarize, or forward attachment content.

## Impact and rollback

Impact is limited by the exact `agentId`, Channel and group checks above. The plugin must return `undefined` for all other agents, groups and text-only messages. Its only external effect is a deterministic call to the existing ingest script for one attachment on the dedicated group. It does not change models, runtimes, OAuth, bindings, bot identity, Cron, lark-cli, P1, or OpenClaw core/channel source.

Rollback is one validated reverse patch: disable and remove `plugins.entries.video-factory-preingest-barrier`, remove its id from `plugins.allow`, restart the Gateway, then remove only the three plugin files. Do not remove historical PNG/TXT evidence or receipts.

## Required approval boundary

Approval must explicitly authorize the three project plugin files, the one global config patch above, one Gateway restart, and the focused barrier tests. Without that exact approval, no plugin source, config, or restart may be performed.
