from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest

from src.factory.phase1_subject_media import SubjectMediaRequest, run_subject_media
from src.factory.phase1_topic import build_director_script, build_research_brief, build_scene_plan, build_topic_request


def _write(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_subject_media_requires_skill_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("JIAN_YING_SKILL_ROOT", raising=False)
    with pytest.raises(ValueError, match="jianying_skill_root_required"):
        run_subject_media(SubjectMediaRequest(tmp_path / "s.json", tmp_path / "p.json", tmp_path / "r.json", Path("E:/runtime/job")))


def test_subject_media_uses_injected_runner_and_returns_candidate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    skill = tmp_path / "skill"; (skill / "scripts").mkdir(parents=True); (skill / "scripts" / "jy_wrapper.py").write_text("", encoding="utf-8")
    request_value = build_topic_request(subject="watchdog", duration=30)
    research = build_research_brief(topic="watchdog", sources=[{"id":"s1","url":"https://example.com/a","title":"a","kind":"official_document"},{"id":"s2","url":"https://example.com/b","title":"b","kind":"research_paper"}], facts=[{"id":"f1","claim":"watchdog detects stalled software","source_ids":["s1"]},{"id":"f2","claim":"window follows worst case execution time","source_ids":["s1","s2"]}])
    script_value = build_director_script(request_value, research, {"script":"why reset? watchdog detects stalled software. window follows worst case execution time."})
    plan_value = build_scene_plan(script_value, research)
    script = _write(tmp_path / "script.json", script_value)
    plan = _write(tmp_path / "plan.json", plan_value)
    request = _write(tmp_path / "request.json", request_value)
    calls: list[list[str]] = []

    def runner(command: list[str], **_: object) -> object:
        calls.append(command)
        return type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    def visual(**kwargs: object) -> dict:
        output = Path(kwargs["output"]); output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(b"visual")
        clips = Path(kwargs["clips_dir"]); clips.mkdir(parents=True)
        report_entries = []
        for i in range(1, 6):
            clip = clips / f"scene_{i:02d}.mp4"; clip.write_bytes(str(i).encode())
            report_entries.append({"scene_index":i,"clip":{"filename":f"clips/{clip.name}","sha256":hashlib.sha256(clip.read_bytes()).hexdigest()}})
        report = Path(kwargs["report"]); _write(report,{"visual":{"filename":output.name,"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"scene_timing":report_entries}})
        return {"status":"passed","visual":{"path":str(output)}}

    workdir = Path("E:/Claude_allow/Download") / f"subject-media-{uuid.uuid4().hex}"
    media_python = Path("E:/project/OpenClaw_VideoFactory/.venv/Scripts/python.exe")
    result = run_subject_media(SubjectMediaRequest(script, plan, request, workdir), skill_root=skill, media_python=media_python, runner=runner, render_runner=visual)
    assert result["status"] == "PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW"
    assert len(calls) == 3
    assert all(str(workdir.resolve()) in " ".join(call) for call in calls)
