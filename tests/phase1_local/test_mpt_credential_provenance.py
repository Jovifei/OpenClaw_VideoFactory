"""Secret-leak and fingerprint tests for M5A provenance evidence."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.phase1_mpt_credential_provenance import build_provenance, fingerprint


def test_fingerprint_is_stable_and_non_reversible_in_report(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    secret = "approved-secret-value"
    config.write_text(f'[app]\nllm_provider = "openai"\nopenai_api_key = "{secret}"\n', encoding="utf-8")
    report = build_provenance(config_path=config, env={"MIMO_API_KEY": secret, "MPT_LLM_API_KEY": ""})
    serialized = json.dumps(report, ensure_ascii=False)
    assert report["status"] == "NO_APPROVED_EXISTING_CREDENTIAL_SOURCE_FOUND"
    assert fingerprint(secret) in serialized
    assert secret not in serialized


def test_distinct_approved_environment_source_is_detected(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text('[app]\nllm_provider = "openai"\nopenai_api_key = "rejected-secret-value-1234567890"\n', encoding="utf-8")
    report = build_provenance(config_path=config, env={"MIMO_API_KEY": "approved-new-existing-secret-0987654321", "MPT_LLM_API_KEY": ""})
    assert report["status"] == "APPROVED_EXISTING_CREDENTIAL_SOURCE_FOUND"
    assert report["m5b"] == "CONDITIONALLY_ALLOWED_SEPARATE_REVIEW"
