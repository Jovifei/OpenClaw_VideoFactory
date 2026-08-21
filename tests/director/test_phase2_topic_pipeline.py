from __future__ import annotations

import json
from pathlib import Path

import yaml

import generate_video
from src.factory.director import AIDirector
from tests.director.test_director_pipeline_components import FakeScriptProvider
from video_factory.pipeline.validation import validate


def test_topic_work_dir_reset_removes_only_pipeline_artifacts(tmp_path: Path) -> None:
    work_dir = tmp_path / "director_job"
    work_dir.mkdir()
    (work_dir / "output.mp4").write_bytes(b"stale")
    (work_dir / "render_report.json").write_text("{}", encoding="utf-8")
    (work_dir / "operator_note.txt").write_text("preserve", encoding="utf-8")
    generate_video._reset_director_work_dir(work_dir)
    assert not (work_dir / "output.mp4").exists()
    assert not (work_dir / "render_report.json").exists()
    assert (work_dir / "operator_note.txt").read_text(encoding="utf-8") == "preserve"


def test_phase2_topic_pipeline_writes_script_selection_and_review_state(monkeypatch) -> None:
    class LongScriptProvider(FakeScriptProvider):
        def generate(self, **kwargs):
            value = super().generate(**kwargs)
            for beat in value["beats"]:
                beat["narration"] = str(beat["narration"]) * 4
            return value

    director = AIDirector(provider=LongScriptProvider(), repo_root=Path.cwd(), workflow="phase2")

    def fake_run_job(job_path: Path, *, emit: bool = True) -> dict[str, object]:
        job = yaml.safe_load(job_path.read_text(encoding="utf-8"))
        validate(job, "video_job")
        work_dir = job_path.parent
        (work_dir / "render_report.json").write_text(json.dumps({
            "duration": 38.4,
            "resolution": {"width": 1080, "height": 1920},
            "fps": 30.0,
            "codec": "h264",
            "audio": {"present": True},
            "subtitle": {"present": True},
            "subtitle_region": {"x": 90, "y": 1120, "width": 900, "height": 460},
        }), encoding="utf-8")
        return {"mode": "job", "job_id": job["job_id"], "output": "dist/fake/output.mp4", "render_report": "dist/fake/render_report.json"}

    monkeypatch.setattr(generate_video, "run_job", fake_run_job)
    result = generate_video.run_topic("介绍 Modbus RTU", director=director, emit=False)
    work_dir = Path.cwd() / "dist" / "director" / result["job_id"]
    assert result["status"] == "review_required"
    assert (work_dir / "script.json").is_file()
    assert (work_dir / "asset_selection.json").is_file()
    assert (work_dir / "video_job_state.json").is_file()
    assert json.loads((work_dir / "video_job_state.json").read_text(encoding="utf-8"))["state"] == "quality_check"
    validate(json.loads((work_dir / "director_quality_report.json").read_text(encoding="utf-8")), "director_quality_report")
