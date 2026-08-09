from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from video_factory.pipeline.composition import load_composition, validate_composition
from video_factory.pipeline.errors import FactoryContractError


def test_default_knowledge_composition_is_schema_and_region_safe() -> None:
    composition = load_composition("knowledge_illustration")
    assert composition["composition_id"] == "knowledge_illustration"
    assert composition["layout"] == "knowledge_illustration"
    assert composition["regions"]["content_area"]["height"] > 0


def test_composition_content_subtitle_overlap_fails_closed() -> None:
    composition = load_composition()
    broken = copy.deepcopy(composition)
    broken["regions"]["subtitle_area"]["y"] = broken["regions"]["content_area"]["y"]
    with pytest.raises(FactoryContractError) as caught:
        validate_composition(broken)
    assert caught.value.code in {"composition_schema_invalid", "composition_region_invalid"}


def test_composition_path_escape_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FactoryContractError) as caught:
        load_composition("../composition.json", repo_root=tmp_path)
    assert caught.value.code == "composition_schema_invalid"
