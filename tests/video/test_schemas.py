"""T05 / stage-four ② (part 1) — the three ``schemas/video/*`` contracts.

Covers architecture §2.2, §3.2–§3.4 and §8.2–§8.3:

* all three schemas pass ``Draft202012Validator.check_schema()``
* ``$id`` / ``title`` follow the §8.3 naming rules and deliberately avoid the
  already-taken ``VideoJob`` name (§8.2)
* the shipped examples (storyboard / job / compiled timeline) validate
* deliberately malformed documents are rejected
* ``video_factory.pipeline.validation`` wraps jsonschema as specified in §3.7
"""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from video_factory.pipeline import validation

from . import ROOT

SCHEMA_DIR = ROOT / "schemas" / "video"
EXAMPLE_DIR = ROOT / "examples" / "pink_pig_story_demo"
WORK_DIR = ROOT / "dist" / "story_demo"

SCHEMA_NAMES = ("storyboard", "timeline", "video_job")
EXPECTED_TITLES = {
    "storyboard": "Storyboard",
    "timeline": "Timeline",
    "video_job": "VideoRenderJob",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schemas() -> dict[str, dict]:
    return {
        name: json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        for name in SCHEMA_NAMES
    }


@pytest.fixture(scope="module")
def storyboard_example() -> dict:
    return json.loads((EXAMPLE_DIR / "storyboard.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def job_example() -> dict:
    return yaml.safe_load((EXAMPLE_DIR / "job.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def timeline_example() -> dict:
    return json.loads((WORK_DIR / "timeline.json").read_text(encoding="utf-8"))


def _errors(schema: dict, document: dict) -> list[str]:
    return [
        f"{'.'.join(str(part) for part in err.absolute_path)}: {err.message}"
        for err in sorted(
            Draft202012Validator(schema).iter_errors(document),
            key=lambda err: list(err.absolute_path),
        )
    ]


def _assert_rejected(schema: dict, document: dict) -> None:
    assert _errors(schema, document), "document was expected to be rejected but validated cleanly"


# ---------------------------------------------------------------------------
# The schemas themselves
# ---------------------------------------------------------------------------


class TestSchemaFilesAreWellFormed:
    @pytest.mark.parametrize("name", SCHEMA_NAMES)
    def test_check_schema_passes(self, schemas: dict[str, dict], name: str) -> None:
        """T01 acceptance: ``Draft202012Validator.check_schema()`` on all three."""
        Draft202012Validator.check_schema(schemas[name])

    @pytest.mark.parametrize("name", SCHEMA_NAMES)
    def test_declares_draft_2020_12(self, schemas: dict[str, dict], name: str) -> None:
        assert schemas[name]["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    @pytest.mark.parametrize("name", SCHEMA_NAMES)
    def test_id_follows_the_naming_rule(self, schemas: dict[str, dict], name: str) -> None:
        assert schemas[name]["$id"] == f"https://openclaw.local/schemas/video/{name}.schema.json"

    @pytest.mark.parametrize("name", SCHEMA_NAMES)
    def test_title_avoids_the_taken_video_job_name(
        self, schemas: dict[str, dict], name: str
    ) -> None:
        """§8.2 — ``VideoJob`` belongs to the existing state-machine schema."""
        title = schemas[name]["title"]
        assert title == EXPECTED_TITLES[name]
        assert title != "VideoJob"

    @pytest.mark.parametrize("name", SCHEMA_NAMES)
    def test_top_level_is_closed_and_requires_schema_version(
        self, schemas: dict[str, dict], name: str
    ) -> None:
        schema = schemas[name]
        assert schema["additionalProperties"] is False
        assert "schema_version" in schema["required"]

    def test_readme_documents_the_responsibility_boundary(self) -> None:
        """T01 要点 2 — the README must delimit the three schema families."""
        readme = (SCHEMA_DIR / "README.md").read_text(encoding="utf-8")
        assert "schemas/video_job.schema.json" in readme
        assert "schemas/video_workflow" in readme


# ---------------------------------------------------------------------------
# Positive cases — shipped documents validate
# ---------------------------------------------------------------------------


class TestExamplesValidate:
    def test_storyboard_example_validates(
        self, schemas: dict[str, dict], storyboard_example: dict
    ) -> None:
        assert _errors(schemas["storyboard"], storyboard_example) == []

    def test_job_example_validates(self, schemas: dict[str, dict], job_example: dict) -> None:
        assert _errors(schemas["video_job"], job_example) == []

    def test_offline_fixture_job_validates(self, schemas: dict[str, dict]) -> None:
        fixture = ROOT / "tests" / "video" / "fixtures" / "job_offline.yaml"
        document = yaml.safe_load(fixture.read_text(encoding="utf-8"))
        assert _errors(schemas["video_job"], document) == []

    def test_compiled_timeline_validates(
        self, schemas: dict[str, dict], timeline_example: dict
    ) -> None:
        assert _errors(schemas["timeline"], timeline_example) == []

    def test_job_yaml_carries_an_explicit_schema_version(self, job_example: dict) -> None:
        """Engineer deviation D3 — ``schema_version`` must be present in job.yaml."""
        assert job_example["schema_version"] == "1.0"


# ---------------------------------------------------------------------------
# Negative cases — storyboard
# ---------------------------------------------------------------------------


class TestStoryboardNegatives:
    @pytest.fixture
    def doc(self, storyboard_example: dict) -> dict:
        return copy.deepcopy(storyboard_example)

    @pytest.mark.parametrize(
        "field", ["schema_version", "storyboard_id", "title", "ip", "globals", "scenes"]
    )
    def test_missing_top_level_field_is_rejected(
        self, schemas: dict[str, dict], doc: dict, field: str
    ) -> None:
        doc.pop(field)
        _assert_rejected(schemas["storyboard"], doc)

    def test_unknown_top_level_field_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        doc["unexpected_extension"] = True
        _assert_rejected(schemas["storyboard"], doc)

    def test_empty_scene_list_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"] = []
        _assert_rejected(schemas["storyboard"], doc)

    def test_bad_schema_version_pattern_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        doc["schema_version"] = "v1"
        _assert_rejected(schemas["storyboard"], doc)

    def test_bad_storyboard_id_pattern_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        doc["storyboard_id"] = "Pink Pig Demo"
        _assert_rejected(schemas["storyboard"], doc)

    def test_bad_scene_id_pattern_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0]["scene_id"] = "scene-1"
        _assert_rejected(schemas["storyboard"], doc)

    def test_unsupported_transition_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        doc["scenes"][0]["transition_out"] = "dissolve"
        _assert_rejected(schemas["storyboard"], doc)

    def test_empty_narration_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0]["narration"] = ""
        _assert_rejected(schemas["storyboard"], doc)

    def test_zero_order_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0]["order"] = 0
        _assert_rejected(schemas["storyboard"], doc)

    def test_unknown_duration_mode_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0]["duration_intent"] = {"mode": "tts"}
        _assert_rejected(schemas["storyboard"], doc)

    def test_unknown_scene_field_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0]["camera_move"] = "pan"
        _assert_rejected(schemas["storyboard"], doc)

    def test_missing_globals_field_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["globals"].pop("narration_cps")
        _assert_rejected(schemas["storyboard"], doc)

    def test_non_positive_transition_seconds_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        """Engineer deviation D1 — encoded as ``minimum: 0.001`` instead of
        ``exclusiveMinimum: true`` (rejected by the jsonschema 4.26 metaschema)."""
        doc["globals"]["transition_seconds"] = 0
        _assert_rejected(schemas["storyboard"], doc)


# ---------------------------------------------------------------------------
# Negative cases — timeline
# ---------------------------------------------------------------------------


class TestTimelineNegatives:
    @pytest.fixture
    def doc(self, timeline_example: dict) -> dict:
        return copy.deepcopy(timeline_example)

    def test_scene_shorter_than_the_renderer_floor_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        doc["scenes"][0]["duration"] = 0.1
        _assert_rejected(schemas["timeline"], doc)

    def test_unknown_transition_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0]["transition"] = "dissolve"
        _assert_rejected(schemas["timeline"], doc)

    def test_missing_image_path_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["scenes"][0].pop("image_path")
        _assert_rejected(schemas["timeline"], doc)

    def test_wall_clock_timestamp_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        """§3.3 / R6 — timeline documents must stay free of wall-clock data."""
        doc["generated_at"] = "2026-08-09T10:37:07+08:00"
        _assert_rejected(schemas["timeline"], doc)

    def test_none_is_an_accepted_terminal_transition(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        assert doc["scenes"][-1]["transition"] == "none"
        assert _errors(schemas["timeline"], doc) == []


# ---------------------------------------------------------------------------
# Negative cases — video_job
# ---------------------------------------------------------------------------


class TestVideoJobNegatives:
    @pytest.fixture
    def doc(self, job_example: dict) -> dict:
        return copy.deepcopy(job_example)

    def test_wrong_job_kind_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["job_kind"] = "state_machine"
        _assert_rejected(schemas["video_job"], doc)

    def test_malformed_pad_color_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["render"]["pad_color"] = "#F7E4EA"
        _assert_rejected(schemas["video_job"], doc)

    def test_unknown_audio_strategy_is_rejected(
        self, schemas: dict[str, dict], doc: dict
    ) -> None:
        doc["audio"]["strategy"] = "elevenlabs"
        _assert_rejected(schemas["video_job"], doc)

    @pytest.mark.parametrize("strategy", ["tts_with_offline_fallback", "bgm_only", "silent"])
    def test_documented_audio_strategies_are_accepted(
        self, schemas: dict[str, dict], doc: dict, strategy: str
    ) -> None:
        doc["audio"]["strategy"] = strategy
        assert _errors(schemas["video_job"], doc) == []

    def test_missing_work_dir_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["outputs"].pop("work_dir")
        _assert_rejected(schemas["video_job"], doc)

    def test_unknown_output_field_is_rejected(self, schemas: dict[str, dict], doc: dict) -> None:
        doc["outputs"]["thumbnail"] = "dist/thumb.png"
        _assert_rejected(schemas["video_job"], doc)


# ---------------------------------------------------------------------------
# validation.py — the jsonschema wrapper (§3.7)
# ---------------------------------------------------------------------------


class TestValidationWrapper:
    def test_is_available_reports_true_in_this_environment(self) -> None:
        assert validation.is_available() is True

    @pytest.mark.parametrize(
        "name", ["storyboard", "timeline", "video_job", "video_job_state", "pink_pig_registry"]
    )
    def test_load_returns_a_schema_for_every_catalogued_name(self, name: str) -> None:
        schema = validation.load(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_load_unknown_name_raises(self) -> None:
        with pytest.raises(validation.FactoryContractError) as excinfo:
            validation.load("nope")
        assert excinfo.value.code == "schema_catalog_invalid"

    def test_validate_accepts_the_shipped_storyboard(self, storyboard_example: dict) -> None:
        validation.validate(storyboard_example, "storyboard")

    def test_validate_rejects_a_malformed_storyboard(self, storyboard_example: dict) -> None:
        broken = copy.deepcopy(storyboard_example)
        broken["scenes"][0]["order"] = "first"
        with pytest.raises(validation.SchemaValidationError) as excinfo:
            validation.validate(broken, "storyboard")
        assert excinfo.value.code == "storyboard_schema_invalid"
        assert excinfo.value.context["path"] == "scenes.0.order"

    def test_validate_rejects_a_malformed_timeline(self, timeline_example: dict) -> None:
        broken = copy.deepcopy(timeline_example)
        broken["scenes"][0]["duration"] = 0.01
        with pytest.raises(validation.SchemaValidationError):
            validation.validate(broken, "timeline")

    def test_validate_rejects_a_malformed_job(self, job_example: dict) -> None:
        broken = copy.deepcopy(job_example)
        broken["job_kind"] = "nope"
        with pytest.raises(validation.SchemaValidationError):
            validation.validate(broken, "video_job")
