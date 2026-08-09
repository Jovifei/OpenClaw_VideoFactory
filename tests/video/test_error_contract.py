from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from . import ROOT


def _load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_factory_contract_error_has_code_message_context() -> None:
    error = FactoryContractError("storyboard_schema_invalid", "bad storyboard", {"path": "scenes.0"})
    assert str(error) == "storyboard_schema_invalid"
    assert error.to_dict() == {
        "code": "storyboard_schema_invalid",
        "message": "bad storyboard",
        "context": {"path": "scenes.0"},
    }


@pytest.mark.parametrize(
    ("schema_name", "code", "relative"),
    [
        ("pink_pig_registry", "asset_registry_invalid", "src/factory/assets/pink_pig/registry.json"),
        ("storyboard", "storyboard_schema_invalid", "examples/pink_pig_story_demo/storyboard.json"),
        ("timeline", "timeline_schema_invalid", "dist/story_demo/timeline.json"),
        ("video_job", "video_job_invalid", "examples/pink_pig_story_demo/job.yaml"),
    ],
)
def test_required_schema_errors_have_structured_contract(schema_name: str, code: str, relative: str) -> None:
    value = _load_json(relative) if relative.endswith(".json") else None
    if schema_name == "pink_pig_registry":
        value = copy.deepcopy(value)
        value["style_profile_ref"] = "../escape.json"
    elif schema_name == "storyboard":
        value = copy.deepcopy(value)
        value["scenes"][0]["order"] = "first"
    elif schema_name == "timeline":
        value = copy.deepcopy(value)
        value["scenes"][0]["duration"] = 0.01
    else:
        value = {"schema_version": "1.0", "job_kind": "wrong"}
    with pytest.raises(FactoryContractError) as excinfo:
        validate(value, schema_name)
    error = excinfo.value
    assert error.code == code
    assert error.message
    assert isinstance(error.context, dict)
    assert error.context["schema"] == schema_name
    assert "path" in error.context


def test_schema_error_code_does_not_contain_json_path() -> None:
    value = _load_json("examples/pink_pig_story_demo/storyboard.json")
    value["scenes"][0]["order"] = "first"
    with pytest.raises(FactoryContractError) as excinfo:
        validate(value, "storyboard")
    assert excinfo.value.code == "storyboard_schema_invalid"
    assert ":scenes" not in excinfo.value.code
    assert excinfo.value.context["path"] == "scenes.0.order"


def test_cli_emits_structured_error_object(tmp_path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("schema_version: '1.0'\njob_kind: wrong\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "generate_video.py", "--job", str(invalid)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(proc.stdout.strip())
    assert proc.returncode == 2
    assert set(payload["error"]) == {"code", "message", "context"}
    assert payload["error"]["code"] == "video_job_invalid"


def test_legacy_storyboard_code_is_not_emitted() -> None:
    value = _load_json("examples/pink_pig_story_demo/storyboard.json")
    value["scenes"][0]["order"] = "first"
    with pytest.raises(FactoryContractError) as excinfo:
        validate(value, "storyboard")
    legacy_code = "storyboard_" + "invalid"
    assert legacy_code not in excinfo.value.code
