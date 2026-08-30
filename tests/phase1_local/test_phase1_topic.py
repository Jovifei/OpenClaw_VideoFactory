from __future__ import annotations

import json
from pathlib import Path

import pytest
from video_factory.pipeline import validation

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from src.factory.phase1_topic import (
    MPT_COMMIT,
    OPENMONTAGE_COMMIT,
    build_director_script,
    build_research_brief,
    build_scene_plan,
    build_topic_request,
    ingest_mpt_candidates,
    select_candidate,
    stable_subject_key,
)


def research() -> dict:
    return build_research_brief(
        topic="  看门狗 定时器  ",
        sources=[
            {"id": "src1", "url": "https://vendor.example/watchdog", "title": "芯片手册", "kind": "official_document"},
            {"id": "src2", "url": "https://lab.example/reliability", "title": "可靠性研究", "kind": "research_paper"},
        ],
        facts=[
            {"id": "fact1", "claim": "看门狗用于检测软件失去响应。", "source_ids": ["src1"]},
            {"id": "fact2", "claim": "喂狗窗口应由最坏执行时间决定。", "source_ids": ["src1", "src2"]},
        ],
        comparables=[{"url": "https://video.example/a", "title": "拆解", "hook_style": "故障反问", "structure": "现象-原理-验证", "pace": "紧凑", "visual_grammar": "框图与时间轴"}],
    )


def mpt_document(scripts: list[str]) -> dict:
    return {
        "schema_version": "1.0", "kind": "phase1_script_drafts", "subject": "看门狗定时器",
        "language": "zh-CN", "requested_candidates": 3, "successful_candidates": 3,
        "mpt_version": "1.3.5", "mpt_commit": MPT_COMMIT,
        "candidates": [{"candidate": index, "script": value, "duration_seconds": 1.0} for index, value in enumerate(scripts, 1)],
        "failures": [],
    }


def test_topic_request_defaults_and_stable_policy_key() -> None:
    request = build_topic_request(subject="  看门狗   定时器 ")
    validate(request, "phase1_topic_request")
    assert request == {"schema_version": "1.0", "subject": "看门狗 定时器", "duration": 40, "aspect": "16:9", "language": "zh-CN", "mascot": "off"}
    assert stable_subject_key(request) == stable_subject_key(build_topic_request(subject="看门狗 定时器"))
    assert OPENMONTAGE_COMMIT in stable_subject_key(request)
    assert MPT_COMMIT in stable_subject_key(request)


@pytest.mark.parametrize("field,value", [("duration", 24), ("aspect", "1:1"), ("mascot", "invented")])
def test_topic_request_rejects_invalid_modes(field: str, value: object) -> None:
    args = {"subject": "看门狗", field: value}
    with pytest.raises(FactoryContractError):
        build_topic_request(**args)


def test_research_requires_unique_sources_primary_kind_and_linked_facts() -> None:
    validate(research(), "phase1_research_brief")
    with pytest.raises(FactoryContractError):
        build_research_brief(topic="x", sources=[{"id": "a", "url": "https://x/a", "title": "a", "kind": "blog"}, {"id": "b", "url": "https://x/b", "title": "b", "kind": "news"}], facts=[{"id": "f", "claim": "c", "source_ids": ["a"]}])
    with pytest.raises(FactoryContractError):
        build_research_brief(topic="x", sources=[{"id": "a", "url": "https://x/a", "title": "a", "kind": "official_document"}, {"id": "b", "url": "https://x/a", "title": "b", "kind": "primary_source"}], facts=[{"id": "f", "claim": "c", "source_ids": ["missing"]}])


@pytest.mark.parametrize("injection", [{"path": "C:/secret"}, {"visual_grammar": {"audio": "x"}}, {"provider": "remote"}])
def test_research_rejects_comparable_control_injection_recursively(injection: dict) -> None:
    doc = research()
    doc["comparables"][0].update(injection)
    with pytest.raises(FactoryContractError):
        build_research_brief(topic=doc["topic"], sources=doc["sources"], facts=doc["facts"], comparables=doc["comparables"])


def test_mpt_ingest_requires_exactly_three_successes_and_no_controls(tmp_path: Path) -> None:
    path = tmp_path / "candidates.json"
    path.write_text(json.dumps(mpt_document(["甲", "乙", "丙"]), ensure_ascii=False), encoding="utf-8")
    result = ingest_mpt_candidates(path)
    validate(result, "phase1_script_candidates")
    bad = mpt_document(["甲", "乙", "丙"])
    bad["temperature"] = 0.7
    path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(FactoryContractError):
        ingest_mpt_candidates(path)


def test_mpt_ingest_rejects_nested_raw_controls_and_noncanonical_ids() -> None:
    nested = mpt_document(["甲", "乙", "丙"])
    nested["candidates"][0]["metadata"] = {"render": {"path": "C:/escape"}}
    with pytest.raises(FactoryContractError) as exc:
        ingest_mpt_candidates(nested)
    assert exc.value.context["reason"] == "forbidden_control"
    duplicate = mpt_document(["甲", "乙", "丙"])
    duplicate["candidates"][2]["candidate"] = 2
    with pytest.raises(FactoryContractError) as exc:
        ingest_mpt_candidates(duplicate)
    assert exc.value.context["reason"] == "candidate_ids_invalid"


def test_new_contracts_fail_closed_without_jsonschema(monkeypatch) -> None:
    monkeypatch.setattr(validation, "is_available", lambda: False)
    with pytest.raises(FactoryContractError) as exc:
        build_topic_request(subject="看门狗")
    assert exc.value.context["reason"] == "schema_validation_unavailable"


def test_selection_threshold_tie_break_and_rewrite_fail_closed() -> None:
    candidates = ingest_mpt_candidates(mpt_document(["看门狗故障 原理 验证 fact1 fact2", "看门狗故障 原理 验证 fact1 fact2", "短"] ))
    selected = select_candidate(candidates, research(), rewrite_attempt=0)
    validate(selected, "phase1_selected_script")
    assert selected["selected_candidate"] == 1
    assert selected["score_breakdown"]["total"] >= 85
    weak = ingest_mpt_candidates(mpt_document(["短", "也短", "仍短"]))
    with pytest.raises(FactoryContractError) as exc:
        select_candidate(weak, research(), rewrite_attempt=1)
    assert exc.value.context["reason"] == "selection_threshold_not_met"


def test_director_script_and_scene_plan_preserve_fact_refs_and_variety() -> None:
    candidates = ingest_mpt_candidates(mpt_document(["看门狗故障 原理 配置 验证 总结 fact1 fact2"] * 3))
    selected = select_candidate(candidates, research())
    script = build_director_script(build_topic_request(subject="看门狗定时器"), research(), selected)
    validate(script, "director_script")
    plan = build_scene_plan(script, research())
    validate(plan, "phase1_scene_plan")
    assert 5 <= len(plan["scenes"]) <= 9
    assert len({scene["visual_type"] for scene in plan["scenes"]}) >= 3
    assert all(scene["source_refs"] for scene in plan["scenes"])
    assert all(len({s["visual_type"] for s in plan["scenes"][i:i+3]}) > 1 for i in range(len(plan["scenes"]) - 2))
