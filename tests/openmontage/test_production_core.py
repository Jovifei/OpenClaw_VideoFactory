from third_party.openmontage.delivery_promise import PromiseType, classify_from_brief
from third_party.openmontage.slideshow_risk import score_slideshow_risk
from third_party.openmontage.verify_scene_pacing import verify_scene_pacing


def test_delivery_promise_rejects_slide_fallback_for_motion_led() -> None:
    promise = classify_from_brief("cinematic", {"motion_required": True})
    assert promise.promise_type is PromiseType.MOTION_LED
    result = promise.validate_cuts([{"type": "text_card"}, {"type": "chart"}, {"type": "video"}])
    assert result["valid"] is False
    assert result["motion_ratio"] == 1 / 3


def test_slideshow_risk_fails_empty_plan_and_accepts_directed_variety() -> None:
    assert score_slideshow_risk([])["verdict"] == "fail"
    scenes = [
        {"type": f"technical_{i}", "description": f"unique {i}", "information_role": "teach",
         "shot_intent": "reveal evidence", "shot_language": {"shot_size": size, "camera_movement": "push"}}
        for i, size in enumerate(("wide", "medium", "close", "detail", "wide"))
    ]
    assert score_slideshow_risk(scenes, renderer_family="technical_explainer")["verdict"] in {"strong", "acceptable"}


def test_scene_pacing_reports_duration_and_scene_count_failures() -> None:
    result = verify_scene_pacing(
        [{"duration_seconds": 1.0}, {"duration_seconds": 20.0}],
        target_duration_seconds=30.0,
        min_scenes=5,
        max_scenes=9,
    )
    assert result["valid"] is False
    assert "scene_count" in result["violations"]
    assert "total_duration" in result["violations"]
