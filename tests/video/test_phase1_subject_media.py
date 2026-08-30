from __future__ import annotations

import hashlib
import json
import uuid
import subprocess
import sys
from pathlib import Path

import pytest

from src.factory.phase1_subject_media import SubjectMediaRequest, run_subject_media, validate_ready_reports, validate_timing_coverage
from src.factory.phase1_topic import build_director_script, build_research_brief, build_scene_plan, build_topic_request
from video_factory.pipeline import validation


def _write(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_subject_media_requires_skill_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("JIAN_YING_SKILL_ROOT", raising=False)
    with pytest.raises(ValueError, match="jianying_skill_root_required"):
        run_subject_media(SubjectMediaRequest(tmp_path / "s.json", tmp_path / "p.json", tmp_path / "r.json", Path("E:/runtime/job")))


def test_subject_media_requires_explicit_media_python(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PHASE1_MEDIA_PYTHON", raising=False)
    skill = tmp_path / "skill"; (skill / "scripts").mkdir(parents=True); (skill / "scripts" / "jy_wrapper.py").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="media_python_required"):
        run_subject_media(SubjectMediaRequest(tmp_path / "s.json", tmp_path / "p.json", tmp_path / "r.json", Path("E:/runtime/job")), skill_root=skill)


def test_subject_media_result_schema_is_strict() -> None:
    assert validation.is_available()
    with pytest.raises(Exception):
        validation.validate({"schema_version":"1.0","status":"PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW"}, "phase1_subject_media_result")


def test_ready_reports_reject_status_only_documents() -> None:
    reports = {name:{"status":status} for name,status in {
        "timing":"timing_manifest_ready","render":"passed","visual_review":"passed",
        "preview":"audio_preview_ready_for_manual_listening","jianying":"draft_ready_for_manual_jianying_review"}.items()}
    with pytest.raises(ValueError, match="ready_report_contract_invalid"):
        validate_ready_reports(reports, scene_count=5, expanded_audio_count=5, visual_duration_us=30_000_000)


def test_ready_reports_fail_closed_under_python_optimized_mode() -> None:
    code = """from src.factory.phase1_subject_media import validate_ready_reports
r={k:{'status':v} for k,v in {'timing':'timing_manifest_ready','render':'passed','visual_review':'passed','preview':'audio_preview_ready_for_manual_listening','jianying':'draft_ready_for_manual_jianying_review'}.items()}
validate_ready_reports(r,scene_count=5,expanded_audio_count=5,visual_duration_us=30000000)
"""
    done = subprocess.run([sys.executable, "-O", "-c", code], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=False)
    assert done.returncode != 0
    assert "ready_report_contract_invalid:" in done.stderr


def test_subject_media_timing_coverage_requires_three_quarters_of_visual_duration() -> None:
    with pytest.raises(ValueError, match="subject_media_voice_coverage_below_minimum"):
        validate_timing_coverage({"voice":{"voice_end_microseconds":29_900_000}}, visual_duration_us=40_000_000)
    assert validate_timing_coverage({"voice":{"voice_end_microseconds":30_000_000,"coverage_ratio":0.75}}, visual_duration_us=40_000_000) == 0.75


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
        script_name = Path(command[1]).name
        def arg(name: str) -> Path: return Path(command[command.index(name) + 1])
        if script_name == "phase1_jianying_timing_probe.py":
            _write(arg("--manifest"), {"schema_version":"1.0","status":"timing_manifest_ready","script":{"sha256":hashlib.sha256(script.read_bytes()).hexdigest()},"scene_plan":{"sha256":hashlib.sha256(plan.read_bytes()).hexdigest()},"segments":[{}]*5,"voice":{"rendered_audio_segment_count":5,"voice_end_microseconds":25_000_000,"coverage_ratio":0.8333333333333334}})
        elif script_name == "assemble_jianying_voice_preview.py":
            visual_path, output_path = arg("--visual"), arg("--output"); output_path.write_bytes(b"preview")
            _write(arg("--report"), {"status":"audio_preview_ready_for_manual_listening","visual":{"sha256":hashlib.sha256(visual_path.read_bytes()).hexdigest()},"render_report":{"sha256":hashlib.sha256(arg("--visual-report").read_bytes()).hexdigest()},"audio_source":{"segment_count":5},"output":{"sha256":hashlib.sha256(output_path.read_bytes()).hexdigest(),"audio_present":True,"full_decode":"passed","codec":"aac","mean_volume_db":-20.0,"max_volume_db":-2.0},"sync_validation":{"status":"passed"}})
        elif script_name == "phase1_jianying_tts_draft.py":
            _write(arg("--report"), {"status":"draft_ready_for_manual_jianying_review","inputs":{"script_sha256":hashlib.sha256(script.read_bytes()).hexdigest(),"timing_manifest_sha256":hashlib.sha256(arg("--timing-manifest").read_bytes()).hexdigest(),"render_report_sha256":hashlib.sha256(arg("--visual-report").read_bytes()).hexdigest()},"sync_validation":{"status":"passed"},"audio_validation":{"status":"passed","muted":False,"segment_count":5},"subtitle_validation":{"status":"passed","segment_count":5},"tracks":[{"name":"VideoTrack","segment_count":5,"duration_microseconds":30_000_000},{"name":"VoiceOver","segment_count":5},{"name":"Subtitles","segment_count":5}],"export":{"automatic_export":"disabled"}})
        return type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    def visual(**kwargs: object) -> dict:
        output = Path(kwargs["output"]); output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(b"visual")
        clips = Path(kwargs["clips_dir"]); clips.mkdir(parents=True)
        report_entries = []
        for i in range(1, 6):
            clip = clips / f"scene_{i:02d}.mp4"; clip.write_bytes(str(i).encode())
            report_entries.append({"scene_index":i,"clip":{"filename":f"clips/{clip.name}","sha256":hashlib.sha256(clip.read_bytes()).hexdigest()}})
        report = Path(kwargs["report"]); _write(report,{"status":"passed","visual":{"filename":output.name,"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"audio_present":False,"burned_in_subtitles":False,"scene_timing":report_entries}})
        _write(Path(kwargs["review_report"]), {"status":"passed","visual":{"sha256":hashlib.sha256(output.read_bytes()).hexdigest()},"contact_sheet":{"sha256":"a"*64},"post_render_report":{"sha256":"b"*64},"post_render":{"full_decode":True,"all_frame_scan":{"status":"passed"}}})
        return {"status":"passed","visual":{"path":str(output)}}

    workdir = Path("E:/Claude_allow/Download") / f"subject-media-{uuid.uuid4().hex}"
    media_python = Path("E:/project/OpenClaw_VideoFactory/.venv/Scripts/python.exe")
    result = run_subject_media(SubjectMediaRequest(script, plan, request, workdir), skill_root=skill, media_python=media_python, runner=runner, render_runner=visual)
    assert result["status"] == "PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW"
    assert len(calls) == 3
    assert all(str(workdir.resolve()) in " ".join(call) for call in calls)


def test_subject_media_failure_writes_sanitized_stage_evidence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    request_value = build_topic_request(subject="watchdog", duration=30)
    research = build_research_brief(topic="watchdog", sources=[{"id":"s1","url":"https://example.com/a","title":"a","kind":"official_document"},{"id":"s2","url":"https://example.com/b","title":"b","kind":"research_paper"}], facts=[{"id":"f1","claim":"watchdog detects stalled software","source_ids":["s1"]},{"id":"f2","claim":"window follows worst case execution time","source_ids":["s1","s2"]}])
    script_value = build_director_script(request_value, research, {"script":"why reset? watchdog detects stalled software. window follows worst case execution time."})
    plan_value = build_scene_plan(script_value, research)
    script, plan, topic = _write(tmp_path/"s.json",script_value), _write(tmp_path/"p.json",plan_value), _write(tmp_path/"r.json",request_value)
    skill = tmp_path/"skill"; (skill/"scripts").mkdir(parents=True); (skill/"scripts"/"jy_wrapper.py").write_text("",encoding="utf-8")
    workdir = Path("E:/Claude_allow/Download") / f"subject-media-fail-{uuid.uuid4().hex}"
    def fail(*_: object, **__: object) -> object: raise RuntimeError("secret C:/private token")
    with pytest.raises(RuntimeError): run_subject_media(SubjectMediaRequest(script,plan,topic,workdir),skill_root=skill,media_python=Path("E:/project/OpenClaw_VideoFactory/.venv/Scripts/python.exe"),runner=fail)
    failure = json.loads((workdir/"media_failure.json").read_text(encoding="utf-8"))
    assert failure["failed_stage"] == "timing" and "C:/private" not in json.dumps(failure)
    assert not (workdir/"jianying_manifest.json").exists()
