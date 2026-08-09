from __future__ import annotations

import copy
from pathlib import Path

import pytest

from src.factory.director import AIDirector, stable_storyboard_id
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate


def _draft(*, short: bool = False) -> dict:
    narration = "串口收到请求后先核对地址和功能码，再按帧边界拆解字段并验证响应，最后把异常定位到可以复现的工程步骤。"
    if short:
        narration = "太短。"
    scenes = []
    purposes = ["hook", "problem", "explain", "measure", "repair", "summary"]
    poses = ["question", "thinking", "normal", "measure", "repair", "success"]
    actions = ["提出问题", "观察报文", "解释字段", "测量时序", "修复配置", "盖章总结"]
    for index, (purpose, pose, action) in enumerate(zip(purposes, poses, actions)):
        scenes.append(
            {
                "purpose": purpose,
                "core_action": action,
                "narration": narration,
                "caption": f"第{index + 1}步",
                "mood": "focused",
                "pose": pose,
                "transition_out": "fade",
            }
        )
    return {
        "title": "Modbus RTU 的一帧数据",
        "content_scope": "evergreen_embedded_mainline",
        "scenes": scenes,
    }


class FakeProvider:
    provider_name = "fake"

    def __init__(self, values: list[dict]) -> None:
        self.values = values
        self.calls = 0
        self.prompts: list[str] = []

    def generate(self, *, prompt: str, output_schema: Path, timeout_seconds: int = 180) -> dict:
        self.calls += 1
        self.prompts.append(prompt)
        value = self.values[min(self.calls - 1, len(self.values) - 1)]
        return copy.deepcopy(value)


def test_ai_director_deterministically_assembles_existing_storyboard() -> None:
    provider = FakeProvider([_draft()])
    director = AIDirector(provider=provider, repo_root=Path.cwd())
    storyboard = director.create_storyboard("介绍 Modbus RTU")
    validate(storyboard, "storyboard")
    assert storyboard["storyboard_id"] == stable_storyboard_id("介绍 Modbus RTU")
    assert all(scene["asset_id"] is None for scene in storyboard["scenes"])
    assert [scene["scene_id"] for scene in storyboard["scenes"]] == [
        "s01", "s02", "s03", "s04", "s05", "s06"
    ]
    assert storyboard["scenes"][-1]["transition_out"] is None
    assert director.last_report["factual_review_required"] is True
    assert director.last_report["compiled_duration_seconds"] >= 25


def test_ai_director_retries_invalid_draft_then_succeeds() -> None:
    invalid = _draft()
    invalid["scenes"][0]["pose"] = "unknown"
    provider = FakeProvider([invalid, _draft()])
    storyboard = AIDirector(provider=provider, repo_root=Path.cwd()).create_storyboard("Modbus")
    assert storyboard["storyboard_id"].startswith("sb_")
    assert provider.calls == 2


def test_ai_director_fails_closed_after_duration_validation() -> None:
    provider = FakeProvider([_draft(short=True)])
    director = AIDirector(provider=provider, repo_root=Path.cwd(), max_attempts=3)
    with pytest.raises(FactoryContractError) as caught:
        director.create_storyboard("Modbus")
    assert caught.value.code == "director_storyboard_invalid"
    assert provider.calls == 3


def test_provider_unavailable_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    class Unavailable:
        provider_name = "fake"

        def __init__(self) -> None:
            self.calls = 0

        def generate(self, **kwargs):
            self.calls += 1
            raise FactoryContractError(
                "director_provider_unavailable",
                "unavailable",
                {"provider": "fake", "reason": "missing"},
            )

    provider = Unavailable()
    with pytest.raises(FactoryContractError) as caught:
        AIDirector(provider=provider, repo_root=Path.cwd()).create_storyboard("Modbus")
    assert caught.value.code == "director_provider_unavailable"
    assert provider.calls == 1
