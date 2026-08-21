# Reference-tool adoption matrix

| Project | Adoption in this branch | Reason |
| --- | --- | --- |
| PySceneDetect 0.7.1 | Direct offline dependency | BSD-3-Clause scene boundaries and deterministic timing |
| faster-whisper 1.2.1 | Optional offline adapter | MIT local ASR only; cached `small`, CPU `int8` |
| Video Analyzer | Clean-room field ideas only | Claude/MCP execution is not part of Phase 1 |
| Scene Scribe | Clean-room report organization only | No project license was found; no code is copied |
| OpenMontage | Gate/workflow ideas only | AGPL pipeline is not vendored or executed |
| Code2MP4 | Contract/data-flow ideas only | Existing renderer remains the single pipeline |
| Auto-Editor, WhisperX, prompt-remix executors | Deferred | Not needed for the conservative local slice |

The branch stores provenance in the wheel lock and Change Request. It does not
download models, invoke remote providers, or reuse reference frames/audio.
