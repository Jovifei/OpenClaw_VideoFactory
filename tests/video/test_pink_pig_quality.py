from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from video_factory.pipeline.composition import load_composition
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.pink_pig_quality import validate_pink_pig_quality


ROOT = Path(__file__).resolve().parents[2]


def _registry() -> dict:
    value = json.loads((ROOT / "src/factory/assets/pink_pig/registry.json").read_text(encoding="utf-8"))
    value["style_profile"] = json.loads((ROOT / "src/factory/assets/pink_pig/style_profile.json").read_text(encoding="utf-8"))
    return value


def _storyboard() -> dict:
    registry = _registry()
    return {
        "ip": {"character_id": "pink_pig", "registry_version": registry["registry_version"]},
        "scenes": [{"director_notes": "measure the protocol frame"}],
    }


def _timeline(asset_id: str = "pink_pig.normal.v1") -> dict:
    return {"scenes": [{"asset_id": asset_id, "image_path": "assets/pink_pig/pig01.png"}]}


def test_registry_backed_quality_passes_for_local_renderable_asset() -> None:
    result = validate_pink_pig_quality(
        storyboard=_storyboard(),
        timeline=_timeline(),
        registry=_registry(),
        composition=load_composition(),
        mascot_contract={"mode": "required", "skill_loaded": True},
        repo_root=ROOT,
    )
    assert result["status"] == "pass"
    assert result["signature_asset_id"] == "pink_pig.signature.v1"
    assert result["asset_ids"] == ["pink_pig.normal.v1"]


def test_unregistered_asset_fails_closed() -> None:
    with pytest.raises(FactoryContractError) as caught:
        validate_pink_pig_quality(
            storyboard=_storyboard(),
            timeline=_timeline("pink_pig.unknown.v1"),
            registry=_registry(),
            composition=load_composition(),
            repo_root=ROOT,
        )
    assert caught.value.code == "pink_pig_asset_unregistered"


def test_missing_style_profile_fails_closed() -> None:
    registry = _registry()
    registry.pop("style_profile")
    with pytest.raises(FactoryContractError) as caught:
        validate_pink_pig_quality(
            storyboard=_storyboard(), timeline=_timeline(), registry=registry, repo_root=ROOT
        )
    assert caught.value.code == "pink_pig_style_missing"


def test_character_mismatch_fails_closed() -> None:
    storyboard = _storyboard()
    storyboard["ip"]["character_id"] = "other_mascot"
    with pytest.raises(FactoryContractError) as caught:
        validate_pink_pig_quality(
            storyboard=storyboard, timeline=_timeline(), registry=_registry(), repo_root=ROOT
        )
    assert caught.value.code == "pink_pig_character_mismatch"
