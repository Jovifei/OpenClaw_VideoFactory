from __future__ import annotations

import json
from pathlib import Path

import pytest
from video_factory.pipeline import validation

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from src.factory.phase1_topic import (
    estimate_narration_duration_seconds,
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


def test_subject_policy_uses_vendored_openmontage_commit() -> None:
    provenance = json.loads(Path("third_party/openmontage/PROVENANCE.json").read_text(encoding="utf-8"))
    approved = provenance["upstream_commit"]
    assert OPENMONTAGE_COMMIT == approved
    assert approved in stable_subject_key(build_topic_request(subject="看门狗"))


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


@pytest.mark.parametrize("url", ["relative/path", "ftp://host/a", "https:///missing-host"])
def test_research_rejects_non_http_absolute_urls(url: str) -> None:
    sources = [{"id":"a","url":url,"title":"a","kind":"official_document"},{"id":"b","url":"https://x/b","title":"b","kind":"research_paper"}]
    with pytest.raises(FactoryContractError):
        build_research_brief(topic="x", sources=sources, facts=[{"id":"f","claim":"事实","source_ids":["a"]}])


def test_research_rejects_duplicate_fact_and_source_ids() -> None:
    with pytest.raises(FactoryContractError):
        build_research_brief(topic="x", sources=[{"id":"a","url":"https://x/a","title":"a","kind":"official_document"},{"id":"a","url":"https://x/b","title":"b","kind":"research_paper"}], facts=[{"id":"f","claim":"事实","source_ids":["a"]}])
    with pytest.raises(FactoryContractError):
        build_research_brief(topic="x", sources=[{"id":"a","url":"https://x/a","title":"a","kind":"official_document"},{"id":"b","url":"https://x/b","title":"b","kind":"research_paper"}], facts=[{"id":"f","claim":"事实一","source_ids":["a"]},{"id":"f","claim":"事实二","source_ids":["b"]}])


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
    candidates = ingest_mpt_candidates(mpt_document(["看门狗故障：看门狗用于检测软件失去响应，喂狗窗口应由最坏执行时间决定。原理配置验证。", "看门狗故障：看门狗用于检测软件失去响应，喂狗窗口应由最坏执行时间决定。原理配置验证。", "短"] ))
    selected = select_candidate(candidates, research(), rewrite_attempt=0)
    validate(selected, "phase1_selected_script")
    assert selected["selected_candidate"] == 1
    assert selected["score_breakdown"]["total"] >= 85
    weak = ingest_mpt_candidates(mpt_document(["短", "也短", "仍短"]))
    with pytest.raises(FactoryContractError) as exc:
        select_candidate(weak, research(), rewrite_attempt=1)
    assert exc.value.context["reason"] == "selection_threshold_not_met"


def test_director_script_and_scene_plan_preserve_fact_refs_and_variety() -> None:
    candidates = ingest_mpt_candidates(mpt_document(["看门狗用于检测软件失去响应。喂狗窗口应由最坏执行时间决定。然后配置、验证并总结。"] * 3))
    selected = select_candidate(candidates, research())
    script = build_director_script(build_topic_request(subject="看门狗定时器"), research(), selected)
    validate(script, "director_script")
    plan = build_scene_plan(script, research())
    validate(plan, "phase1_scene_plan")
    assert 5 <= len(plan["scenes"]) <= 9
    assert len({scene["visual_type"] for scene in plan["scenes"]}) >= 3
    assert {ref for scene in plan["scenes"] for ref in scene["source_refs"]} == {"fact1", "fact2"}
    assert all(len({s["visual_type"] for s in plan["scenes"][i:i+3]}) > 1 for i in range(len(plan["scenes"]) - 2))
    assert plan["scenes"][0]["information_role"] == "hook_question"
    assert plan["scenes"][0]["source_refs"] == []
    assert all(scene["source_refs"] for scene in plan["scenes"][1:])


def test_selected_prose_changes_director_beats_and_only_matching_claims_get_refs() -> None:
    request = build_topic_request(subject="看门狗定时器")
    brief = research()
    first = {"script":"看门狗用于检测软件失去响应。工程师配置超时，然后验证恢复。"}
    second = {"script":"喂狗窗口应由最坏执行时间决定。工程师测量边界，然后记录结论。"}
    a = build_director_script(request, brief, first)
    b = build_director_script(request, brief, second)
    assert a["beats"][0]["narration"] != b["beats"][0]["narration"]
    assert a["beats"][1:] == b["beats"][1:]
    assert {ref for beat in a["beats"][1:] for ref in beat["fact_refs"]} == {"fact1", "fact2"}


def test_contradictory_keyword_overlap_never_scores_or_binds_facts() -> None:
    brief = research()
    prose = "看门狗用于检测软件失去响应只是关键词，并非真实原理；喂狗窗口无需由最坏执行时间决定。"
    candidates = ingest_mpt_candidates(mpt_document([prose] * 3))
    with pytest.raises(FactoryContractError) as exc:
        select_candidate(candidates, brief, rewrite_attempt=1)
    assert exc.value.context["best_score"] < 85
    script = build_director_script(build_topic_request(subject="看门狗定时器"), brief, {"script": prose})
    assert not script["beats"][0]["fact_refs"]
    assert prose not in script["narration"]


def test_grounded_claim_anchors_pass_without_copying_unbound_opening_prose() -> None:
    brief = research()
    grounded_a = "为什么系统会突然重启？看门狗用于检测软件失去响应。喂狗窗口应由最坏执行时间决定。"
    grounded_b = "先别急着重启。看门狗用于检测软件失去响应。喂狗窗口应由最坏执行时间决定。"
    selected = select_candidate(ingest_mpt_candidates(mpt_document([grounded_a] * 3)), brief)
    assert selected["score_breakdown"]["factual_consistency"] == 100
    request = build_topic_request(subject="看门狗定时器")
    first = build_director_script(request, brief, {"script": grounded_a})
    second = build_director_script(request, brief, {"script": grounded_b})
    assert first["beats"][0]["narration"] == second["beats"][0]["narration"]
    assert "为什么系统会突然重启" not in first["narration"]
    assert "先别急着重启" not in second["narration"]
    assert all(beat["fact_refs"] for beat in first["beats"][1:])


@pytest.mark.parametrize("target_seconds", [25, 40, 60])
def test_director_script_expands_grounded_chinese_narration_to_requested_budget(target_seconds: int) -> None:
    brief = research()
    request = build_topic_request(subject="看门狗定时器", duration=target_seconds)
    selected = {"script": "先核对日志：看门狗用于检测软件失去响应。再记录边界：喂狗窗口应由最坏执行时间决定。"}
    script = build_director_script(request, brief, selected)

    estimate = estimate_narration_duration_seconds(script["narration"])
    assert target_seconds * 0.8 <= estimate <= target_seconds
    assert 5 <= len(script["beats"]) <= 9
    assert any(beat["purpose"] == "hook" for beat in script["beats"])
    assert all(beat["fact_refs"] for beat in script["beats"] if beat["fact_refs"])
    assert "软件会自动修复" not in script["narration"]
    assert "最坏执行时间决定" in script["narration"]


def test_director_script_uses_only_grounded_selected_safe_framing_and_expands_short_input_deterministically() -> None:
    brief = research()
    request = build_topic_request(subject="看门狗定时器", duration=40)
    grounded = {"script": "先核对日志：看门狗用于检测软件失去响应。再记录边界：喂狗窗口应由最坏执行时间决定。软件会自动修复所有故障。"}
    first = build_director_script(request, brief, grounded)
    second = build_director_script(request, brief, grounded)

    assert first == second
    assert "先核对日志" in first["narration"]
    assert "软件会自动修复所有故障" not in first["narration"]
    for beat in first["beats"]:
        if beat["fact_refs"]:
            assert set(beat["fact_refs"]).issubset({"fact1", "fact2"})
        else:
            assert beat["purpose"] == "hook"
