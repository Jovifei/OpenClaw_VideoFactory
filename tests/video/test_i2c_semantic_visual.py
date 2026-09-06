from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.factory.phase1_topic import (
    build_director_script,
    build_scene_plan,
    build_topic_request,
    review_candidate_prose,
    select_candidate,
    build_research_brief,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def i2c_research() -> dict:
    return json.loads((ROOT / "examples" / "phase1_subject_i2c" / "research_brief.json").read_text(encoding="utf-8"))


def test_i2c_paraphrase_binds_only_the_verified_open_drain_fact(i2c_research: dict) -> None:
    result = review_candidate_prose(
        "I2C输出端只能把线路拉低，高电平交给上拉电阻恢复。", i2c_research
    )
    assert result["status"] == "passed"
    assert result["sentences"][0]["fact_refs"] == ["open_drain"]


def test_i2c_editorial_review_rejects_an_unbound_engineering_addition(i2c_research: dict) -> None:
    result = review_candidate_prose(
        "上拉电阻还能自动修复总线故障。", i2c_research
    )
    assert result["status"] == "rejected"
    assert result["sentences"][0]["reason"] == "unbound_factual_sentence"


def test_i2c_editorial_review_rejects_contradictory_paraphrase(i2c_research: dict) -> None:
    result = review_candidate_prose(
        "I2C不需要上拉电阻，线路会自己恢复高电平。", i2c_research
    )
    assert result["status"] == "rejected"
    assert result["sentences"][0]["reason"] == "contradiction_marker"


def test_i2c_scene_plan_emits_source_bound_bus_diagram(i2c_research: dict) -> None:
    request = build_topic_request(subject=i2c_research["topic"], duration=40, aspect="16:9")
    script = build_director_script(
        request,
        i2c_research,
        {"script": "为什么I2C总线要上拉？I2C线路通常采用开漏结构；器件主动拉低，释放后由上拉电阻恢复高电平。上拉电阻与总线电容决定上升沿；电阻过大可能使线路来不及达到有效高电平。电阻过小则增加低电平灌电流，可能超出器件的拉低能力；阻值必须兼顾两端限制。"},
    )
    plan = build_scene_plan(script, i2c_research)
    diagrams = [scene["visual_spec"] for scene in plan["scenes"] if "visual_spec" in scene]
    assert len(diagrams) == 3
    assert all(item["kind"] == "i2c_bus_v1" for item in diagrams)
    assert {ref for item in diagrams for ref in item["fact_refs"]} == {"open_drain", "rise_time", "sink_current"}
    assert diagrams[0]["labels"] == ["SDA", "SCL", "START", "ADDRESS", "ACK/NACK", "DATA", "STOP"]


def test_i2c_source_bound_candidate_can_reach_the_existing_threshold(i2c_research: dict) -> None:
    prose = "为什么I2C总线要上拉？I2C线路通常采用开漏结构；器件主动拉低，释放后由上拉电阻恢复高电平。上拉电阻与总线电容决定上升沿；电阻过大可能使线路来不及达到有效高电平。电阻过小则增加低电平灌电流，可能超出器件的拉低能力；阻值必须兼顾两端限制。"
    candidates = {"schema_version": "1.0", "mpt_version": "1.3.5", "mpt_commit": "eb8c23757e098a07bbcd93b3b50e252fc8d1869a", "candidates": [{"candidate": i, "script": prose} for i in (1, 2, 3)]}
    selected = select_candidate(candidates, i2c_research, duration_target_seconds=40)
    assert selected["score_breakdown"]["total"] >= 85


def test_research_brief_round_trip_preserves_editorial_contract(i2c_research: dict) -> None:
    rebuilt = build_research_brief(topic=i2c_research["topic"], sources=i2c_research["sources"], facts=i2c_research["facts"], comparables=i2c_research["comparables"], editorial_contract=i2c_research["editorial_contract"])
    assert rebuilt["editorial_contract"] == i2c_research["editorial_contract"]
