"""Unit tests for the MoneyPrinterTurbo configure helper (no network, no secrets)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.phase1_mpt_configure import _apply_settings, show_status


SAMPLE_TOML = """llm_provider = "moonshot"

[app]
hide_config = false

openai_api_key = ""
openai_base_url = ""
openai_model_name = ""

[whisper]
model_size = "large-v3"
"""


def test_apply_settings_replaces_and_inserts() -> None:
    updated = _apply_settings(
        SAMPLE_TOML,
        {
            "llm_provider": '"openai"',
            "openai_api_key": '"sk-test"',
            "openai_base_url": '"https://example.invalid/v1"',
            "openai_model_name": '"mimo-v2.5"',
            "model_size": '"small"',
        },
    )
    assert 'llm_provider = "openai"' in updated
    assert 'openai_api_key = "sk-test"' in updated
    assert 'openai_base_url = "https://example.invalid/v1"' in updated
    assert 'openai_model_name = "mimo-v2.5"' in updated
    assert 'model_size = "small"' in updated
    assert 'llm_provider = "moonshot"' not in updated


def test_apply_settings_is_idempotent() -> None:
    settings = {
        "llm_provider": '"openai"',
        "openai_api_key": '"sk-test"',
        "openai_base_url": '"https://example.invalid/v1"',
        "openai_model_name": '"mimo-v2.5"',
        "model_size": '"small"',
    }
    once = _apply_settings(SAMPLE_TOML, settings)
    twice = _apply_settings(once, settings)
    assert once == twice


def test_show_status_reports_missing_config(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    show_status(tmp_path)
    captured = capsys.readouterr()
    assert "does not exist" in captured.out
