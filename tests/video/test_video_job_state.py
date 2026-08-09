from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from . import ROOT


SCHEMA_PATH = ROOT / "schemas" / "video" / "video_job_state.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base(state: str) -> dict:
    return {
        "schema_version": "1.0",
        "job_id": "modbus_rtu_intro",
        "topic": "介绍 Modbus RTU",
        "state": state,
    }


def _valid(state: str) -> dict:
    value = _base(state)
    if state in {"validated", "compiled", "rendering", "completed"}:
        value["storyboard_ref"] = "examples/pink_pig_story_demo/storyboard.json"
    if state in {"compiled", "rendering", "completed"}:
        value["timeline_ref"] = "dist/story_demo/timeline.json"
    if state == "completed":
        value["output_ref"] = "dist/pink_pig_story_demo.mp4"
        value["render_report_ref"] = "dist/story_demo/render_report.json"
    if state == "failed":
        value["error"] = {
            "code": "video_job_invalid",
            "message": "Video render job failed schema validation.",
            "context": {"schema": "video_job"},
        }
    return value


@pytest.mark.parametrize("state", ["draft", "validated", "compiled", "rendering", "completed", "failed"])
def test_each_lifecycle_state_validates(state: str) -> None:
    Draft202012Validator(_schema()).validate(_valid(state))


def test_state_schema_is_well_formed_and_closed() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["title"] == "VideoRenderJobState"
    assert schema["additionalProperties"] is False


@pytest.mark.parametrize(
    "state,field",
    [
        ("validated", "storyboard_ref"),
        ("compiled", "timeline_ref"),
        ("rendering", "timeline_ref"),
        ("completed", "output_ref"),
        ("completed", "render_report_ref"),
        ("failed", "error"),
    ],
)
def test_state_specific_required_fields_are_enforced(state: str, field: str) -> None:
    value = _valid(state)
    value.pop(field, None)
    with pytest.raises(Exception):
        Draft202012Validator(_schema()).validate(value)


def test_unknown_state_is_rejected() -> None:
    value = _base("queued")
    with pytest.raises(Exception):
        Draft202012Validator(_schema()).validate(value)


def test_extra_state_field_is_rejected() -> None:
    value = _valid("draft")
    value["transition"] = "validated"
    with pytest.raises(Exception):
        Draft202012Validator(_schema()).validate(value)


def test_validation_wrapper_uses_video_job_state_error_contract() -> None:
    broken = _valid("completed")
    broken.pop("render_report_ref")
    with pytest.raises(FactoryContractError) as excinfo:
        validate(broken, "video_job_state")
    assert excinfo.value.code == "video_job_state_invalid"
    assert set(excinfo.value.to_dict()) == {"code", "message", "context"}
    assert excinfo.value.context["schema"] == "video_job_state"
