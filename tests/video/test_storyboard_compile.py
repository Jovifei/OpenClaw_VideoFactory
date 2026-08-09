"""T05 / stage-four ② (part 2) — Storyboard → Timeline compiler.

Covers architecture §4.2 (compilation rules R1–R7) and the full §4.3 error-code
table (all 10 domain error codes get at least one negative case).

The compiler is a **pure function** (``compile_storyboard``) — no I/O, no
wall-clock, no randomness — so it is exhaustively testable without any render.

Run from the repository root (see ``tests/video/__init__.py``, deviation D5):
    <envs/default python> -m pytest tests/video/test_storyboard_compile.py -v
"""

from __future__ import annotations

import copy
import json

import pytest

from src.factory.assets.pink_pig.loader import load_registry
from video_factory.pipeline.storyboard import (
    StoryboardError,
    compile_storyboard,
    validate_storyboard,
)
from video_factory.pipeline.timeline import rendered_duration_seconds
from video_factory.pipeline.validation import SchemaValidationError

from . import ROOT

EXAMPLE_PATH = ROOT / "examples" / "pink_pig_story_demo" / "storyboard.json"
REGISTRY_VERSION = "1.0.0"
CHARACTER_ID = "pink_pig"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry():
    """The real shipped Pink Pig registry (co-located ``registry.json``)."""
    return load_registry()


@pytest.fixture(scope="module")
def example_doc() -> dict:
    """The shipped, schema-valid demo storyboard (happy path)."""
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _compile(doc: dict, reg) -> dict:
    """Compile *doc* against *reg* with the repo root wired in."""
    return compile_storyboard(doc, reg, repo_root=ROOT)


# ---------------------------------------------------------------------------
# R1 — Asset binding (IP consistency guarantee)
# ---------------------------------------------------------------------------


class TestR1AssetBinding:
    def test_scene_poses_resolve_to_the_expected_assets(self, example_doc, registry) -> None:
        """Each ``pose`` in the demo maps to the matching render-ready asset."""
        tl = _compile(example_doc, registry)
        by_id = {s["scene_id"]: s["asset_id"] for s in tl["scenes"]}
        expected = {
            "s01": "pink_pig.normal.v1",
            "s02": "pink_pig.thinking.v1",
            "s03": "pink_pig.measure.v1",
            "s04": "pink_pig.repair.v1",
            "s05": "pink_pig.success.v1",
        }
        assert by_id == expected

    def test_mood_index_resolves_through_pose(self, example_doc, registry) -> None:
        """R1 — ``mood`` falls through ``mood_index`` → ``pose_index`` → asset."""
        doc = copy.deepcopy(example_doc)
        # s01 declares mood "calm" (→ pose "normal"); drop asset_id/pose to force mood path.
        doc["scenes"][0]["asset_id"] = None
        doc["scenes"][0]["pose"] = None
        tl = _compile(doc, registry)
        assert tl["scenes"][0]["asset_id"] == "pink_pig.normal.v1"

    def test_non_render_ready_pose_falls_back_to_a_render_ready_asset(
        self, example_doc, registry
    ) -> None:
        """R1 — ``render_ready: false`` pose must resolve to its ``fallback_asset_id``."""
        doc = copy.deepcopy(example_doc)
        doc["scenes"][0]["asset_id"] = "pink_pig.question.v1"  # not render-ready
        tl = _compile(doc, registry)
        resolved = tl["scenes"][0]["asset_id"]
        assert resolved == "pink_pig.normal.v1"
        assert resolved != "pink_pig.question.v1"


# ---------------------------------------------------------------------------
# R2 — Duration derivation
# ---------------------------------------------------------------------------


