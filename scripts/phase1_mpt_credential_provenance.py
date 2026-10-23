"""Secret-safe provenance inventory for the approved MPT credential sources.

This script never calls the provider and never writes a secret-bearing config.
It compares only SHA-256 fingerprints and records whether an approved source
is distinct from the credential that received the observed 401.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tomllib
from pathlib import Path
from typing import Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "external" / "MoneyPrinterTurbo" / "config.toml"
REPORT_PATH = REPO_ROOT / "reports" / "phase1" / "stage_20260929" / "mpt_credential_provenance.json"
APPROVED_ENV_VARS = ("MIMO_API_KEY", "MPT_LLM_API_KEY")


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source(*, locator: str, source_type: str, presence: str, digest: str | None, approved: bool, equals_rejected: bool | None, provenance: str) -> dict[str, object]:
    return {
        "locator": locator,
        "source_type": source_type,
        "presence": presence,
        "fingerprint_sha256": digest,
        "approved_source": approved,
        "equals_rejected_effective": equals_rejected,
        "provenance": provenance,
    }


def build_provenance(*, config_path: Path = CONFIG_PATH, env: Mapping[str, str] | None = None) -> dict[str, object]:
    environment = os.environ if env is None else env
    raw = config_path.read_bytes() if config_path.is_file() else b""
    config_sha = hashlib.sha256(raw).hexdigest() if raw else None
    app: dict[str, object] = {}
    parse_status = "MISSING"
    if raw:
        try:
            document = tomllib.loads(raw.decode("utf-8"))
            app = document.get("app") if isinstance(document.get("app"), dict) else {}
            parse_status = "OK"
        except Exception as exc:  # noqa: BLE001 - safe metadata only
            parse_status = f"ERROR:{type(exc).__name__}"
    provider = str(app.get("llm_provider", ""))
    credential_field = f"{provider}_api_key" if provider else ""
    config_value = str(app.get(credential_field, "") or "")
    rejected_fingerprint = fingerprint(config_value) if config_value else None
    sources = [
        _source(
            locator="owner_workspace/external/MoneyPrinterTurbo/config.toml",
            source_type="effective_ignored_mpt_config",
            presence="PRESENT" if config_value else "MISSING",
            digest=rejected_fingerprint,
            approved=True,
            equals_rejected=True if config_value else None,
            provenance="effective credential recorded by the approved MPT setup; the same value was rejected by the observed HTTP 401",
        )
    ]
    for name in APPROVED_ENV_VARS:
        value = str(environment.get(name, "") or "")
        digest = fingerprint(value) if value else None
        sources.append(
            _source(
                locator=f"process_environment/{name}",
                source_type="documented_approved_environment_input",
                presence="PRESENT" if value else "MISSING",
                digest=digest,
                approved=True,
                equals_rejected=(digest == rejected_fingerprint) if digest and rejected_fingerprint else None,
                provenance="project-documented existing environment input; value and process dump are never persisted",
            )
        )
    template = REPO_ROOT / ".env.example"
    sources.append(
        _source(
            locator="workspace/.env.example",
            source_type="template_only",
            presence="PRESENT" if template.is_file() else "MISSING",
            digest=None,
            approved=False,
            equals_rejected=None,
            provenance="template contains no applicable credential value and is not a restoration source",
        )
    )
    distinct = any(
        bool(item.get("approved_source"))
        and item.get("presence") == "PRESENT"
        and item.get("fingerprint_sha256")
        and item.get("fingerprint_sha256") != rejected_fingerprint
        for item in sources
    )
    status = "APPROVED_EXISTING_CREDENTIAL_SOURCE_FOUND" if distinct else "NO_APPROVED_EXISTING_CREDENTIAL_SOURCE_FOUND"
    report: dict[str, object] = {
        "schema_version": "phase1_mpt_credential_provenance_v1",
        "status": status,
        "authorization": "Remote GPT iteration 41 WP-M5A read-only credential provenance discovery",
        "scope": {
            "search_roots": ["owner_workspace/external/MoneyPrinterTurbo", "workspace_root_config_history", "process_environment"],
            "unrelated_user_directories_scanned": False,
            "provider_called": False,
            "config_changed": False,
        },
        "effective_config": {
            "locator": "owner_workspace/external/MoneyPrinterTurbo/config.toml",
            "config_sha256": config_sha,
            "parse_status": parse_status,
            "provider": provider or None,
            "credential_field": f"app.{credential_field}" if credential_field else None,
            "fingerprint_sha256": rejected_fingerprint,
            "observed_401": True,
        },
        "sources": sources,
        "approved_distinct_existing_source_found": distinct,
        "m5b": "NOT_RUN_SAME_REJECTED_FINGERPRINT_OR_NO_DISTINCT_SOURCE" if not distinct else "CONDITIONALLY_ALLOWED_SEPARATE_REVIEW",
        "next_state": "I2C_BLOCKED:MPT_APPROVED_CREDENTIAL_UNAVAILABLE" if not distinct else "M5B_REVIEW_REQUIRED",
        "candidate003": "TERMINAL_PRESERVE",
        "m6": "NOT_AUTHORIZED",
        "candidate004": "NOT_AUTHORIZED",
        "media": "NOT_AUTHORIZED",
        "formal_gate": "NOT_AUTHORIZED",
    }
    serialized = json.dumps(report, ensure_ascii=False)
    if config_value and config_value in serialized:
        raise RuntimeError("secret_leak_in_provenance_report")
    for name in APPROVED_ENV_VARS:
        value = str(environment.get(name, "") or "")
        if value and value in serialized:
            raise RuntimeError("environment_secret_leak_in_provenance_report")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory approved MPT credential provenance without exposing values.")
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args(argv)
    report = build_provenance()
    path = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": path.relative_to(REPO_ROOT).as_posix(), "m5b": report["m5b"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
