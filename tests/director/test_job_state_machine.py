from __future__ import annotations

import json
from pathlib import Path

import pytest

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.job_state import VideoJobStateMachine
from video_factory.pipeline.validation import validate


def test_phase2_state_machine_accepts_ordered_transitions_and_atomic_write(tmp_path: Path) -> None:
    machine = VideoJobStateMachine(work_dir=tmp_path)
    state = machine.initial(job_id="director_abc123", topic="Modbus RTU", factual_review_required=False)
    refs = {"script_ref": "script.json"}
    state = machine.transition(state, "planning")
    state = machine.transition(state, "script_ready", artifact_refs=refs)
    state = machine.transition(state, "storyboard_ready", artifact_refs={"storyboard_ref": "storyboard.json"})
    state = machine.transition(state, "rendering", artifact_refs={"timeline_ref": "timeline.json"})
    state = machine.transition(state, "quality_check", artifact_refs={"render_report_ref": "render_report.json", "quality_report_ref": "director_quality_report.json"})
    state = machine.transition(state, "completed", artifact_refs={"output_ref": "output.mp4"})
    validate(state, "video_job_state")
    assert state["state_revision"] == 6
    path = machine.write(state)
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "completed"


def test_state_machine_rejects_skip_backtrack_terminal_and_unsafe_refs(tmp_path: Path) -> None:
    machine = VideoJobStateMachine(work_dir=tmp_path)
    state = machine.initial(job_id="director_abc123", topic="Modbus RTU")
    for target in ("completed", "created"):
        with pytest.raises(FactoryContractError) as caught:
            machine.transition(state, target)
        assert caught.value.code == "video_job_state_invalid"
    with pytest.raises(FactoryContractError):
        machine.transition(state, "planning", artifact_refs={"script_ref": "../secret.json"})
    with pytest.raises(FactoryContractError):
        machine.transition(state, "failed")
    failed = machine.transition(state, "failed", error={"code": "director_script_invalid", "message": "bad", "context": {}})
    with pytest.raises(FactoryContractError):
        machine.transition(failed, "planning")
