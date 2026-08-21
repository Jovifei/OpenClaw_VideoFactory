from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.factory.director import build_script_prompt, load_director_context, load_factual_brief
from video_factory.pipeline.errors import FactoryContractError


def _brief(topic: str) -> dict:
    digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    return {
        "schema_version": "1.0",
        "topic_digest": digest,
        "facts": [{"fact_id": "fact_1", "claim": "协议使用结构化帧。", "source_ids": ["source_1"]}],
        "sources": [
            {"source_id": "source_1", "title": "Protocol", "publisher": "Official", "url": "https://example.com/1", "kind": "standard"},
            {"source_id": "source_2", "title": "Serial", "publisher": "Official", "url": "https://example.com/2", "kind": "official_document"},
        ],
        "review_status": "verified",
    }


def test_factual_brief_loads_and_prompt_is_sanitized(tmp_path: Path) -> None:
    topic = "介绍 Modbus RTU"
    path = tmp_path / "brief.json"
    path.write_text(json.dumps(_brief(topic), ensure_ascii=False), encoding="utf-8")
    brief = load_factual_brief("brief.json", repo_root=tmp_path, topic=topic)
    assert brief.verified is True
    prompt = build_script_prompt(topic, load_director_context(Path.cwd()), factual_brief=brief)
    assert "DirectorScript" in prompt
    assert "asset_id" in prompt
    assert str(path) not in prompt
    assert "Protocol" in prompt


def test_factual_brief_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "brief.json"
    path.write_text(json.dumps(_brief("other"), ensure_ascii=False), encoding="utf-8")
    with pytest.raises(FactoryContractError) as caught:
        load_factual_brief("brief.json", repo_root=tmp_path, topic="介绍 Modbus RTU")
    assert caught.value.code == "director_factual_brief_invalid"
    assert "other" not in json.dumps(caught.value.to_dict(), ensure_ascii=False)


def test_factual_brief_unresolved_source_fails_closed(tmp_path: Path) -> None:
    topic = "Modbus"
    value = _brief(topic)
    value["facts"][0]["source_ids"] = ["missing_source"]
    path = tmp_path / "brief.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(FactoryContractError) as caught:
        load_factual_brief("brief.json", repo_root=tmp_path, topic=topic)
    assert caught.value.code == "director_factual_brief_invalid"


@pytest.mark.parametrize("value", ["../brief.json", "C:/secret/brief.json", "/tmp/brief.json"])
def test_factual_brief_unsafe_reference_fails_closed(value: str) -> None:
    with pytest.raises(FactoryContractError) as caught:
        load_factual_brief(value, repo_root=Path.cwd(), topic="Modbus")
    assert caught.value.code == "director_factual_brief_invalid"
