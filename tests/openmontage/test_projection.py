import json
from pathlib import Path

from src.factory.db import CandidateStore
from src.factory.openmontage_projection import project_job_read_only


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

    project_dir = project_job_read_only(store, job_id, tmp_path / "projections")

    assert store.status(job_id) == state_before
    assert store.events(job_id) == events_before
    assert json.loads((project_dir / "project.json").read_text(encoding="utf-8"))["state_authority"] == "factory_sqlite"
    assert list(project_dir.glob("checkpoint_*.json"))
    assert (project_dir / "history" / "events.jsonl").is_file()
    assert not list((tmp_path / "projections").rglob("*.tmp"))
