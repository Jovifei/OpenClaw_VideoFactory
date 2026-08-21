from __future__ import annotations

import hashlib
from pathlib import Path

from src.factory.assets.pink_pig.loader import load_registry
from src.factory.director import AssetSelector, ScriptPlanner, StoryboardAssembler, load_director_context, stable_script_id


ROOT = Path(__file__).resolve().parents[2]


class FakeScriptProvider:
    provider_name = "fake"
    provider_version = "test"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, *, prompt: str, output_schema: Path, timeout_seconds: int) -> dict[str, object]:
        self.calls += 1
        digest = hashlib.sha256("介绍 Modbus RTU".encode("utf-8")).hexdigest()
        return {
            "schema_version": "1.0",
            "script_id": stable_script_id("介绍 Modbus RTU"),
            "topic_digest": digest,
            "title": "Modbus RTU是什么",
            "hook": "为什么一根串口线也能让设备可靠通信？",
            "narration": "Modbus RTU把工程设备组织成可验证的请求和响应。",
            "duration_target_seconds": 40,
            "style": {"language": "zh-CN", "tone": "technical_calm_dry_humor", "content_scope": "evergreen_embedded_mainline"},
            "beats": [
                {"purpose": "hook", "narration": "先看它解决什么问题。", "subtitle": "它解决什么问题？", "visual_intent": "展示主从关系", "pose": "normal", "required_tags": ["education", "explain"], "fact_refs": []},
                {"purpose": "explain", "narration": "主站发起请求，从站按地址回应。", "subtitle": "主站请求，从站回应", "visual_intent": "展示通信方向", "pose": "thinking", "required_tags": ["education", "explain"], "fact_refs": []},
                {"purpose": "frame", "narration": "帧里包含地址、功能码、数据和 CRC。", "subtitle": "地址、功能码、数据、CRC", "visual_intent": "展示协议帧", "pose": "measure", "required_tags": ["education", "protocol_frame"], "fact_refs": []},
                {"purpose": "repair", "narration": "排错时先看串口参数和 CRC。", "subtitle": "先查参数，再查 CRC", "visual_intent": "展示排错路径", "pose": "repair", "required_tags": ["education", "warning", "repair"], "fact_refs": []},
                {"purpose": "summary", "narration": "抓住请求、响应和校验，就能可靠对话。", "subtitle": "请求、响应、校验", "visual_intent": "总结可靠通信", "pose": "success", "required_tags": ["education", "summary"], "fact_refs": []},
            ],
        }


def test_script_planner_is_deterministic_and_scores_fake_script() -> None:
    provider = FakeScriptProvider()
    context = load_director_context(ROOT)
    planner = ScriptPlanner(provider, repo_root=ROOT, context=context)
    script = planner.create_script("介绍 Modbus RTU")
    assert script["script_id"] == "script_06b00f079b94d3e8"
    assert planner.last_result is not None
    assert planner.last_result.score["score"] >= 85
    assert provider.calls == 1


def test_storyboard_assembly_then_registry_asset_selection_is_distinct() -> None:
    context = load_director_context(ROOT)
    planner = ScriptPlanner(FakeScriptProvider(), repo_root=ROOT, context=context)
    script = planner.create_script("介绍 Modbus RTU")
    registry = load_registry(repo_root=ROOT)
    storyboard = StoryboardAssembler(repo_root=ROOT, registry=registry).from_script(script)
    result = AssetSelector(repo_root=ROOT, registry=registry).select_assets(storyboard, registry)
    selected = [scene["asset_id"] for scene in result.storyboard["scenes"]]
    assert len(selected) == 5
    assert len(set(selected)) >= 4
    assert all(asset_id in registry.assets for asset_id in selected)
    assert result.report["selections"][0]["relative_path"].startswith("assets/")
