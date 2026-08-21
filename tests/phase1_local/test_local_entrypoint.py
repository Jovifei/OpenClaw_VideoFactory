from __future__ import annotations

import json
from pathlib import Path

import pytest

import generate_video
from src.factory import phase1_local
from video_factory.pipeline import review_package
from video_factory.pipeline.errors import FactoryContractError


def _plan() -> dict[str, object]:
    return {
        "job_id": "phase1_0123456789abcdef",
        "topic": "本地测试主题",
        "topic_digest": "0" * 64,
        "script": {"schema_version": "1.0"},
        "storyboard": {"schema_version": "1.0", "scenes": [{"scene_id": "s01"}]},
        "asset_selection": {"schema_version": "1.0", "selections": []},
        "factual_brief": {
            "schema_version": "1.0",
            "review_status": "verified",
            "sources": [],
        },
    }


def _wire_local_entrypoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    brief_path = tmp_path / "brief.json"
    brief_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(generate_video, "ROOT", tmp_path)
    monkeypatch.setattr(
        phase1_local,
        "load_local_brief",
        lambda _path: {"input_mode": "topic", "topic": "本地测试主题"},
    )
    monkeypatch.setattr(phase1_local, "build_local_plan", lambda _brief, repo_root: _plan())
    monkeypatch.setattr(
        review_package,
        "build_review_package",
        lambda **_kwargs: {"manifest": {"status": "ready_for_human_review"}, "quality": {"status": "passed"}},
    )
    return brief_path


def test_local_entrypoint_completes_with_declared_timeline_ref(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    brief_path = _wire_local_entrypoint(monkeypatch, tmp_path)
    monkeypatch.setattr(generate_video, "run_job", lambda _path, emit=False: {"audio_mode": "tts"})

    result = generate_video.run_local_brief(brief_path, emit=False)

    state_path = tmp_path / "dist" / "phase1_local" / "phase1_0123456789abcdef" / "video_job_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["quality_status"] == "passed"
    assert result["audio_mode"] == "tts"
    assert state["state"] == "completed"
    assert state["timeline_ref"] == "timeline.json"
    assert state["output_ref"] == "final_master.mp4"


def test_local_entrypoint_persists_structured_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    brief_path = _wire_local_entrypoint(monkeypatch, tmp_path)

    def fail_render(_path: Path, emit: bool = False) -> dict[str, object]:
        raise FactoryContractError(
            "audio_narration_incomplete",
            "The job requires narration.",
            {"mode": "bgm", "segments": 0},
        )

    monkeypatch.setattr(generate_video, "run_job", fail_render)
    with pytest.raises(FactoryContractError):
        generate_video.run_local_brief(brief_path, emit=False)

    state_path = tmp_path / "dist" / "phase1_local" / "phase1_0123456789abcdef" / "video_job_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["state"] == "failed"
    assert state["error"]["code"] == "audio_narration_incomplete"
    assert state["error"]["context"]["stage"] == "rendering"
