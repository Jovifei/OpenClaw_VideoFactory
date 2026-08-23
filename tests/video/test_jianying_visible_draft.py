from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load_module():
    path = ROOT / "scripts/phase1_jianying_visible_draft.py"
    assert path.is_file(), "visible-draft junction helper must exist"
    spec = importlib.util.spec_from_file_location("phase1_jianying_visible_draft", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_visible_alias_rejects_media_content_on_c_drive(tmp_path: Path) -> None:
    module = _load_module()
    source = tmp_path / "E-drive-source"
    source.mkdir()
    with pytest.raises(ValueError, match="source_draft_must_be_e_drive"):
        module.validate_visible_draft_paths(Path("C:/source"), tmp_path / "app-root", "candidate")


def test_visible_alias_requires_target_inside_app_projects_root(tmp_path: Path) -> None:
    module = _load_module()
    source = Path("E:/OpenClaw_VideoFactory_Runtime/jianying_drafts/source")
    with pytest.raises(ValueError, match="visible_target_outside_app_root"):
        module.validate_visible_draft_paths(source, tmp_path / "app-root", "../outside")


def test_v59_draft_info_layout_is_a_valid_source_draft(tmp_path: Path) -> None:
    module = _load_module()
    (tmp_path / "draft_info.json").write_text("{}", encoding="utf-8")
    assert module.is_valid_jianying_draft_layout(tmp_path) is True
