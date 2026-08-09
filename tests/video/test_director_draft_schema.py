"""Contract tests for the provider-facing DirectorDraft schema."""

from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from . import ROOT


SCHEMA_PATH = ROOT / "schemas" / "video" / "director_draft.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _scene(index: int, *, purpose: str | None = None) -> dict:
    return {
        "purpose": purpose or ("hook" if index == 0 else "summary" if index == 4 else "explain"),
        "core_action": "小粉猪拆解并标注协议帧",
        "narration": f"第 {index + 1} 幕解释一个可验证的工程要点。",
        "caption": "工程要点",
        "mood": "focused",
        "pose": "thinking" if index == 1 else "measure",
        "transition_out": None if index == 4 else "fade",
    }


def _valid_draft() -> dict:
    return {
        "title": "认识 Modbus RTU",
        "content_scope": "evergreen_embedded_mainline",
        "scenes": [_scene(index) for index in range(5)],
    }


def _errors(schema: dict, document: dict) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (list(error.absolute_path), error.validator, error.message),
    )


def test_schema_is_well_formed_and_closed(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)
    assert schema["title"] == "DirectorDraft"
    assert schema["additionalProperties"] is False
    assert schema["$id"].endswith("/director_draft.schema.json")


def test_valid_five_scene_draft_passes(schema: dict) -> None:
    document = _valid_draft()
    assert _errors(schema, document) == []
    assert len(document["scenes"]) == 5
    assert document["scenes"][0]["purpose"] == "hook"
    assert document["scenes"][-1]["purpose"] == "summary"


@pytest.mark.parametrize("count", [4, 10])
def test_scene_count_must_be_between_five_and_nine(schema: dict, count: int) -> None:
    document = _valid_draft()
    document["scenes"] = [_scene(index) for index in range(count)]
    assert _errors(schema, document)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("content_scope", "breaking_news"),
        ("scenes", "not-an-array"),
    ],
)
def test_top_level_contract_is_restricted(schema: dict, field: str, value: object) -> None:
    document = _valid_draft()
    document[field] = value
    assert _errors(schema, document)


def test_scene_requires_all_declared_fields(schema: dict) -> None:
    document = _valid_draft()
    document["scenes"][0].pop("core_action")
    assert _errors(schema, document)


def test_pose_vocabulary_is_the_registry_eight(schema: dict) -> None:
    allowed = {
        "normal",
        "thinking",
        "question",
        "measure",
        "repair",
        "success",
        "warning",
        "ending",
    }
    assert set(schema["$defs"]["scene"]["properties"]["pose"]["enum"]) == allowed

    document = _valid_draft()
    document["scenes"][0]["pose"] = "random_mascot"
    assert _errors(schema, document)


def test_transition_vocabulary_and_terminal_null(schema: dict) -> None:
    document = _valid_draft()
    document["scenes"][0]["transition_out"] = "dissolve"
    assert _errors(schema, document)

    document = _valid_draft()
    document["scenes"][-1]["transition_out"] = None
    assert _errors(schema, document) == []


def test_provider_cannot_add_asset_or_path_fields(schema: dict) -> None:
    document = _valid_draft()
    document["scenes"][0]["asset_id"] = "pink_pig.normal.v1"
    document["scenes"][0]["image_path"] = "assets/pink_pig/pig01.png"
    assert _errors(schema, document)


def test_first_and_last_purpose_are_checked_by_semantic_layer(schema: dict) -> None:
    document = _valid_draft()
    assert _errors(schema, document) == []

    invalid = copy.deepcopy(document)
    invalid["scenes"][0]["purpose"] = "summary"
    invalid["scenes"][-1]["purpose"] = "explain"
    # The JSON Schema intentionally validates shape only. The Director semantic
    # layer owns the positional hook/summary invariant.
    assert _errors(schema, invalid) == []
    assert invalid["scenes"][0]["purpose"] != "hook"
    assert invalid["scenes"][-1]["purpose"] != "summary"
