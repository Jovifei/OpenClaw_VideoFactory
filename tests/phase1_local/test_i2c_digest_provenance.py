from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.factory.director.context import normalize_topic
from src.factory.phase1_local import build_local_plan, load_local_brief
from video_factory.pipeline.errors import FactoryContractError


ROOT = Path(__file__).resolve().parents[2]
STALE = ROOT / "examples/phase1_subject_i2c/phase1_local_brief_9x16.json"
REPAIRED = ROOT / "examples/phase1_subject_i2c/phase1_local_brief_9x16_repaired.json"


def test_stale_historical_i2c_digest_is_rejected() -> None:
    brief = load_local_brief(STALE)
    with pytest.raises(FactoryContractError) as caught:
        build_local_plan(brief, ROOT)
    assert caught.value.code == "phase1_local_brief_invalid"
    assert caught.value.context["field"] == "factual_brief.topic_digest"
    assert caught.value.context["reason"] == "topic_digest_mismatch"


def test_repaired_i2c_brief_uses_current_digest_and_preserves_contract() -> None:
    brief = load_local_brief(REPAIRED)
    plan = build_local_plan(brief, ROOT)
    expected = hashlib.sha256(normalize_topic(str(brief["topic"])).encode("utf-8")).hexdigest()

    assert plan["topic"] == "I2C总线为什么要上拉电阻"
    assert plan["topic_digest"] == expected
    assert plan["script"]["topic_digest"] == expected
    assert plan["factual_brief"]["topic_digest"] == expected
    assert {item["fact_id"] for item in plan["factual_brief"]["facts"]} == {
        "open_drain",
        "rise_time",
        "sink_current",
    }
    assert {source["source_id"] for source in plan["factual_brief"]["sources"]} == {
        "nxp_um10204",
        "ti_slva689",
    }
    assert plan["render_profile"]["aspect_ratio"] == "9:16"
    assert plan["render_profile"]["width"] == 1080
    assert plan["render_profile"]["height"] == 1920
    assert plan["render_profile"]["fps"] == 30
