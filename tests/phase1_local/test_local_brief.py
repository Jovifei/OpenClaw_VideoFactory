from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate


ROOT = Path(__file__).resolve().parents[2]


def _brief(topic: str = "用小粉猪讲清 Modbus RTU") -> dict[str, object]:
    digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    return {
        "schema_version": "1.0",
        "input_mode": "topic",
        "topic": topic,
        "factual_brief": {
            "schema_version": "1.0",
            "topic_digest": digest,
            "facts": [
                {
                    "fact_id": "fact_protocol_frame",
                    "claim": "Modbus RTU uses a structured request and response frame.",
                    "source_ids": ["source_standard"],
                }
            ],
            "sources": [
                {
                    "source_id": "source_standard",
                    "title": "Modbus Application Protocol",
                    "publisher": "Modbus Organization",
                    "url": "https://example.test/modbus-protocol",
                    "kind": "standard",
                },
                {
                    "source_id": "source_serial",
                    "title": "Modbus Serial Line Protocol",
                    "publisher": "Modbus Organization",
                    "url": "https://example.test/modbus-serial",
                    "kind": "official_document",
                },
            ],
            "review_status": "verified",
        },
    }


def _write_brief(tmp_path: Path, value: dict[str, object]) -> Path:
    path = tmp_path / "local_brief.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def test_topic_brief_builds_deterministic_existing_director_artifacts(tmp_path: Path) -> None:
    brief = load_local_brief(_write_brief(tmp_path, _brief()))
    first = build_local_plan(brief, ROOT)
    second = build_local_plan(brief, ROOT)
    expected_digest = hashlib.sha256(str(brief["topic"]).encode("utf-8")).hexdigest()
    assert first["job_id"] == f"phase1_{expected_digest[:16]}"
    assert first["topic_digest"] == expected_digest
    assert first["script"] == second["script"]
    assert first["storyboard"] == second["storyboard"]
    assert first["asset_selection"] == second["asset_selection"]
    assert first["script"]["script_id"] == f"script_{expected_digest[:16]}"
    assert len(first["script"]["beats"]) == 5
    assert first["script"]["beats"][0]["purpose"] == "hook"
    assert first["script"]["beats"][-1]["purpose"] == "summary"
    assert all(scene["asset_id"] for scene in first["storyboard"]["scenes"])
    assert len(first["asset_selection"]["selections"]) == 5
    validate(first["script"], "director_script")
    validate(first["storyboard"], "storyboard")
    validate(first["asset_selection"], "asset_selection_report")


@pytest.mark.parametrize(
    ("mode", "extra"),
    [
        ("authorized_public_research", {"research_authorization_id": "JOVI-RESEARCH-001"}),
    ],
)
def test_future_input_modes_are_schema_valid_but_fail_closed(mode: str, extra: dict[str, str], tmp_path: Path) -> None:
    value = _brief()
    value["input_mode"] = mode
    value.update(extra)
    brief = load_local_brief(_write_brief(tmp_path, value))
    with pytest.raises(FactoryContractError) as caught:
        build_local_plan(brief, ROOT)
    assert caught.value.code == "phase1_local_input_mode_unsupported"
    assert caught.value.context == {"input_mode": mode, "reason": "not_implemented"}


def test_local_reference_requires_verified_analyzer_context(tmp_path: Path) -> None:
    value = _brief()
    value.update(
        {
            "input_mode": "local_reference",
            "reference_sha256": "a" * 64,
            "reference_abstraction": {
                "pace": "medium",
                "scene_count_band": "2-4",
                "median_shot_duration_seconds": 3.0,
                "shot_density_per_second": 0.1,
                "structure": ["hook", "explain", "evidence", "repair", "summary"],
                "duration_target_seconds": 40,
            },
        }
    )
    brief = load_local_brief(_write_brief(tmp_path, value))
    with pytest.raises(FactoryContractError) as caught:
        build_local_plan(brief, ROOT)
    assert caught.value.code == "phase1_reference_context_required"

    plan = build_local_plan(
        brief,
        ROOT,
        reference_context={
            "source_sha256": "a" * 64,
            "policy_version": "reference-analysis-v1",
            "analysis_verified": True,
        },
    )
    assert plan["job_id"].startswith("phase1_ref_")
    assert plan["script"]["duration_target_seconds"] == 40


@pytest.mark.parametrize("field", ["asset_id", "path", "render", "provider_prompt"])
def test_brief_rejects_factory_control_fields(field: str, tmp_path: Path) -> None:
    value = _brief()
    value[field] = "must-not-enter-brief"
    with pytest.raises(FactoryContractError) as caught:
        load_local_brief(_write_brief(tmp_path, value))
    assert caught.value.code == "phase1_local_brief_invalid"


def test_digest_and_verified_factual_review_are_semantic_requirements(tmp_path: Path) -> None:
    mismatch = _brief()
    mismatch["factual_brief"]["topic_digest"] = "0" * 64  # type: ignore[index]
    with pytest.raises(FactoryContractError) as caught:
        build_local_plan(load_local_brief(_write_brief(tmp_path, mismatch)), ROOT)
    assert caught.value.code == "phase1_local_brief_invalid"
    assert caught.value.context["reason"] == "topic_digest_mismatch"

    unverified = _brief()
    unverified["factual_brief"]["review_status"] = "unreviewed"  # type: ignore[index]
    with pytest.raises(FactoryContractError) as caught:
        build_local_plan(load_local_brief(_write_brief(tmp_path, unverified)), ROOT)
    assert caught.value.code == "phase1_local_brief_invalid"
    assert caught.value.context["reason"] == "factual_brief_not_verified"
