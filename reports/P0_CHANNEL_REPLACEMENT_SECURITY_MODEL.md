# Security model

- Treat all Feishu event fields and attachments as untrusted until channel-side validation.
- Persist replay keys for message and callback identities; never use model text as intent.
- Store only a hash of each 256-bit-or-larger ticket; enforce TTL, single use, uploader/operator match, chat match, attachment SHA, media kind, and fixed action mapping.
- Never place paths, model names, raw media, URLs, base64, or free-form action in card values or Analyzer arguments.
- Card callbacks never enter Router/LLM. Analyzer reads only quarantined paths after a validated `analysis_request`.
- The bridge-only `trusted_from_gateway` mark is assigned after validation and is not accepted from Feishu input.
