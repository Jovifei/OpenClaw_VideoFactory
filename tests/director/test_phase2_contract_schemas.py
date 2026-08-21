from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from video_factory.pipeline.validation import validate


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "video"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def _beat(index: int, purpose: str | None = None) -> dict:
    return {
        "purpose": purpose or f"explain_{index}",
        "narration": f"第{index}幕说明协议的一个关键点。",
        "subtitle": f"关键点 {index}",
        "visual_intent": "展示经过验证的技术图",
        "pose": "thinking",
        "required_tags": ["education", "explain"],
        "fact_refs": [f"fact_{index}"],
    }


def _script() -> dict:
    beats = [_beat(1, "hook"), _beat(2), _beat(3), _beat(4), _beat(5, "summary")]
    return {
        "schema_version": "1.0",
        "script_id": "script_0123456789abcdef",
        "topic_digest": "a" * 64,
        "title": "Modbus RTU是什么",
        "hook": "为什么一根串口线也能让设备可靠通信？",
        "narration": "这里是经过事实资料约束的完整旁白。",
        "duration_target_seconds": 40,
        "style": {
            "language": "zh-CN",
            "tone": "technical_calm_dry_humor",
            "content_scope": "evergreen_embedded_mainline",
        },
        "beats": beats,
    }


def _brief() -> dict:
    return {
        "schema_version": "1.0",
        "topic_digest": "a" * 64,
        "facts": [
            {"fact_id": "fact_1", "claim": "设备按协议帧交换数据。", "source_ids": ["source_1"]}
        ],
        "sources": [
            {"source_id": "source_1", "title": "Serial Line Specification", "publisher": "Modbus Organization", "url": "https://example.com/spec", "kind": "standard"},
            {"source_id": "source_2", "title": "Application Protocol", "publisher": "Modbus Organization", "url": "https://example.com/protocol", "kind": "official_document"},
        ],
        "review_status": "verified",
    }


def _selection_report() -> dict:
    return {
        "schema_version": "1.0",
        "job_id": "director_0123456789abcdef",
        "storyboard_id": "sb_0123456789abcdef",
        "selections": [
            {
                "scene_id": "s01",
                "asset_id": "pink_pig.knowledge_frame_layout.v1",
                "tags": ["education", "explain"],
                "relative_path": "assets/modbus_rtu_illustrations/02-frame-layout.png",
                "sha256": "b" * 64,
                "source_type": "repository_owned",
                "rights_basis": "repository-owned asset",
                "classification": "factual",
                "fallback_used": False,
                "crop": "contain",
                "transformation": "fit content region",
            }
        ],
    }


def _quality_report() -> dict:
    return {
        "schema_version": "1.0",
        "job_id": "director_0123456789abcdef",
        "status": "completed",
        "score": 92,
        "checks": [{"check_id": "media_decode", "status": "pass", "detail": "ffmpeg decode passed"}],
        "factual_review_required": False,
        "factual_review_status": "verified",
        "render_report_ref": "render_report.json",
        "error": None,
    }


@pytest.mark.parametrize("name", ["director_script", "director_factual_brief", "asset_selection_report", "director_quality_report"])
def test_phase2_schema_files_are_well_formed(name: str) -> None:
    Draft202012Validator.check_schema(_schema(name))


def test_director_script_accepts_semantic_contract() -> None:
    Draft202012Validator(_schema("director_script")).validate(_script())


def test_director_script_rejects_asset_id_and_extra_fields() -> None:
    broken = _script()
    broken["asset_id"] = "pink_pig.normal.v1"
    with pytest.raises(Exception):
        Draft202012Validator(_schema("director_script")).validate(broken)


def test_director_script_rejects_wrong_scene_count() -> None:
    broken = _script()
    broken["beats"] = broken["beats"][:4]
    with pytest.raises(Exception):
        Draft202012Validator(_schema("director_script")).validate(broken)


def test_factual_brief_requires_two_sources() -> None:
    brief = _brief()
    Draft202012Validator(_schema("director_factual_brief")).validate(brief)
    brief["sources"] = brief["sources"][:1]
    with pytest.raises(Exception):
        Draft202012Validator(_schema("director_factual_brief")).validate(brief)


def test_asset_selection_report_and_quality_report_validate() -> None:
    Draft202012Validator(_schema("asset_selection_report")).validate(_selection_report())
    Draft202012Validator(_schema("director_quality_report")).validate(_quality_report())


def _v2_state(state: str) -> dict:
    value = {
        "schema_version": "2.0",
        "job_id": "director_0123456789abcdef",
        "topic": "Modbus RTU",
        "topic_digest": "a" * 64,
        "state": state,
        "state_revision": 1,
    }
    if state in {"script_ready", "storyboard_ready", "rendering", "quality_check", "completed"}:
        value["script_ref"] = "script.json"
    if state in {"storyboard_ready", "rendering", "quality_check", "completed"}:
        value["storyboard_ref"] = "storyboard.json"
    if state in {"rendering", "quality_check", "completed"}:
        value["timeline_ref"] = "timeline.json"
    if state in {"quality_check", "completed"}:
        value["render_report_ref"] = "render_report.json"
        value["quality_report_ref"] = "director_quality_report.json"
    if state == "completed":
        value["output_ref"] = "pink_pig_modbus_ai_demo.mp4"
        value["factual_review_required"] = False
        value["factual_review_status"] = "verified"
    if state == "failed":
        value["error"] = {"code": "director_quality_failed", "message": "quality gate failed", "context": {}}
    return value


@pytest.mark.parametrize("state", ["created", "planning", "script_ready", "storyboard_ready", "rendering", "quality_check", "completed", "failed"])
def test_v2_director_job_states_validate(state: str) -> None:
    Draft202012Validator(_schema("video_job_state")).validate(_v2_state(state))


def test_v2_state_rejects_unknown_state_and_missing_quality_report() -> None:
    broken = _v2_state("quality_check")
    broken.pop("quality_report_ref")
    with pytest.raises(Exception):
        Draft202012Validator(_schema("video_job_state")).validate(broken)
    broken = _v2_state("queued")
    with pytest.raises(Exception):
        Draft202012Validator(_schema("video_job_state")).validate(broken)


def test_validation_catalog_has_phase2_contracts_and_stable_codes() -> None:
    for name in ["director_script", "director_factual_brief", "asset_selection_report", "director_quality_report"]:
        validate(_script() if name == "director_script" else _brief() if name == "director_factual_brief" else _selection_report() if name == "asset_selection_report" else _quality_report(), name)