class TestR2Duration:
    def test_auto_mode_uses_default_scene_seconds(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        # s01 uses duration_intent.mode == "auto" → globals.default_scene_seconds (2.5)
        assert tl["scenes"][0]["duration"] == 2.5

    def test_fixed_mode_uses_explicit_seconds(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        # s05 uses duration_intent.mode == "fixed", seconds 3.0
        assert tl["scenes"][4]["duration"] == 3.0

    def test_narration_mode_scales_with_character_count(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        # s02 "先仔细思考一下需要做什么。" = 13 chars / narration_cps 5.0 = 2.6 (matches timeline.json).
        narration = example_doc["scenes"][1]["narration"]
        expected = min(8.0, max(1.2, len(narration) / 5.0))
        assert tl["scenes"][1]["duration"] == pytest.approx(expected, abs=0.001)

    def test_durations_are_clamped_within_bounds(self, example_doc, registry) -> None:
        # Force an absurd narration length; the clamp must keep it <= max_scene_seconds.
        doc = copy.deepcopy(example_doc)
        doc["scenes"][2]["narration"] = "字" * 1000
        tl = _compile(doc, registry)
        assert tl["scenes"][2]["duration"] <= 8.0


# ---------------------------------------------------------------------------
# R3 — Transition resolution (last scene forced to "none")
# ---------------------------------------------------------------------------


class TestR3Transition:
    def test_non_terminal_transitions_are_preserved(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        assert [s["transition"] for s in tl["scenes"][:-1]] == ["fade", "zoom", "slide", "fade"]

    def test_last_scene_transition_is_forced_to_none(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        assert tl["scenes"][-1]["transition"] == "none"

    def test_explicit_none_on_last_scene_is_kept(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][-1]["transition_out"] = "none"
        tl = _compile(doc, registry)
        assert tl["scenes"][-1]["transition"] == "none"


# ---------------------------------------------------------------------------
# R4 — Order (deterministic ascending sort)
# ---------------------------------------------------------------------------


class TestR4Order:
    def test_scenes_are_sorted_by_order_ascending(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        # Shuffle the order field while keeping unique orders.
        doc["scenes"][0]["order"] = 5
        doc["scenes"][1]["order"] = 3
        doc["scenes"][2]["order"] = 1
        doc["scenes"][3]["order"] = 2
        doc["scenes"][4]["order"] = 4
        tl = _compile(doc, registry)
        assert [s["order"] for s in tl["scenes"]] == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# R5 — Caption (falls back to narration)
# ---------------------------------------------------------------------------


class TestR5Caption:
    def test_null_caption_falls_back_to_narration(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        for scene in tl["scenes"]:
            assert scene["caption"] == scene["narration"]

    def test_explicit_caption_is_preserved(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][0]["caption"] = "自定义字幕"
        tl = _compile(doc, registry)
        assert tl["scenes"][0]["caption"] == "自定义字幕"


# ---------------------------------------------------------------------------
# R7 — Total duration (rendered timeline duration formula)
# ---------------------------------------------------------------------------


class TestR7TotalDuration:
    def test_total_duration_matches_the_rendered_duration_formula(
        self, example_doc, registry
    ) -> None:
        tl = _compile(example_doc, registry)
        expected = rendered_duration_seconds(tl["scenes"], tl["transition_seconds"])
        assert tl["total_duration_seconds"] == expected

    def test_total_duration_equals_sum_minus_overlap(self, example_doc, registry) -> None:
        tl = _compile(example_doc, registry)
        n = len(tl["scenes"])
        s = tl["transition_seconds"]
        manual = round(sum(sc["duration"] for sc in tl["scenes"]) - s * (n - 1), 3)
        assert tl["total_duration_seconds"] == manual


# ---------------------------------------------------------------------------
# Determinism (the compile must be byte-identical across runs)
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_compile_is_deterministic_across_three_runs(self, example_doc, registry) -> None:
        blobs = [json.dumps(_compile(example_doc, registry), sort_keys=True, ensure_ascii=False)
                 for _ in range(3)]
        assert blobs[0] == blobs[1] == blobs[2]

    def test_compiled_timeline_has_no_wall_clock_fields(self, example_doc, registry) -> None:
        """R6 — the timeline stays free of any wall-clock / generated_at field."""
        tl = _compile(example_doc, registry)
        assert "generated_at" not in tl
        for scene in tl["scenes"]:
            assert "generated_at" not in scene


# ---------------------------------------------------------------------------
# §4.3 error-code coverage — negative cases
# ---------------------------------------------------------------------------


class TestErrorCodes:
    def test_registry_version_mismatch(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["ip"]["registry_version"] = "9.9.9"
        with pytest.raises(StoryboardError, match="registry_version_mismatch"):
            _compile(doc, registry)

    def test_character_mismatch(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["ip"]["character_id"] = "not_pink_pig"
        with pytest.raises(StoryboardError, match="character_mismatch"):
            _compile(doc, registry)

    def test_scene_order_invalid(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][1]["order"] = 99  # breaks 1..N contiguity
        with pytest.raises(StoryboardError, match="scene_order_invalid"):
            validate_storyboard(doc)

    def test_scene_id_duplicated(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][1]["scene_id"] = "s01"
        with pytest.raises(StoryboardError, match="scene_id_duplicated"):
            validate_storyboard(doc)

    def test_asset_unresolved(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][0]["asset_id"] = "pink_pig.does_not_exist.v9"
        doc["scenes"][0]["pose"] = None
        doc["scenes"][0]["mood"] = None
        with pytest.raises(StoryboardError, match="asset_unresolved"):
            _compile(doc, registry)

    def test_scene_duration_invalid_constructible_under_low_floor(
        self, example_doc, registry
    ) -> None:
        """§4.3 row 8.

        With the DEFAULT globals (``min_scene_seconds`` = 1.2, ``transition_seconds``
        = 0.4) the clamp floor (1.2) is always > transition_seconds, so
        ``scene_duration_invalid`` is *not* reachable — that is the t03 finding.
        It becomes reachable when the globals allow a floor below the transition
        length (here ``min_scene_seconds`` 0.25 ≤ ``transition_seconds`` 0.4 and a
        fixed 0.25 s scene). This proves the code path is real, not dead.
        """
        doc = copy.deepcopy(example_doc)
        doc["globals"]["min_scene_seconds"] = 0.25
        doc["globals"]["transition_seconds"] = 0.4
        doc["scenes"][0]["duration_intent"] = {"mode": "fixed", "seconds": 0.25}
        with pytest.raises(StoryboardError, match="scene_duration_invalid"):
            _compile(doc, registry)

    def test_transition_unsupported(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][0]["transition_out"] = "dissolve"  # non-terminal scene
        with pytest.raises(StoryboardError, match="transition_unsupported"):
            _compile(doc, registry)

    def test_narration_empty(self, example_doc, registry) -> None:
        doc = copy.deepcopy(example_doc)
        doc["scenes"][0]["narration"] = ""
        doc["scenes"][0]["caption"] = None
        with pytest.raises(StoryboardError, match="narration_empty"):
            validate_storyboard(doc)

    def test_storyboard_schema_invalid_emits_structured_contract(
        self, example_doc, registry
    ) -> None:
        """Schema failures use a stable code with path in structured context."""
        broken = copy.deepcopy(example_doc)
        broken["scenes"][0]["order"] = "first"  # wrong type → schema failure
        from video_factory.pipeline.validation import validate as _validate

        with pytest.raises(SchemaValidationError) as exc:
            _validate(broken, "storyboard")
        assert exc.value.code == "storyboard_schema_invalid"
        assert exc.value.context["path"] == "scenes.0.order"

    def test_asset_fallback_cycle_covered_in_registry_suite(self, registry) -> None:
        """§4.3 row 7 — asserted in ``test_registry.py::TestFallbackFailureModes``.

        ``compile_storyboard`` swallows registry errors into ``asset_unresolved``, so
        the raw ``asset_fallback_cycle`` code can only be observed through
        ``registry.resolve()`` directly. We assert the resolver exists and documents
        the cycle contract here (the concrete raise lives in the registry suite).
        """
        assert hasattr(registry, "resolve")
