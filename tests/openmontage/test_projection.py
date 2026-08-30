import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from src.factory.db import CandidateStore
from src.factory.openmontage_projection import build_checkpoint, project_job_read_only


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("state", "stage", "status"),
    [
        ("NEW", "research", "in_progress"),
        ("RESEARCHING", "research", "in_progress"),
        ("SCRIPTING", "script", "in_progress"),
        ("VOICE", "edit", "in_progress"),
        ("CAPTIONS", "edit", "in_progress"),
        ("ASSETS", "assets", "in_progress"),
        ("RENDERING", "compose", "in_progress"),
        ("QUALITY_CHECK", "review", "in_progress"),
        ("PENDING_REVIEW", "review", "awaiting_human"),
        ("FAILED", "review", "failed"),
        ("CANCELLED", "review", "failed"),
    ],
)
def test_every_sqlite_state_maps_to_declared_schema_valid_checkpoint(state: str, stage: str, status: str) -> None:
    checkpoint = build_checkpoint(
        {"job": {"job_id": "job-mapped", "state": state, "updated_at": "2026-08-30T00:00:00Z"},
         "artifacts": [], "events": []}
    )
    assert (checkpoint["stage"], checkpoint["status"]) == (stage, status)
    manifest = yaml.safe_load((ROOT / "third_party/openmontage/pipelines/phase1-local-topic.yaml").read_text(encoding="utf-8"))
    assert checkpoint["stage"] in {item["name"] for item in manifest["stages"]}
    schema = json.loads((ROOT / "third_party/openmontage/schemas/checkpoints/checkpoint.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(checkpoint, schema)


def test_unknown_sqlite_state_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown_sqlite_state"):
        build_checkpoint({"job": {"job_id": "job-x", "state": "ALIEN", "updated_at": "2026-08-30T00:00:00Z"}, "artifacts": [], "events": []})


def test_projection_is_atomic_and_does_not_transition_sqlite(tmp_path: Path) -> None:
    store = CandidateStore(tmp_path / "factory.sqlite3")
    store.initialize()
    created = store.create_job("fixture", "projection-key", "template", "topic")
    job_id = created["job_id"]
    artifact = tmp_path / "artifact.json"
    artifact.write_text('{"ok":true}', encoding="utf-8")
    import hashlib
    store.record_artifact(job_id, "research", "artifact.json", hashlib.sha256(artifact.read_bytes()).hexdigest())
    state_before = store.status(job_id)
    events_before = store.events(job_id)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("projection must use one snapshot read")

    store.status = forbidden  # type: ignore[method-assign]
    store.artifacts = forbidden  # type: ignore[method-assign]
    store.events = forbidden  # type: ignore[method-assign]

    project_dir = project_job_read_only(store, job_id, tmp_path / "projections")

    pointer = json.loads((project_dir / "current.json").read_text(encoding="utf-8"))
    generation = project_dir / pointer["generation"]
    assert json.loads((generation / "project.json").read_text(encoding="utf-8"))["state_authority"] == "sqlite"
    assert list(generation.glob("checkpoint_*.json"))
    assert (generation / "history" / "events.jsonl").is_file()
    snapshot = store.projection_snapshot(job_id)
    assert snapshot["job"] == state_before
    assert snapshot["events"] == events_before
    assert not list((tmp_path / "projections").rglob("*.tmp"))
