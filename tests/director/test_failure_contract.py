from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import generate_video
from src.factory.director import AIDirector
from src.factory.director.ai_director import _safe_report_error
from tests.director.test_director_pipeline_components import FakeScriptProvider
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.failure_contract import normalize_execution_error, sanitize_error_payload, sanitize_stage
from video_factory.pipeline.job_state import VideoJobStateMachine


@pytest.mark.parametrize(
    ("exc", "reason"),
    [
        (RuntimeError("C:/private/raw-output.mp4"), "runtime_error"),
        (ValueError("bad C:/private/input.json"), "value_error"),
        (OSError("C:/private/render.log"), "io_error"),
        (TimeoutError("secret command timed out"), "timeout"),
    ],
)
def test_execution_errors_are_stable_and_path_free(exc: BaseException, reason: str) -> None:
    error = normalize_execution_error(exc, stage="rendering")
    assert error.code == "video_job_execution_failed"
    assert error.context == {"stage": "rendering", "reason": reason}
    assert "private" not in repr(error.to_dict())
    assert "raw-output" not in repr(error.to_dict())


def test_unknown_stage_falls_back_to_rendering_and_absolute_paths_are_redacted() -> None:
    assert sanitize_stage("unclassified") == "rendering"
    payload = sanitize_error_payload(
        {
            "code": "video_job_execution_failed",
            "message": "failed C:/secret/output.mp4",
            "context": {"stage": "unclassified", "path": "C:/secret/output.mp4", "reason": "C:/secret"},
        }
    )
    assert payload["message"] == "Video job execution failed."
    assert payload["context"]["stage"] == "rendering"
    assert payload["context"]["path"] == "redacted"
    assert payload["context"]["reason"] == "redacted"


def test_director_failure_report_sanitizes_factory_error_details() -> None:
    report_error = _safe_report_error(
        FactoryContractError(
            "director_provider_failed",
            "failed C:/secret/provider-output.json",
            {"path": "C:/secret/provider-output.json", "reason": "C:/secret", "attempt": 2},
        ),
        attempt=2,
    )
    assert report_error["message"] == "Video job execution failed."
    assert report_error["context"]["path"] == "redacted"
    assert report_error["context"]["reason"] == "redacted"
    assert "secret" not in json.dumps(report_error)


def test_fail_atomically_increments_revision_and_persists_sanitized_error(tmp_path: Path) -> None:
    machine = VideoJobStateMachine(work_dir=tmp_path)
    state = machine.initial(job_id="director_failure", topic="Modbus RTU")
    failed = machine.fail(state, RuntimeError("C:/private/output.mp4"), stage="render")
    persisted = json.loads((tmp_path / "video_job_state.json").read_text(encoding="utf-8"))
    assert failed["state"] == persisted["state"] == "failed"
    assert failed["state_revision"] == persisted["state_revision"] == 1
    assert persisted["error"]["code"] == "video_job_execution_failed"
    assert persisted["error"]["context"] == {"stage": "rendering", "reason": "runtime_error"}
    assert "private" not in json.dumps(persisted)


class _RaisingDirector:
    workflow = "phase2"
    last_report = None
    last_script = None
    last_score = None
    last_asset_selection = None

    def create_storyboard(self, topic: str) -> dict[str, object]:
        raise RuntimeError("C:/private/provider-output.json")


def test_current_topic_failure_report_is_sanitized_before_persistence() -> None:
    topic = "malicious report unique"

    class MaliciousDirector(_RaisingDirector):
        def __init__(self) -> None:
            digest = generate_video.hashlib.sha256(topic.encode()).hexdigest()
            self.last_report = {
                "schema_version": "1.0",
                "provider": "fake",
                "provider_version": "test",
                "prompt_version": "pink_pig_director_v1",
                "topic_digest": digest,
                "attempts": 1,
                "draft_validation": {"status": "fail", "error_count": 1, "validator": "provider"},
                "storyboard_validation": {"status": "fail", "error_count": 1, "validator": "provider"},
                "semantic_validation": {"status": "fail", "error_count": 1, "validator": "provider"},
                "storyboard_id": "sb_0123456789abcdef",
                "storyboard_sha256": "b" * 64,
                "compiled_duration_seconds": 0.0,
                "factual_review_required": True,
                "error": {
                    "code": "video_job_execution_failed",
                    "message": "C:/secret/raw-provider-output",
                    "context": {"path": "C:/secret/raw-provider-output", "reason": "C:/secret"},
                },
            }

    director = MaliciousDirector()
    try:
        with pytest.raises(FactoryContractError):
            generate_video.run_topic(topic, director=director, emit=False)
        digest = generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]
        report = json.loads((generate_video.ROOT / "dist" / "director" / f"director_{digest}" / "director_report.json").read_text(encoding="utf-8"))
        assert "secret" not in json.dumps(report)
        assert report["error"]["message"] == "Video job execution failed."
        assert report["error"]["context"]["path"] == "redacted"
    finally:
        shutil.rmtree(generate_video.ROOT / "dist" / "director" / f"director_{generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]}", ignore_errors=True)


