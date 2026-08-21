from __future__ import annotations

from pathlib import Path

from src.factory import phase1_cli
from src.factory.db import CandidateStore


def test_phase1_doctor_is_local_only(capsys) -> None:
    assert phase1_cli.main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert '"mode": "phase1_local_only"' in output
    assert '"provider_enabled": false' in output
    assert '"feishu_enabled": false' in output
    assert '"cron_enabled": false' in output


def test_candidate_store_accepts_phase1_metadata(tmp_path: Path) -> None:
    store = CandidateStore(tmp_path / "phase1.sqlite3")
    store.initialize()
    created = store.create_job(
        "local_topic",
        "phase1:test",
        "video_factory_local_brief",
        "test topic",
        requested_duration_seconds=30,
        metadata={"topic_digest": "a" * 64, "brief_path": "state/input.json"},
    )
    assert created["created"] is True
    assert created["metadata"]["topic_digest"] == "a" * 64
    existing = store.create_job(
        "local_topic",
        "phase1:test",
        "video_factory_local_brief",
        "test topic",
        requested_duration_seconds=30,
        metadata={"topic_digest": "b" * 64},
    )
    assert existing["created"] is False
    assert existing["metadata"]["topic_digest"] == "a" * 64
