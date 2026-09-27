from __future__ import annotations

import pytest

from video_factory.pipeline.audio_planner import NarrationDurationBudgetError, allocate_scene_durations
from video_factory.pipeline.narration_timing import rewrite_narration_once, storyboard_with_narration


def test_allocate_scene_durations_is_measured_and_frame_aligned() -> None:
    timeline = {
        "fps": 30,
        "transition_mode": "technical_cut",
        "transition_seconds": 0.4,
        "scenes": [{"scene_id": "s01", "duration": 2.0}, {"scene_id": "s02", "duration": 2.0}],
    }
    allocated = allocate_scene_durations(
        timeline,
        ({"actual_duration": 2.01}, {"actual_duration": 2.21}),
        tail_margin_seconds=0.2,
        min_total_seconds=0.0,
    )
    assert allocated["scenes"][0]["duration"] == 2.233
    assert allocated["scenes"][1]["duration"] == 2.433
    assert allocated["total_duration_seconds"] == 4.666


def test_allocate_scene_durations_fails_over_phase1_upper_bound() -> None:
    with pytest.raises(NarrationDurationBudgetError, match="narration_duration_budget_exceeded"):
        allocate_scene_durations(
            {"fps": 30, "transition_mode": "technical_cut", "scenes": [{"duration": 2.0}] * 5},
            tuple({"actual_duration": 13.0} for _ in range(5)),
            tail_margin_seconds=0.2,
        )


def test_fixed_fixture_rewrite_preserves_fact_bindings() -> None:
    script = {"beats": [
        {"narration": "原句一", "fact_refs": ["mutex_task_ownership"]},
        {"narration": "原句二", "fact_refs": ["isr_nonblocking_boundary"]},
        {"narration": "原句三", "fact_refs": ["priority_inheritance_context"]},
        {"narration": "原句四", "fact_refs": ["short_isr_handler"]},
        {"narration": "原句五", "fact_refs": ["mutex_task_ownership"]},
    ]}
    brief = {"facts": [{"fact_id": value} for value in {
        "mutex_task_ownership", "isr_nonblocking_boundary", "priority_inheritance_context", "short_isr_handler",
    }]}
    rewritten, meta = rewrite_narration_once(script, brief)
    assert meta["topic_kind"] == "freertos_mutex"
    assert [beat["fact_refs"] for beat in rewritten["beats"]] == [beat["fact_refs"] for beat in script["beats"]]
    assert all(rewritten_beat["narration"] != original["narration"] for rewritten_beat, original in zip(rewritten["beats"], script["beats"]))


def test_storyboard_with_narration_changes_only_narration() -> None:
    storyboard = {"globals": {"fps": 30}, "scenes": [
        {"scene_id": "s01", "narration": "old", "caption": "keep", "duration": 2.0},
    ]}
    result = storyboard_with_narration(storyboard, {"beats": [{"narration": "new"}]})
    assert result["scenes"][0]["narration"] == "new"
    assert result["scenes"][0]["caption"] == "keep"
    assert storyboard["scenes"][0]["narration"] == "old"
