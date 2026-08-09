from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.factory.director import CodexCliDirectorProvider
from video_factory.pipeline.errors import FactoryContractError


def _schema_path() -> Path:
    return Path.cwd() / "schemas" / "video" / "director_draft.schema.json"


def _draft() -> dict:
    return {
        "title": "测试主题",
        "content_scope": "evergreen_embedded_mainline",
        "scenes": [],
    }


def test_provider_uses_read_only_ephemeral_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr("src.factory.director.provider.shutil.which", lambda _: "codex.cmd")

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        if "--version" in command:
            return SimpleNamespace(returncode=0, stdout="codex-cli 0.146.0\n", stderr="")
        Path(kwargs["cwd"], "director_draft.json").write_text(
            json.dumps(_draft(), ensure_ascii=False), encoding="utf-8"
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("src.factory.director.provider.subprocess.run", fake_run)
    result = CodexCliDirectorProvider(working_dir=tmp_path).generate(
        prompt="prompt", output_schema=_schema_path(), timeout_seconds=5
    )
    command = captured["command"]
    assert result["title"] == "测试主题"
    assert "--ephemeral" in command
    assert "--sandbox" in command and "read-only" in command
    assert "--ignore-user-config" in command
    assert "--output-schema" in command
    assert "--model" not in command
    assert captured["shell"] is False
    assert captured["timeout"] == 5
    assert captured["input"] == "prompt"


def test_provider_rejects_malformed_output_without_raw_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.factory.director.provider.shutil.which", lambda _: "codex.cmd")

    def fake_run(command, **kwargs):
        if "--version" in command:
            return SimpleNamespace(returncode=0, stdout="codex-cli 0.146.0\n", stderr="")
        Path(kwargs["cwd"], "director_draft.json").write_text("not-json", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="model secret should not leak")

    monkeypatch.setattr("src.factory.director.provider.subprocess.run", fake_run)
    with pytest.raises(FactoryContractError) as caught:
        CodexCliDirectorProvider(working_dir=tmp_path).generate(
            prompt="prompt", output_schema=_schema_path()
        )
    assert caught.value.code == "director_output_invalid"
    assert "secret" not in json.dumps(caught.value.to_dict(), ensure_ascii=False)


def test_provider_nonzero_exit_is_structured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.factory.director.provider.shutil.which", lambda _: "codex.cmd")
    monkeypatch.setattr(
        "src.factory.director.provider.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=17, stdout="", stderr="private"),
    )
    with pytest.raises(FactoryContractError) as caught:
        CodexCliDirectorProvider(working_dir=tmp_path).generate(
            prompt="prompt", output_schema=_schema_path()
        )
    assert caught.value.code == "director_provider_failed"
    assert caught.value.context == {"provider": "codex-cli", "reason": "nonzero_exit", "exit_code": 17}
