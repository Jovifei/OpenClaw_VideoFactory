"""Phase 1.5 composition and knowledge-asset contract tests."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess

import pytest
from jsonschema import Draft202012Validator

from . import ROOT


SCHEMA_PATH = ROOT / "schemas" / "video" / "composition.schema.json"
CONFIG_PATH = ROOT / "video_factory" / "configs" / "compositions" / "knowledge_illustration.json"
REGISTRY_PATH = ROOT / "src" / "factory" / "assets" / "pink_pig" / "registry.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def composition() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _errors(schema: dict, document: dict) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (list(error.absolute_path), error.validator, error.message),
    )


def test_composition_schema_is_well_formed_and_closed(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)
    assert schema["title"] == "KnowledgeIllustrationComposition"
    assert schema["additionalProperties"] is False


def test_shipped_knowledge_composition_validates(schema: dict, composition: dict) -> None:
    assert _errors(schema, composition) == []
    assert composition["layout"] == "knowledge_illustration"
    assert composition["canvas"] == {
        "width": 1080,
        "height": 1920,
        "background_color": "0xF7E4EA",
    }


def test_regions_match_fixed_vertical_safe_bands(composition: dict) -> None:
    regions = composition["regions"]
    assert set(regions) == {"brand_area", "content_area", "subtitle_area", "signature_area"}
    assert regions["content_area"]["y"] == 240
    assert regions["content_area"]["y"] + regions["content_area"]["height"] == 1040
    assert regions["subtitle_area"]["y"] == 1120
    assert regions["subtitle_area"]["y"] + regions["subtitle_area"]["height"] == 1580
    assert regions["signature_area"]["y"] == 1760
    assert regions["signature_area"]["y"] + regions["signature_area"]["height"] == 1860


def test_composition_rejects_unknown_fields_and_missing_brand_area(schema: dict, composition: dict) -> None:
    unknown = copy.deepcopy(composition)
    unknown["regions"]["unsafe_overlay"] = {"x": 0, "y": 0, "width": 1, "height": 1}
    assert _errors(schema, unknown)

    missing = copy.deepcopy(composition)
    missing["regions"].pop("brand_area")
    assert _errors(schema, missing)


def test_registry_contains_five_verified_modbus_illustrations_and_signature() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assets = {item["asset_id"]: item for item in registry["assets"]}
    expected = {
        "pink_pig.knowledge_master_slave.v1": "01-master-slave.png",
        "pink_pig.knowledge_frame_layout.v1": "02-frame-layout.png",
        "pink_pig.knowledge_serial_parameters.v1": "03-serial-parameters.png",
        "pink_pig.knowledge_troubleshooting.v1": "04-troubleshooting.png",
        "pink_pig.knowledge_summary.v1": "05-summary.png",
    }
    for asset_id, filename in expected.items():
        asset = assets[asset_id]
        assert asset["asset_role"] == "knowledge_illustration"
        assert asset["path"] == f"assets/modbus_rtu_illustrations/{filename}"
        assert asset["render_ready"] is True
        assert asset["width"] == 1672 and asset["height"] == 941
        assert hashlib.sha256((ROOT / asset["path"]).read_bytes()).hexdigest() == asset["sha256"]

    signature = assets["pink_pig.signature.v1"]
    assert signature["asset_role"] == "signature"
    assert signature["render_ready"] is True
    assert signature["path"] == "assets/pink_pig/signature.png"
    assert signature["width"] == 400 and signature["height"] == 400
    assert signature["sha256"] == hashlib.sha256((ROOT / signature["path"]).read_bytes()).hexdigest()
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=pix_fmt",
            "-of",
            "default=nw=1",
            str(ROOT / signature["path"]),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "pix_fmt=rgba" in probe.stdout
