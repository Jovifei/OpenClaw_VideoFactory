# Analyzer MCP Tools

`mcp.servers.analyzers` is registered as a fixed stdio server running `scripts/analyzer_mcp.py`. The local Gateway probe reports three tools and no diagnostics.

All tools share exactly six input fields and require a receipt-verified quarantine copy. They reject arbitrary paths, commands, model names, URLs, file keys, base64, output directories, and ffmpeg parameters. Image uses `xiaomimimo/mimo-v2.5` without a text-only fallback; audio uses local faster-whisper CUDA; video uses bounded ffprobe/ffmpeg, audio extraction, transcription, and keyframe analysis. Results are job-scoped and idempotently cached.

This is an offline/local MCP readiness report. R3-R5 real Channel execution remains user-gated.
