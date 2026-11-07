from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import yaml

import generate_video
from video_factory.pipeline import narration_timing, registry, storyboard, validation


def test_outer_job_persists_shared_audio_integrity_evidence_without_rendering(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(generate_video, "ROOT", tmp_path)
    job_path = tmp_path / "render_job.yaml"
    (tmp_path / "storyboard.json").write_text(json.dumps({"scenes": [{"scene_id": "s01"}]}), encoding="utf-8")
    work_dir = tmp_path / "work"
    raw_path = work_dir / "raw.wav"
    aligned_path = work_dir / "aligned.wav"
    work_dir.mkdir()
    raw_path.write_bytes(b"raw")
    aligned_path.write_bytes(b"aligned")
    (work_dir / "script.json").write_text(json.dumps({"beats": [{"narration": "完整旁白", "fact_refs": []}]}), encoding="utf-8")
    (work_dir / "factual_brief.json").write_text(json.dumps({"facts": []}), encoding="utf-8")
    job = {
        "schema_version": "1.0",
        "job_id": "phase1_audio_contract_integration",
        "job_kind": "video_render",
        "storyboard_ref": "storyboard.json",
        "registry_ref": "registry.json",
        "render": {
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "transition_seconds": 0.4,
            "pad_color": "0xF4F6F8",
            "encoder": "cpu",
        },
        "audio": {
            "strategy": "tts_with_offline_fallback",
            "allow_network": False,
            "require_narration": True,
            "source_aligned_narration": True,
            "tts": {"provider": "windows-sapi", "voice": "test"},
        },
        "outputs": {"video": "out/final_master.mp4", "work_dir": "work"},
    }
    job_path.write_text(yaml.safe_dump(job, sort_keys=False), encoding="utf-8")

    timeline = {
        "schema_version": "1.0",
        "fps": 30,
        "transition_mode": "technical_cut",
        "transition_seconds": 0.4,
        "scenes": [{"scene_id": "s01", "duration": 1.2, "narration": "完整旁白"}],
        "total_duration_seconds": 1.2,
    }
    storyboard_doc = {"schema_version": "1.0", "scenes": [{"scene_id": "s01", "narration": "完整旁白"}]}
    integrity = {
        "status": "passed",
        "segments_in_order": True,
        "expected_endpoint_seconds": 1.2,
        "actual_endpoint_seconds": 1.2,
    }
    segment = {
        "scene_id": "s01",
        "narration": "完整旁白",
        "audio_path": str(raw_path),
        "audio_file": raw_path.name,
        "raw_audio_sha256": "raw-sha",
        "actual_duration": 1.0,
        "scene_duration": 1.0,
        "allocated_scene_duration": 1.2,
        "aligned_duration": 1.2,
        "aligned_audio_sha256": "aligned-sha",
        "overflow": False,
        "audio_integrity": {"status": "passed", "prefix_match": True, "tail_is_silence": True},
    }
    captured: dict[str, object] = {}

    def fake_plan_source_aligned_narration(**kwargs):
        captured.update(kwargs)
        return {
            "timeline": timeline,
            "storyboard": storyboard_doc,
            "script": {"beats": [{"narration": "完整旁白", "fact_refs": []}]},
            "audio_path": aligned_path,
            "segments": (segment,),
            "subtitle_path": work_dir / "subtitle.srt",
            "rewrite_count": 0,
            "passes": [{"objective_audio_integrity": integrity}],
            "objective_audio_integrity": integrity,
            "original_script_sha256": "original-script-sha",
            "final_script_sha256": "final-script-sha",
            "final_timeline_sha256": "final-timeline-sha",
            "final_srt_sha256": "final-srt-sha",
        }

    monkeypatch.setattr(narration_timing, "plan_source_aligned_narration", fake_plan_source_aligned_narration)
    monkeypatch.setattr(registry, "load_pink_pig_registry", lambda **_kwargs: SimpleNamespace(get=lambda _id: None))
    monkeypatch.setattr(storyboard, "load_storyboard", lambda _path: storyboard_doc)
    monkeypatch.setattr(storyboard, "validate_storyboard", lambda _doc: None)
    monkeypatch.setattr(storyboard, "compile_storyboard", lambda _doc, _registry, repo_root: timeline)
    monkeypatch.setattr(validation, "validate", lambda _value, _kind: None)
    monkeypatch.setattr(generate_video, "load_mascot_contract", lambda *_args, **_kwargs: {"mode": "off"})
    def fake_build_srt(_timeline, path, composition=None):
        path.write_text("1\n00:00:00,000 --> 00:00:01,200\n完整旁白\n", encoding="utf-8")
        return [{"start": 0.0, "end": 1.2}]

    monkeypatch.setattr(generate_video, "build_srt_from_timeline", fake_build_srt)
    render_inputs: dict[str, object] = {}

    def fake_render_video(**kwargs):
        render_inputs.update(kwargs)
        Path(kwargs["output_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(kwargs["output_path"]).write_bytes(b"no-real-render")
        return {"duration": 1.2, "video_codec": "h264", "audio_codec": "aac"}

    monkeypatch.setattr(generate_video, "render_video", fake_render_video)
    monkeypatch.setattr(generate_video, "to_render_timeline", lambda _timeline: [])
    monkeypatch.setattr(generate_video, "build_render_report", lambda **_kwargs: {"status": "passed"})
    original_run = subprocess.run
    monkeypatch.setattr(
        generate_video.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=json.dumps({"format": {"duration": "1.2", "size": "12", "format_name": "mov,mp4"}, "streams": []}),
            stderr="",
            returncode=0,
        ) if args and "ffprobe" in args[0] else original_run(*args, **kwargs),
    )

    result = generate_video.run_job(job_path, emit=False)
    report = json.loads((work_dir / "run_report.json").read_text(encoding="utf-8"))

    assert result["audio_mode"] == "tts"
    assert captured["work_dir"] == work_dir
    assert render_inputs["audio_path"] == aligned_path
    assert report["narration_alignment"]["mode"] == "source_aligned_measured_tts"
    assert report["narration_alignment"]["objective_audio_integrity"]["status"] == "passed"
    assert report["audio_plan"]["segments"][0]["audio_integrity"]["prefix_match"] is True
