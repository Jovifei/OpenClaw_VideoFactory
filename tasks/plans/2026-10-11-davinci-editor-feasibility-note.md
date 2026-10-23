# DaVinci Resolve MCP — optional editor feasibility note

**Status:** candidate only; implementation deferred pending Phase 1 closure and
a locally available, versioned Resolve installation.

**Remote review:** OpenClaw_VideoFactory ChatGPT Project, iteration 43, accepted
DaVinci Resolve MCP as a candidate for the optional Jianying manual-edit
branch. It did not authorize installation, routing changes or an adapter spike.

## Decision

DaVinci Resolve MCP is a credible candidate to evaluate for structured editing
and project automation. The available evidence does not prove that it is faster
than Jianying for this project. Its upstream documentation describes generated
edits as a first-pass assembly that still needs editorial work and judgment.

Keep the Phase 1 production contract as:

```text
mandatory: verified inputs → Remotion/FFmpeg → local MP4 + quality report + review package
optional: validated render artifacts → one editable editor backend → Jovi manual review
```

DaVinci may later replace Jianying in the optional branch for a particular
job. It must not replace the deterministic renderer, SQLite job authority,
source-bound script/audio contracts or current Phase 1 Gate. Only one editor
backend may control a given job.

## GitHub evidence checked 2026-10-11

| Candidate | Evidence | Assessment |
|---|---|---|
| [`samuelgursky/davinci-resolve-mcp`](https://github.com/samuelgursky/davinci-resolve-mcp) | MIT; upstream release `v4.10.4` published 2026-10-10; README reports 37 compound tools, 389 granular tools, 136 guarded workflow actions and 338 live-tested API methods across specific Resolve builds. The installer lists Codex CLI support. | Strongest primary candidate for a later compatibility pilot. The repository’s own “What this does not do” section says an AI assembly is a first pass, not a finished cut. Live test coverage is not complete for every API method or every Resolve version. |
| [`apvlv/davinci-resolve-mcp`](https://github.com/apvlv/davinci-resolve-mcp) | Smaller MIT server; exposes basic project/timeline/media/Fusion operations and generic Python/Lua execution. | Not preferred: less structured editing evidence and broad code-execution tools need a stricter security review. |
| [`Tooflex/davinci-resolve-mcp`](https://github.com/Tooflex/davinci-resolve-mcp) | Small MIT implementation; Windows launcher and Python 3.10/3.11 constraints documented. | Useful comparison only; lower project activity/validation evidence than the primary candidate. |

Codex has MCP server support through its local MCP configuration. The candidate
upstream explicitly lists Codex CLI in its current installer documentation.

The primary repository documents important limits:

- Resolve must be installed and running for the live scripting server.
- External scripting is a Studio feature. The Free in-app bridge is
  version-dependent; upstream reports that Free 21.1 no longer lists Python
  scripts in the Workspace Scripts menu. Use a verified Studio setup for a
  reliable pilot unless that behavior is requalified on the exact local build.
- The current public API lacks some fine-grained edit operations. Its edit
  kernel blocks partial range trims where Resolve exposes no razor/split
  primitive; tool coverage must be checked against the desired cut operations.
- The MCP can arrange a first pass and provide tools/analysis; the human still
  judges whether the cut is good.
- Keep the default local stdio transport and guarded compound tools. Do not
  enable the separate offline project-file/DB editing server for this pilot;
  it could bypass the project’s SQLite stage authority and artifact checks.

## Local prerequisite status

Read-only checks on 2026-10-11 did not find Resolve in the standard C:/E:
Program Files locations, the Windows uninstall registry, or the running
process list. Custom install locations were not exhaustively searched. Resolve
edition/version and any license are therefore **unknown**. No software was
installed and no MCP settings were changed.

This means the claimed editing speed benefit remains unmeasured. A meaningful
comparison requires Resolve and the current Jianying workflow to both be
available, then timing the same bounded edit operations on the same disposable
assets.

## Bounded evaluation stages

### Stage A — compatibility evidence

Run only after a locally supported Resolve edition/version is available and a
separate remote plan authorizes the check. Use a disposable project and
synthetic media. Verify connection/version, project and timeline readback,
capabilities, Codex MCP startup, shutdown/recovery, and whether the supported
API can represent this project’s video, voiceover, subtitle and frame-exact
timing inputs. Do not use a production job or candidate.

### Stage B — optional adapter proof

Only after Stage A review and a separate Change Request: test one disposable
optional editor job using the existing visual-only render, timing manifest,
voice clips and subtitle assets. Keep the existing Phase 1 MP4/review package
authoritative. Record Resolve project identity, tool actions, timeline readback,
input/output hashes, export metadata and full-decode/quality evidence. A Resolve
failure must leave the existing Phase 1 deliverable unchanged.

### Stage C — human comparison

On equivalent disposable or already approved review inputs, compare Jianying
and Resolve on assembly time, subtitle/timing fidelity, transitions,
reproducibility, recoverability and evidence capture. Preserve Jovi’s visual
and listening review. Claim “faster” only if measured end-to-end comparison
supports it; MCP call counts alone are not a speed result.

## Keep-or-reject criteria

Keep Resolve as an optional candidate only if a local supported build can run
the required actions reliably, produce a recoverable project/edit artifact,
preserve the timing/media hash lineage, pass the existing local media gates,
leave the mandatory renderer path unaffected, and show a measurable workflow
benefit. Reject or defer it if it depends on unreliable GUI-only steps, cannot
produce reproducible outputs/audit evidence, lacks required timeline operations,
or becomes a hidden Phase 1 dependency.

## Current blockers and next action

- Phase 1 Gate-critical topic/lifecycle/reference evidence remains the main
  project priority.
- No local Resolve installation was detected in standard locations.
- I2C is independently blocked by MPT approved-credential unavailability; the
  exact Jianying pin is also unavailable. DaVinci research does not resolve the
  MPT block.
- Add DaVinci to the deferred candidate list only. Revisit the compatibility
  pilot after Phase 1 closure pressure decreases and the Resolve installation
  prerequisite is available. Obtain a separate remote plan/Change Request
  before installation, MCP registration, or any project mutation.
