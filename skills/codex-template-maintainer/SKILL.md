---
name: codex-template-maintainer
description: "Delegate isolated code changes, tests, and renderer maintenance to Codex without handing it daily production state."
version: 0.2.0
metadata:
  openclaw:
    emoji: "🧑‍💻"
---

# Codex template maintainer

Call Codex only for:

- new Remotion template/component;
- Python/TypeScript pipeline defect;
- FFmpeg command repair;
- ComfyUI adapter or workflow schema integration;
- multi-file refactor;
- test creation or deep review.

## Contract

OpenClaw supplies:

- exact repository/worktree;
- allowed files;
- failing job artifact;
- acceptance tests;
- no secrets;
- no publishing permission.

Codex returns:

- patch or commit;
- tests run;
- preview path;
- risks;
- rollback instructions.

OpenClaw remains the owner of job state, retry count, approval, and notification.
