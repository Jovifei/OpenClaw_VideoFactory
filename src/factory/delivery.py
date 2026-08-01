"""A non-network delivery record for P1 offline review packages."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .db import CandidateStore
from .json_safety import load_json_object_text


DELIVERY_FILES = (
    "final_master.mp4",
    "feishu_preview.mp4",
    "cover.png",
    "captions.srt",
    "quality_report.json",
)
DELIVERY_ARTIFACT_KEYS = frozenset({"name", "relative_path", "sha256", "size_bytes"})
DELIVERY_MANIFEST_KEYS = frozenset({
    "schema_version", "mode", "network_called", "lark_cli_called", "job_id",
    "candidate_state", "artifacts", "preview", "quality_report",
})
DELIVERY_MANIFEST_WITH_KEY = DELIVERY_MANIFEST_KEYS | {"delivery_key"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
JOB_ID_RE = re.compile(r"^job-[a-f0-9]{24}$")


def load_json_object(path: Path) -> dict[str, Any]:
    return load_json_object_text(path.read_text(encoding="utf-8"))


def _valid_artifact(value: object, expected_name: str | None = None) -> bool:
    if not isinstance(value, dict) or set(value) != DELIVERY_ARTIFACT_KEYS:
        return False
    name = value.get("name")
    return (
        isinstance(name, str)
        and name in DELIVERY_FILES
        and (expected_name is None or name == expected_name)
        and value.get("relative_path") == name
        and isinstance(value.get("sha256"), str)
        and bool(SHA256_RE.fullmatch(value["sha256"]))
        and isinstance(value.get("size_bytes"), int)
        and not isinstance(value.get("size_bytes"), bool)
        and value["size_bytes"] >= 0
    )


def valid_delivery_manifest(manifest: object, job_id: str, *, include_delivery_key: bool) -> bool:
    expected_keys = DELIVERY_MANIFEST_WITH_KEY if include_delivery_key else DELIVERY_MANIFEST_KEYS
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        return False
    if (
        manifest.get("schema_version") != "2.0"
        or manifest.get("mode") != "dry-run"
        or manifest.get("network_called") is not False
        or manifest.get("lark_cli_called") is not False
        or manifest.get("job_id") != job_id
        or not JOB_ID_RE.fullmatch(job_id)
        or manifest.get("candidate_state") != "QUALITY_CHECK"
    ):
        return False
    if include_delivery_key and manifest.get("delivery_key") != hashlib.sha256(
        f"{job_id}|offline-dry-run|v2".encode("utf-8")
    ).hexdigest():
        return False
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(DELIVERY_FILES):
        return False
    by_name = {item.get("name"): item for item in artifacts if _valid_artifact(item)}
    return (
        set(by_name) == set(DELIVERY_FILES)
        and len(by_name) == len(artifacts)
        and manifest.get("preview") == by_name["feishu_preview.mp4"]
        and manifest.get("quality_report") == by_name["quality_report.json"]
    )


def record_dry_run_delivery(store: CandidateStore, job_id: str, package: Path) -> dict[str, Any]:
    job_state = store.status(job_id)["state"]
    if job_state != "QUALITY_CHECK":
        raise RuntimeError("delivery_requires_quality_check")
    missing = [name for name in DELIVERY_FILES if not (package / name).is_file()]
    if missing:
        raise RuntimeError(f"delivery_artifact_missing:{','.join(missing)}")
    delivery_key = hashlib.sha256(f"{job_id}|offline-dry-run|v2".encode("utf-8")).hexdigest()
    artifacts = [
        {
            "name": name,
            "relative_path": name,
            "sha256": hashlib.sha256((package / name).read_bytes()).hexdigest(),
            "size_bytes": (package / name).stat().st_size,
        }
        for name in DELIVERY_FILES
    ]
    manifest = {
        "schema_version": "2.0",
        "mode": "dry-run",
        "network_called": False,
        "lark_cli_called": False,
        "job_id": job_id,
        "candidate_state": job_state,
        "artifacts": artifacts,
        "preview": next(item for item in artifacts if item["name"] == "feishu_preview.mp4"),
        "quality_report": next(item for item in artifacts if item["name"] == "quality_report.json"),
    }
    result = store.create_delivery(delivery_key, job_id, manifest)
    persisted_manifest = result["manifest"]
    if (
        result.get("job_id") != job_id
        or result.get("mode") != "dry-run"
        or result.get("status") != "recorded"
        or not valid_delivery_manifest(persisted_manifest, job_id, include_delivery_key=False)
    ):
        raise RuntimeError("delivery_record_invalid")
    (package / "delivery_manifest.json").write_text(
        json.dumps(
            {**persisted_manifest, "delivery_key": delivery_key},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return result
