# P0 Media Root Walk Fix

Status: **fixed and verified**.

The real TXT parameters were correct: the Channel media path and script `SourcePath` are the same E-drive file beneath `media/inbound`; no C-drive/E-drive root mismatch occurred.

`Test-PathWithinRoot` now normalizes both inputs and accepts only exact root equality or a separator-bounded descendant with Windows case-insensitive comparison. `Assert-NoReparseEscape` independently proves that membership, checks the source item and every ancestor including `AllowedRoot`, walks through `FileInfo.Directory` and `DirectoryInfo.Parent`, and returns only when the exact allowed root is reached.

PowerShell parsing passed. All 32 Pester tests passed: the original 28 plus four root-walk regressions. The source-item reparse case uses a directory junction and the actual function definitions loaded from the script, so it does not require administrator-only file symbolic-link privileges.

The same real TXT source was then ingested using the original `message_id`, Channel path, and allowed root. Its source, fixture, and stored SHA-256 values match. The receipt records `content_parsed=false` and `quarantined=true`. Repeating the same call returned idempotent success, kept one original, and did not change the receipt.

OpenClaw configuration SHA-256 remained `c7098b2238c8c2816d96d724b39fe5d43e135445034331e574ea2a1cb2c5660d`. Secret scanning passed. No PNG/MP4 real ingress, lark-cli, P0 Gate, P1, OAuth, Runtime, model, Binding, Gateway, or Cron action occurred.