def test_sandbox_cleanup_validation_failure_persists_failed_state(monkeypatch: pytest.MonkeyPatch) -> None:
    topic = "sandbox cleanup failure unique"

    class SuccessfulDirector:
        workflow = "phase2"
        factual_brief = None
        last_script = {"script": "ok"}
        last_score = {"score": 90}
        last_asset_selection = None

        def __init__(self) -> None:
            digest = generate_video.hashlib.sha256(topic.encode()).hexdigest()
            self.last_report = {
                "schema_version": "1.0",
                "provider": "fake",
                "provider_version": "test",
                "prompt_version": "pink_pig_director_v1",
                "topic_digest": digest,
                "attempts": 1,
                "draft_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
                "storyboard_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
                "semantic_validation": {"status": "pass", "error_count": 0, "validator": "director_semantics"},
                "storyboard_id": "sb_0123456789abcdef",
                "storyboard_sha256": "b" * 64,
                "compiled_duration_seconds": 40.0,
                "factual_review_required": True,
                "error": None,
            }

        def create_storyboard(self, topic: str) -> dict[str, object]:
            return {}

    monkeypatch.setattr(generate_video.shutil, "rmtree", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("C:/private/sandbox")))
    try:
        with pytest.raises(FactoryContractError) as caught:
            generate_video.run_topic(topic, director=SuccessfulDirector(), emit=False)
        assert caught.value.code == "video_job_execution_failed"
        assert caught.value.context["stage"] == "storyboard"
        assert _state_for_topic(topic)["state"] == "failed"
    finally:
        monkeypatch.undo()
        shutil.rmtree(generate_video.ROOT / "dist" / "director" / f"director_{generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]}", ignore_errors=True)


class _LongScriptProvider(FakeScriptProvider):
    def generate(self, **kwargs):
        value = super().generate(**kwargs)
        for beat in value["beats"]:
            beat["narration"] = str(beat["narration"]) * 4
        return value


def _phase2_director() -> AIDirector:
    return AIDirector(provider=_LongScriptProvider(), repo_root=Path.cwd(), workflow="phase2")


def _state_for_topic(topic: str) -> dict[str, object]:
    digest = generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]
    path = generate_video.ROOT / "dist" / "director" / f"director_{digest}" / "video_job_state.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_job_validation_exception_persists_failed_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    topic = "job validation failure unique"
    monkeypatch.setattr(generate_video, "_load_director_job_defaults", lambda: (_ for _ in ()).throw(ValueError("C:/private/job.yaml")))
    try:
        with pytest.raises(FactoryContractError) as caught:
            generate_video.run_topic(topic, director=_phase2_director(), emit=False)
        assert caught.value.code == "video_job_execution_failed"
        assert caught.value.context["stage"] == "job_validation"
        state = _state_for_topic(topic)
        assert state["state"] == "failed"
    finally:
        shutil.rmtree(generate_video.ROOT / "dist" / "director" / f"director_{generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]}", ignore_errors=True)


def test_render_exception_persists_failed_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    topic = "render failure unique"
    monkeypatch.setattr(generate_video, "run_job", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("C:/private/render.mp4")))
    try:
        with pytest.raises(FactoryContractError) as caught:
            generate_video.run_topic(topic, director=_phase2_director(), emit=False)
        assert caught.value.code == "video_job_execution_failed"
        assert caught.value.context["stage"] == "rendering"
        assert _state_for_topic(topic)["state"] == "failed"
    finally:
        shutil.rmtree(generate_video.ROOT / "dist" / "director" / f"director_{generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]}", ignore_errors=True)


def test_quality_exception_persists_failed_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    topic = "quality failure unique"

    def fake_run_job(job_path: Path, *, emit: bool = False) -> dict[str, object]:
        return {"mode": "job", "job_id": "ignored", "output": "dist/fake/output.mp4", "render_report": "render_report.json"}

    monkeypatch.setattr(generate_video, "run_job", fake_run_job)
    monkeypatch.setattr(generate_video, "_build_director_quality_report", lambda **kwargs: (_ for _ in ()).throw(OSError("C:/private/quality.json")))
    try:
        with pytest.raises(FactoryContractError) as caught:
            generate_video.run_topic(topic, director=_phase2_director(), emit=False)
        assert caught.value.code == "video_job_execution_failed"
        assert caught.value.context["stage"] == "quality_check"
        assert _state_for_topic(topic)["state"] == "failed"
    finally:
        shutil.rmtree(generate_video.ROOT / "dist" / "director" / f"director_{generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]}", ignore_errors=True)


