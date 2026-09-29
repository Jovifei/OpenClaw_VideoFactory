"""Pure redaction/classification tests for the M4 diagnostic boundary."""

from __future__ import annotations

from scripts.phase1_mpt_provider_diagnostic import _classify_direct_result, sanitize_text


def test_sanitize_redacts_secret_path_bearer_and_query() -> None:
    raw = (
        r'path=C:\Users\Jovi\secret\config.toml api_key="config-secret-value" '
        "Authorization: Bearer bearer-secret https://example.test/v1?token=query-secret"
    )
    safe = sanitize_text(raw, ["config-secret-value", "bearer-secret"])
    assert "config-secret-value" not in safe
    assert "bearer-secret" not in safe
    assert "query-secret" not in safe
    assert "C:\\Users\\Jovi" not in safe
    assert "<REDACTED>" in safe
    assert "<PATH>" in safe


def test_classification_requires_script_json_for_ready() -> None:
    assert _classify_direct_result(0, False, "provider openai", False) == "MPT_PROVIDER_BLOCKED:UNCLASSIFIED"
    assert _classify_direct_result(0, False, "provider openai", True) == "MPT_PROVIDER_READY"


def test_classification_preserves_specific_supported_blockers() -> None:
    assert _classify_direct_result(1, False, "openai: api_key is not set", False) == "MPT_PROVIDER_BLOCKED:MISSING_CREDENTIAL"
    assert _classify_direct_result(1, False, "HTTP 401 Unauthorized", False) == "MPT_PROVIDER_BLOCKED:AUTH"
    assert _classify_direct_result(1, False, "ConnectTimeout: timed out", False) == "MPT_PROVIDER_BLOCKED:NETWORK"
    assert _classify_direct_result(1, False, "model not found", False) == "MPT_PROVIDER_BLOCKED:MODEL_OR_API"
