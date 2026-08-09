from __future__ import annotations

import copy
import json

import pytest

from src.factory.assets.pink_pig.loader import PinkPigRegistry, load_registry
from video_factory.pipeline.errors import FactoryContractError

from . import ROOT


PROFILE_PATH = ROOT / "src" / "factory" / "assets" / "pink_pig" / "style_profile.json"
REGISTRY_PATH = ROOT / "src" / "factory" / "assets" / "pink_pig" / "registry.json"


def _profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_style_profile_has_all_required_sections() -> None:
    profile = _profile()
    assert {
        "schema_version",
        "brand_identity",
        "character_rules",
        "color_rules",
        "pose_rules",
        "forbidden_rules",
        "quality_checks",
    }.issubset(profile)


def test_style_profile_identity_and_required_character_features() -> None:
    profile = _profile()
    assert profile["brand_identity"]["character_id"] == "pink_pig"
    assert profile["brand_identity"]["display_name"] == "小粉飞猪"
    assert set(profile["character_rules"]["required_features"]) >= {
        "small_wings",
        "round_snout_two_dots",
        "dot_eyes",
    }
    assert profile["character_rules"]["core_action_required"] is True


def test_style_profile_forbidden_rules_include_ip_safety_items() -> None:
    forbidden = set(_profile()["forbidden_rules"])
    assert {
        "realistic_pig",
        "random_character_replacement",
        "unrelated_mascot",
        "generic_cute_mascot",
        "content_obstruction",
    }.issubset(forbidden)


def test_style_profile_quality_checks_have_machine_readable_shape() -> None:
    for check in _profile()["quality_checks"]:
        assert {"check_id", "required", "mode", "description"}.issubset(check)


def test_registry_uses_external_style_profile_as_single_source() -> None:
    registry = _registry()
    assert registry["style_profile_ref"] == "src/factory/assets/pink_pig/style_profile.json"
    assert "style_profile" not in registry
    loaded = load_registry()
    assert isinstance(loaded, PinkPigRegistry)
    assert loaded.style_profile.brand_identity["character_id"] == "pink_pig"


def test_registry_style_reference_rejects_traversal(tmp_path) -> None:
    value = _registry()
    value["style_profile_ref"] = "../style_profile.json"
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(FactoryContractError) as excinfo:
        load_registry(registry_path, repo_root=tmp_path)
    assert excinfo.value.code == "asset_registry_invalid"


def test_invalid_external_style_profile_fails_closed(tmp_path) -> None:
    value = _registry()
    value["style_profile_ref"] = "style_profile.json"
    (tmp_path / "style_profile.json").write_text(json.dumps({"schema_version": "1.0"}), encoding="utf-8")
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(FactoryContractError) as excinfo:
        load_registry(registry_path, repo_root=tmp_path)
    assert excinfo.value.code == "asset_registry_invalid"
