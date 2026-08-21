# AI-DIRECTOR-VIDEO-FACTORY-PHASE2-001

## 1. 完成事项

- Added a compatible Phase 2 planning layer: `DirectorScript`, factual brief,
  deterministic Storyboard assembly, Registry-backed Asset Intelligence, local
  Job State snapshots, and pre/post-render quality reporting.
- Kept `Director.create_storyboard(topic)`, existing `--topic`, `--job`,
  `--config`, Codex CLI adapter, Storyboard Compiler, Composition, Pink Pig
  quality gate, audio/subtitle path, FFmpeg renderer, and `VideoRenderJob` 1.0.
- Added `--topic-file`, `--factual-brief`, and safe `--output-name` handling.
- No second pipeline and no OpenClaw, Feishu, Gateway, Binding, OAuth, Cron,
  database, or formal phase-gate work.

## 2. Compatible interfaces and contracts

- `ScriptPlanner.create_script(topic, factual_brief=None)`
- `StoryboardAssembler.from_script(script)`
- `AssetSelector.select_assets(storyboard, registry)`
- `VideoJobStateMachine.transition(snapshot, target, artifact_refs, error)`
- `AIDirector(workflow="phase2")` stages Script → Storyboard → Asset Selection;
  default `workflow="auto"` preserves the 003 fake-provider compatibility path.
- New schemas:
  `director_script`, `director_factual_brief`, `asset_selection_report`,
  `director_quality_report`; `video_job_state` 2.0 extends, but does not
  remove, the 1.0 six-state contract.

## 3. Script, asset, and lifecycle evidence

- DirectorScript is 5–9 beats with hook/summary bookends, stable topic digest,
  bounded style, legal Pink Pig poses, tags, and fact references.
- Python injects IDs, Registry/IP, Composition regions, scene order, and asset
  IDs. Provider output cannot select paths or Registry IDs.
- Asset selection is deterministic, Registry-only, render-ready/fallback aware,
  repeat-avoiding, and records relative path, SHA-256, rights basis,
  factual/decorative classification, and fallback state.
- Job State snapshots are atomically written under the stable Director job
  directory; revisions are monotonic and terminal states cannot reopen.

## 4. Fake-provider evidence

Offline fake-provider full chain completed for `Modbus RTU是什么` with the
verified factual brief:

- artifact directory: `dist/director/director_ec229e6efe2c340d/`
- MP4: `output.mp4`
- 5 scenes and 5 distinct knowledge assets:
  `pink_pig.knowledge_master_slave.v1`,
  `pink_pig.knowledge_frame_layout.v1`,
  `pink_pig.knowledge_serial_parameters.v1`,
  `pink_pig.knowledge_troubleshooting.v1`,
  `pink_pig.knowledge_summary.v1`
- `video_job_state.json`: `completed`, revision 6,
  `factual_review_status: verified`
- topic-only comparison remains `quality_check` / `review_required`.
- Stable-topic reruns now clear only known pipeline artifacts before starting;
  the prior real-provider failure snapshot is preserved separately under
  `dist/director/provider_failures/director_ec229e6efe2c340d/`, so the main
  job directory is a single completed fake-provider snapshot rather than a
  mixed success/failure directory.

## 5. Real Codex CLI evidence

The required single real-provider acceptance command was attempted once:

```text
python generate_video.py --topic-file examples/ai_director_demo/topic.txt \
  --factual-brief examples/ai_director_demo/factual_brief.json \
  --director-provider codex-cli --output-name pink_pig_modbus_ai_demo.mp4
```

It failed closed with:

```json
{"code":"director_provider_failed","message":"Codex CLI Director provider failed.","context":{"provider":"codex-cli","reason":"nonzero_exit","exit_code":1}}
```

No raw stdout/stderr, prompt, credentials, or absolute provider path was
retained. The real-provider prerequisite is therefore `BLOCKED`; this report
does not claim a real-AI completion.

A separate read-only diagnostic of the same local CLI (without changing Codex
configuration, cache, profile, model, OAuth, or login state) identified the
environment cause as a malformed local models cache: the required
`base_instructions` field is missing. No cache repair or second real-provider
attempt was performed inside this task.

