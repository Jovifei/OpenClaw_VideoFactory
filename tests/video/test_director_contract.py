from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from src.factory.director import Director


def test_director_create_storyboard_signature_is_topic_to_storyboard() -> None:
    signature = inspect.signature(Director.create_storyboard)
    assert list(signature.parameters) == ["self", "topic"]
    assert signature.return_annotation != inspect.Signature.empty


def test_director_stub_fails_closed_without_ai_implementation() -> None:
    with pytest.raises(NotImplementedError, match="^director_not_implemented$"):
        Director().create_storyboard("介绍 Modbus RTU")


def test_director_stub_does_not_create_files(tmp_path: Path) -> None:
    before = sorted(tmp_path.rglob("*"))
    with pytest.raises(NotImplementedError):
        Director().create_storyboard("topic")
    assert sorted(tmp_path.rglob("*")) == before
