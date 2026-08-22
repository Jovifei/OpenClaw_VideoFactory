from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from src.factory.db import CandidateStore
from src.factory.phase1_acceptance import evaluate_job_prereview
from src.factory.state import STAGES


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = (
    "phase1_human_review.schema.json",
    "phase1_job_prereview.schema.json",
    "phase1_quality_report.schema.json",
    "phase1_review_package.schema.json",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _copy_schemas(root: Path) -> None:
    target = root / "schemas" / "video"
    target.mkdir(parents=True)
    for name in SCHEMAS:
        shutil.copyfile(REPO_ROOT / "schemas" / "video" / name, target / name)


def _artifact(path: Path, root: Path) -> dict[str, object]:
    return {
        "name": path.name,
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha(path),
        "bytes": path.stat().st_size,
    }


def _fixture(
    tmp_path: Path,
    *,
    input_mode: str = "topic",
    decision: str = "approved",
) -> tuple[CandidateStore, str, Path, Path]:
    _copy_schemas(tmp_path)
    store = CandidateStore(tmp_path / "state" / "phase1.sqlite3")
    store.initialize()
    created = store.create_job(
        "fixture",
        f"acceptance:{input_mode}",
        "template",
        "Modbus RTU",
    )
    control_job_id = str(created["job_id"])
    for target in STAGES[1:]:
        store.advance(control_job_id, target)

    work = tmp_path / "dist" / "phase1_demo"
    work.mkdir(parents=True)
    final_master = work / "final_master.mp4"
    final_master.write_bytes(b"deterministic-video")
    cover = work / "cover.png"
    cover.write_bytes(b"cover")
    subtitle = work / "subtitle.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8"
    )
    checklist = work / "review_checklist.md"
    checklist.write_text("# Review\n", encoding="utf-8")
    publish = work / "publish_info.md"
    publish.write_text("# Publish\n", encoding="utf-8")
    render_job_id = "phase1_demo"
    quality = {
        "schema_version": "1.0",
        "job_id": render_job_id,
        "status": "passed",
        "scene_count": 5,
        "media": {
            "path": "final_master.mp4",
            "sha256": _sha(final_master),
            "bytes": final_master.stat().st_size,
            "duration_seconds": 35,
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "video_codec": "h264",
            "audio_codec": "aac",
        },
        "narration": {"mode": "tts", "segments_count": 5},
        "subtitle": {
            "path": "subtitle.srt",
            "cue_count": 5,
            "mode": "burned_in",
        },
        "style": {
            "layout_mode": "knowledge_illustration",
            "pink_pig_status": "pass",
            "subtitle_region": {"x": 90, "y": 1120, "width": 900, "height": 460},
        },
        "checks": [{"name": "decode", "status": "passed"}],
        "error": None,
    }
    quality_path = work / "quality_report.json"
    _write_json(quality_path, quality)

    package_artifacts = [
        _artifact(final_master, work),
        _artifact(cover, work),
        _artifact(subtitle, work),
        _artifact(quality_path, work),
        _artifact(checklist, work),
        _artifact(publish, work),
    ]
    package: dict[str, object] = {
        "schema_version": "1.0",
        "job_id": render_job_id,
        "status": "ready_for_human_review",
        "input_mode": input_mode,
        "title": "Modbus RTU",
        "scene_count": 5,
        "quality_report": "quality_report.json",
        "asset_selection": {"assets": ["pig01"]},
        "artifacts": package_artifacts,
    }
    if input_mode == "local_reference":
        reference_names = (
            "reference_receipt.json",
            "reference_rights.json",
            "reference_report.json",
            "original_brief.json",
            "difference_report.json",
        )
        reference_evidence: dict[str, str] = {}
        for name in reference_names:
            value: dict[str, object] = (
                {"status": "ready_for_human_review"}
                if name == "difference_report.json"
                else {"evidence": name}
            )
            path = work / name
            _write_json(path, value)
            package_artifacts.append(_artifact(path, work))
            reference_evidence[name.removesuffix(".json")] = name
        package["reference_evidence"] = reference_evidence
    package_path = work / "review_package.json"
    _write_json(package_path, package)

    store.record_artifact(
        control_job_id,
        "final_master",
        final_master.relative_to(tmp_path).as_posix(),
        _sha(final_master),
    )
    store.record_artifact(
        control_job_id,
        "review_package",
        package_path.relative_to(tmp_path).as_posix(),
        _sha(package_path),
    )

    review = {
        "schema_version": "1.0",
        "control_job_id": control_job_id,
        "render_job_id": render_job_id,
        "reviewer": "Jovi",
        "decision": decision,
        "reviewed_at": "2026-08-22T00:00:00Z",
        "reviewed_artifact_sha256": _sha(final_master),
        "checklist": {
            "video_playable": True,
            "audio_clear": True,
            "subtitles_readable": True,
            "pink_pig_consistent": True,
            "technical_content_acceptable": True,
            "originality_acceptable": True,
        },
        "notes": "Reviewed locally.",
    }
    review_path = tmp_path / "state" / "human_review.json"
    _write_json(review_path, review)
    return store, control_job_id, review_path, final_master


def test_topic_job_prereview_is_ready_after_matching_human_review(
    tmp_path: Path,
) -> None:
    store, job_id, review, _video = _fixture(tmp_path)
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "ready"
    assert report["blockers"] == []
    assert all(report["checks"].values())


def test_changes_required_human_review_blocks_prereview(tmp_path: Path) -> None:
    store, job_id, review, _video = _fixture(
        tmp_path, decision="changes_required"
    )
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "human_review_not_approved" in report["blockers"]


def test_registered_hash_mismatch_blocks_prereview(tmp_path: Path) -> None:
    store, job_id, review, video = _fixture(tmp_path)
    video.write_bytes(b"tampered")
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "registered_artifact_hash_mismatch" in report["blockers"]


def test_local_reference_requires_ready_difference_report(tmp_path: Path) -> None:
    store, job_id, review, _video = _fixture(
        tmp_path, input_mode="local_reference"
    )
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "ready"
    assert report["checks"]["reference_difference_ready"] is True


def test_job_must_reach_pending_review(tmp_path: Path) -> None:
    _copy_schemas(tmp_path)
    store = CandidateStore(tmp_path / "state" / "phase1.sqlite3")
    store.initialize()
    job = store.create_job("fixture", "not-ready", "template", "topic")
    review = tmp_path / "review.json"
    _write_json(review, {})
    report = evaluate_job_prereview(
        store, str(job["job_id"]), review, project_root=tmp_path
    )
    assert report["status"] == "blocked"
    assert "job_not_pending_review" in report["blockers"]