## 6. Media and quality evidence

Independent ffprobe for the fake-provider MP4:

```text
duration 38.400000 s
video h264 1080x1920 30/1
audio aac 24000 Hz
```

`render_report.json` agrees: duration 38.4, 1080×1920, 30.0 fps, H.264, AAC
24 kHz, burned-in subtitle cue count 5, subtitle region x=90/y=1120/
width=900/height=460, Composition `knowledge_illustration`, Pink Pig style
gate pass, and the same ordered asset IDs. FFmpeg complete decode passed for
the fake Phase 2 MP4, the offline job MP4, and the legacy demo MP4.

## 7. Tests and commands

| Command | Result |
|---|---|
| `python -m pytest tests/director -q` | 32 passed |
| `python -m pytest tests/video -q` | 273 passed |
| `python -m pytest video_factory/tests -q` | 5 passed |
| `python generate_video.py --job tests/video/fixtures/job_offline.yaml` | exit 0 |
| `python generate_video.py --config examples/pink_pig_demo/config.yaml` | exit 0 |
| fake-provider full `run_topic()` | completed, MP4/report/state produced |
| `git diff --check` | pass |
| JSON/schema/YAML parse and `py_compile` | pass |
| legacy `storyboard_invalid:path` scan | no matches |

## 8. Obsidian update

Updated in UTF-8:

1. `E:/AI_Tools/Obsidian/Data/notes-personal/codex_memory/03-项目记忆/OpenClaw_VideoFactory/04-落地状态与执行计划.md` — appended the Phase 2 checkpoint and linked the new page.
2. `E:/AI_Tools/Obsidian/Data/notes-personal/codex_memory/03-项目记忆/OpenClaw_VideoFactory/05-AI-Director与素材智能.md` — created with baseline, data flow, contracts, Skill switch, factual policy, evidence, boundaries, and debt.

## 9. Git ignore and branch evidence

- Branch: `codex/ai-director-video-factory-phase2-001`
- Base/current implementation baseline: `76180a59ea662bdf168d88baaeb777d3e8eb59ef`
- `git check-ignore -q -- docs/PINK_PIG_PHASE1_ARCHITECTURE.md` exited 1.
- `git check-ignore -q -- reports/AI_DIRECTOR_PHASE2_IMPLEMENTATION.md` exited 1.
- `git check-ignore -q -- reports/change_requests/AI-DIRECTOR-VIDEO-FACTORY-PHASE2-001.json` exited 1.
- The six pre-existing user dirty files were preserved and not staged, cleaned,
  reset, committed, or pushed.

## 10. Forbidden-surface audit

No task diff was made to OpenClaw, Feishu, Gateway, Binding, OAuth, Cron,
`src/factory/db.py`, `src/factory/state.py`, renderer core, FFmpeg chain,
`PROJECT_STATUS.yaml`, or formal P0/P1/P2 gates. Existing user-owned dirty
changes in those paths remain untouched. This local branch is not a phase
promotion and does not imply formal Gate passage.

## 11. Remaining debt and disposition

- Real Codex CLI provider acceptance is blocked by its nonzero exit 1; the
  read-only diagnostic points to the malformed local models cache described in
  section 5. Repairing or refreshing that cache is a separate authorization
  because this task forbids Codex config/profile/model/OAuth mutation.
- The local artifact hygiene issue found by independent review was corrected:
  stable-topic reruns clean generated media/reports, and the sanitized failure
  snapshot is quarantined outside the completed job directory.
- Topic-only results still need factual review; AI hotspots need event-date and
  dedicated source contracts.
- No VideoJob database, cancellation, recovery, distributed retry engine, or
  VideoClaw/multi-agent orchestration.
- No second production provider; no pixel-level style QA; three SVG-only poses
  may still use fallback.
- Feishu integration and automatic operations remain future phases.
- Formal P0/P1/P2 status is unchanged.

Final disposition: `BLOCKED` (real provider acceptance did not pass; fake and
offline evidence are valid but insufficient for the requested READY marker).
