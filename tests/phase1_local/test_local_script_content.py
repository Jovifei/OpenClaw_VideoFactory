from __future__ import annotations

import hashlib
from pathlib import Path

from src.factory.director.context import normalize_topic
from src.factory.phase1_local import build_local_plan, load_local_brief


ROOT = Path(__file__).resolve().parents[2]


def test_flash_watchdog_fixture_uses_reviewed_topic_copy() -> None:
    brief = load_local_brief(ROOT / "examples/phase1_local_flash_watchdog/brief.json")
    plan = build_local_plan(brief, ROOT)
    script = plan["script"]
    narration = [str(beat["narration"]) for beat in script["beats"]]

    assert script["topic_digest"] == hashlib.sha256(normalize_topic(str(brief["topic"])).encode("utf-8")).hexdigest()
    assert len(narration) == 5
    assert any("独立看门狗" in item for item in narration)
    assert any("服务窗口" in item for item in narration)
    assert not any("对象、边界、输入输出" in item for item in narration)
    assert not any("。。" in item for item in narration)
    assert script["beats"][1]["fact_refs"] == ["flash_erase_sequence"]
    assert set(script["beats"][2]["fact_refs"]) == {
        "iwdg_independent_timeout",
        "service_window_is_budget",
    }


def test_generic_script_removes_duplicate_claim_punctuation(tmp_path: Path) -> None:
    topic = "测试一个已核验主题"
    digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    brief = {
        "schema_version": "1.0",
        "input_mode": "topic",
        "topic": topic,
        "factual_brief": {
            "schema_version": "1.0",
            "topic_digest": digest,
            "review_status": "verified",
            "facts": [
                {
                    "fact_id": "fact_one",
                    "claim": "这是一个带句号的事实。",
                    "source_ids": ["source_one"],
                }
            ],
            "sources": [
                {
                    "source_id": "source_one",
                    "title": "测试资料",
                    "publisher": "测试机构",
                    "url": "https://example.test/source",
                    "kind": "official_document",
                },
                {
                    "source_id": "source_two",
                    "title": "补充资料",
                    "publisher": "测试机构",
                    "url": "https://example.test/source-2",
                    "kind": "standard",
                },
            ],
        },
    }
    plan = build_local_plan(brief, ROOT)
    evidence = str(plan["script"]["beats"][2]["narration"])
    assert evidence == "已核验事实是：这是一个带句号的事实。"
    assert "。。" not in str(plan["script"]["narration"])
