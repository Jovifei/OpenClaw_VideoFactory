"""Contract tests for the sanitized Director run-report schema."""

from __future__ import annotations

import copy
import json

import pytest
from jsonschema import Draft202012Validator

from . import ROOT


SCHEMA_PATH = ROOT / "schemas" / "video" / "director_run_report.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_report() -> dict:
    digest = "a" * 64
    return {
        "schema_version": "1.0",
        "provider": "codex-cli",
        "provider_version": "0.1.0",
        "prompt_version": "pink_pig_director_v1",
        "topic_digest": digest,
        "attempts": 1,
        "draft_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
        "storyboard_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
        "semantic_validation": {"status": "pass", "error_count": 0, "validator": "director_semantics"},
        "storyboard_id": "sb_0123456789abcdef",
        "storyboard_sha256": "b" * 64,
        "compiled_duration_seconds": 40.0,
        "factual_review_required": True,
        "error": None,
    }


def _errors(schema: dict, document: dict) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (list(error.absolute_path), error.validator, error.message),
    )


def test_schema_is_well_formed_and_closed(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)
    assert schema["title"] == "DirectorRunReport"
    assert schema["additionalProperties"] is False
    assert schema["$id"].endswith("/director_run_report.schema.json")


def test_success_report_passes(schema: dict) -> None:
    assert _errors(schema, _valid_report()) == []


def test_failed_report_accepts_only_structured_sanitized_error(schema: dict) -> None:
    report = _valid_report()
    report["attempts"] = 3
    report["draft_validation"] = {"status": "fail", "error_count": 1, "validator": "required"}
    report["storyboard_validation"] = {"status": "fail", "error_count": 0}
    report["semantic_validation"] = {"status": "fail", "error_count": 0}
    report["error"] = {
        "code": "director_output_invalid",
        "message": "Director output failed the draft contract.",
        "context": {
            "provider": "codex-cli",
            "attempt": 3,
            "schema": "director_draft",
            "path": "scenes.0.pose",
            "validator": "enum",
        },
    }
    assert _errors(schema, report) == []


@pytest.mark.parametrize("field", [
    "schema_version",
    "provider",
    "provider_version",
    "prompt_version",
    "topic_digest",
    "attempts",
    "draft_validation",
    "storyboard_validation",
    "semantic_validation",
    "storyboard_id",
    "storyboard_sha256",
    "compiled_duration_seconds",
    "factual_review_required",
    "error",
])
def test_report_requires_all_contract_fields(schema: dict, field: str) -> None:
    report = _valid_report()
    report.pop(field)
    assert _errors(schema, report)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("topic_digest", "not-a-sha256"),
        ("storyboard_sha256", "z" * 64),
        ("attempts", 4),
        ("prompt_version", "v1"),
        ("factual_review_required", False),
        ("draft_validation", {"status": "unknown"}),
    ],
)
def test_report_rejects_unstable_or_invalid_values(schema: dict, field: str, value: object) -> None:
    report = _valid_report()
    report[field] = value
    assert _errors(schema, report)


def test_report_rejects_raw_prompt_paths_and_unknown_fields(schema: dict) -> None:
    report = _valid_report()
    report["prompt"] = "system prompt"
    report["absolute_path"] = "C:\\secret\\output.json"
    assert _errors(schema, report)

    report = _valid_report()
    report["error"] = {
        "code": "director_provider_failed",
        "message": "provider failed",
        "context": {"stdout": "raw model output"},
    }
    assert _errors(schema, report)


def test_error_context_is_deterministically_bounded(schema: dict) -> None:
    report = _valid_report()
    report["error"] = {
        "code": "director_provider_timeout",
        "message": "Director provider timed out.",
        "context": {"attempt": 1, "reason": "timeout"},
    }
    assert _errors(schema, report) == []

    invalid = copy.deepcopy(report)
    invalid["error"]["context"]["raw_response"] = "model output"
    assert _errors(schema, invalid)