def test_verified_brief_aligns_state_director_and_quality_reports(monkeypatch: pytest.MonkeyPatch) -> None:
    topic = "Modbus RTU"

    class VerifiedDirector:
        workflow = "phase2"
        factual_brief = None
        last_script = {"script": "verified"}
        last_score = {"score": 93}
        last_asset_selection = None

        def __init__(self) -> None:
            digest = generate_video.hashlib.sha256(topic.encode()).hexdigest()
            self.last_report = {
                "schema_version": "1.0",
                "provider": "fake",
                "provider_version": "test",
                "prompt_version": "pink_pig_director_v1",
                "topic_digest": digest,
                "attempts": 1,
                "draft_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
                "storyboard_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
                "semantic_validation": {"status": "pass", "error_count": 0, "validator": "director_semantics"},
                "storyboard_id": "sb_0123456789abcdef",
                "storyboard_sha256": "b" * 64,
                "compiled_duration_seconds": 40.0,
                "factual_review_required": False,
                "error": None,
            }

        def create_storyboard(self, topic: str) -> dict[str, object]:
            return {}

    def fake_run_job(job_path: Path, *, emit: bool = False) -> dict[str, object]:
        work_dir = job_path.parent
        (work_dir / "render_report.json").write_text(
            json.dumps({
                "duration": 40.0,
                "resolution": {"width": 1080, "height": 1920},
                "fps": 30.0,
                "codec": "h264",
                "audio": {"present": True},
                "subtitle": {"present": True},
                "subtitle_region": {"x": 90, "y": 1120, "width": 900, "height": 460},
            }),
            encoding="utf-8",
        )
        return {"mode": "job", "job_id": "verified", "output": "output.mp4"}

    monkeypatch.setattr(generate_video, "run_job", fake_run_job)
    class _Brief:
        verified = True
        document = {"review_status": "verified", "facts": [], "sources": []}

    monkeypatch.setattr("src.factory.director.load_factual_brief", lambda *args, **kwargs: _Brief())
    try:
        result = generate_video.run_topic(
            topic,
            director=VerifiedDirector(),
            factual_brief_path="verified-brief.json",
            emit=False,
        )
        work_dir = generate_video.ROOT / "dist" / "director" / result["job_id"]
        state = json.loads((work_dir / "video_job_state.json").read_text(encoding="utf-8"))
        report = json.loads((work_dir / "director_report.json").read_text(encoding="utf-8"))
        quality = json.loads((work_dir / "director_quality_report.json").read_text(encoding="utf-8"))
        assert state["factual_review_required"] is False
        assert report["factual_review_required"] is False
        assert quality["factual_review_required"] is False
    finally:
        shutil.rmtree(generate_video.ROOT / "dist" / "director" / f"director_{generate_video.hashlib.sha256(topic.encode()).hexdigest()[:16]}", ignore_errors=True)


def test_provider_failure_rejects_stale_report_and_writes_failed_snapshot() -> None:
    director = _RaisingDirector()
    with pytest.raises(FactoryContractError) as caught:
        generate_video.run_topic("failure provider unique", director=director, emit=False)
    assert caught.value.code == "video_job_execution_failed"
    assert caught.value.context["stage"] == "storyboard"
    digest = generate_video.hashlib.sha256("failure provider unique".encode()).hexdigest()[:16]
    work_dir = generate_video.ROOT / "dist" / "director" / f"director_{digest}"
    state = json.loads((work_dir / "video_job_state.json").read_text(encoding="utf-8"))
    report = json.loads((work_dir / "director_report.json").read_text(encoding="utf-8"))
    assert state["state"] == "failed"
    assert report["error"]["code"] == "video_job_execution_failed"
    assert report["topic_digest"] == state["topic_digest"]
    assert "private" not in json.dumps(report)


def test_director_reuse_clears_last_run_fields_before_failure() -> None:
    class Provider(FakeScriptProvider):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def generate(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return super().generate(**kwargs)
            raise RuntimeError("stale C:/private/report.json")

    director = AIDirector(provider=Provider(), repo_root=Path.cwd(), workflow="phase2")
    # Simulate artifacts from a prior successful run.  The next run fails
    # before the planner can produce a replacement report.
    director.last_report = {"topic_digest": "old"}
    director.last_script = {"old": True}
    director.last_score = {"score": 99}
    director.last_asset_selection = {"old": True}
    with pytest.raises(FactoryContractError):
        director.create_storyboard("reuse second")
    assert director.last_report is None or director.last_report["topic_digest"] != "old"
    assert director.last_script != {"old": True}
    assert director.last_score != {"score": 99}
    assert director.last_asset_selection is None
