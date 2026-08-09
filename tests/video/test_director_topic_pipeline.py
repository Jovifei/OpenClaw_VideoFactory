from __future__ import annotations

import json
from pathlib import Path

import yaml

import generate_video
from src.factory.director import AIDirector
from tests.video.test_ai_director import FakeProvider, _draft
from video_factory.pipeline.validation import validate


def test_topic_mode_writes_director_artifacts_and_reuses_run_job(monkeypatch) -> None:
    director = AIDirector(
        provider=FakeProvider([_draft()]),
        repo_root=Path.cwd(),
    )
    observed: dict[str, object] = {}

    def fake_run_job(job_path: Path, *, emit: bool = True) -> dict[str, object]:
        observed["job_path"] = job_path
        observed["emit"] = emit
        job = yaml.safe_load(job_path.read_text(encoding="utf-8"))
        validate(job, "video_job")
        return {
            "mode": "job",
            "job_id": job["job_id"],
            "output": "dist/director/fake/output.mp4",
            "render_report": "dist/director/fake/render_report.json",
        }

    monkeypatch.setattr(generate_video, "run_job", fake_run_job)
    result = generate_video.run_topic(
        "介绍 Modbus RTU",
        director=director,
        emit=False,
    )

    work_dir = Path.cwd() / "dist" / "director" / result["job_id"]
    assert observed["emit"] is False
    assert result["mode"] == "topic"
    assert not Path(result["output"]).is_absolute()
    assert (work_dir / "storyboard.json").is_file()
    assert (work_dir / "director_report.json").is_file()
    assert (work_dir / "video_job.yaml").is_file()
    storyboard = json.loads((work_dir / "storyboard.json").read_text(encoding="utf-8"))
    report = json.loads((work_dir / "director_report.json").read_text(encoding="utf-8"))
    validate(storyboard, "storyboard")
    validate(report, "director_run_report")
    assert not (work_dir / ".director_sandbox").exists()


def test_topic_mode_rejects_unconfigured_provider() -> None:
    try:
        generate_video.run_topic("Modbus", provider_name="not-configured", emit=False)
    except Exception as exc:
        assert getattr(exc, "code", None) == "director_provider_unavailable"
    else:
        raise AssertionError("unconfigured provider should fail closed")
