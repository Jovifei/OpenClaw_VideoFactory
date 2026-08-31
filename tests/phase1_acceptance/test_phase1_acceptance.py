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
    "phase1_subject_quality_report.schema.json",
    "phase1_subject_review_package.schema.json",
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
        "checks": [
            {"name": name, "status": "passed"}
            for name in (
                "decode",
                "resolution",
                "fps",
                "video_codec",
                "audio_codec",
                "narration",
                "subtitle",
                "style",
            )
        ],
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


def test_local_reference_allows_hashed_nested_difference_report_artifact(tmp_path: Path) -> None:
    store, job_id, review, _video = _fixture(tmp_path, input_mode="local_reference")
    package_record = next(item for item in store.artifacts(job_id) if item["artifact_type"] == "review_package")
    package_path = tmp_path / package_record["relative_path"]
    package = json.loads(package_path.read_text(encoding="utf-8"))
    artifact = next(item for item in package["artifacts"] if item["name"] == "difference_report.json")
    original = package_path.parent / artifact["path"]
    nested = package_path.parent / "evidence" / "difference_report.json"
    nested.parent.mkdir()
    original.replace(nested)
    artifact["path"] = "evidence/difference_report.json"
    artifact["sha256"] = _sha(nested)
    artifact["bytes"] = nested.stat().st_size
    _write_json(package_path, package)
    store.record_artifact(job_id, "review_package", package_path.relative_to(tmp_path).as_posix(), _sha(package_path))
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


def _subject_fixture(
    tmp_path: Path,
    *,
    decision: str = "approved",
    fixture_id: str = "local_subject",
    metadata_input_mode: str = "local_subject",
) -> tuple[CandidateStore, str, Path, Path, Path]:
    """A structured MOCK review fixture, never evidence of a Jovi approval."""
    _copy_schemas(tmp_path)
    store = CandidateStore(tmp_path / "state" / "phase1.sqlite3")
    store.initialize()
    created = store.create_job(
        fixture_id,
        "acceptance:local-subject",
        "template",
        "I2C pull-up budgeting",
        metadata={"input_mode": metadata_input_mode},
    )
    control_job_id = str(created["job_id"])
    for target in STAGES[1:]:
        store.advance(control_job_id, target)

    package_dir = tmp_path / "dist" / "subject" / "review_package"
    package_dir.mkdir(parents=True)
    preview = package_dir / "evidence" / "audible_preview.mp4"
    preview.parent.mkdir()
    preview.write_bytes(b"mock-audible-preview")
    artifact_specs = (
        ("inputs/topic_request.json", "input"),
        ("inputs/research_brief.json", "input"),
        ("inputs/script_candidates.json", "input"),
        ("inputs/selected_script.json", "input"),
        ("inputs/director_script.json", "input"),
        ("inputs/scene_plan.json", "input"),
        ("evidence/subject_media_result.json", "media_receipt"),
        ("evidence/timing_manifest.json", "timing"),
        ("evidence/render_report.json", "render"),
        ("evidence/visual_review.json", "visual_review"),
        ("evidence/audible_preview.mp4", "preview"),
        ("evidence/audible_preview.json", "preview_report"),
        ("evidence/jianying_manifest.json", "jianying"),
        ("evidence/visual_master.mp4", "visual"),
        ("evidence/contact_sheet.png", "contact_sheet"),
        ("evidence/post_render_check.json", "post_render"),
        ("evidence/native_subtitles.srt", "native_subtitles"),
    )
    artifacts: list[dict[str, object]] = []
    for relative, role in artifact_specs:
        path = package_dir / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"mock:{relative}".encode("utf-8"))
        artifacts.append({
            "name": path.name,
            "path": relative,
            "sha256": _sha(path),
            "bytes": path.stat().st_size,
            "role": role,
        })
    quality_path = package_dir / "subject_quality_report.json"
    quality = {
        "schema_version": "1.0",
        "job_id": control_job_id,
        "attempt": 1,
        "status": "passed",
        "preview": {
            "path": "evidence/audible_preview.mp4",
            "sha256": _sha(preview),
            "bytes": preview.stat().st_size,
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "duration_seconds": 30,
            "video_codec": "h264",
            "audio_codec": "aac",
            "full_decode": True,
        },
        "subtitle": {
            "mode": "native_jianying_track_not_burned_in",
            "review_srt": "evidence/native_subtitles.srt",
            "cue_count": 3,
            "burned_in": False,
        },
        "checks": [{"name": name, "status": "passed"} for name in (
            "h264", "aac", "fps_30", "canvas", "duration", "full_decode",
            "native_subtitles", "automatic_export_disabled",
        )],
        "human_review_required": True,
        "automatic_export": False,
    }
    _write_json(quality_path, quality)
    artifacts.append({
        "name": quality_path.name,
        "path": quality_path.name,
        "sha256": _sha(quality_path),
        "bytes": quality_path.stat().st_size,
        "role": "quality",
    })
    checklist = package_dir / "REVIEW_CHECKLIST.md"
    checklist.write_text("MOCK structured review fixture\n", encoding="utf-8")
    artifacts.append({
        "name": checklist.name,
        "path": checklist.name,
        "sha256": _sha(checklist),
        "bytes": checklist.stat().st_size,
        "role": "review_instructions",
    })
    package_path = package_dir / "review_package.json"
    _write_json(package_path, {
        "schema_version": "1.0",
        "package_kind": "phase1_subject",
        "job_id": control_job_id,
        "attempt": 1,
        "status": "ready_for_human_review",
        "preview_status": "preview_not_jianying_export",
        "title": "MOCK subject preview",
        "input_mode": "topic",
        "human_review_required": True,
        "automatic_export": False,
        "media_receipt": "evidence/subject_media_result.json",
        "quality_report": quality_path.name,
        "review_checklist": checklist.name,
        "artifacts": artifacts,
    })
    store.record_artifact(
        control_job_id, "final_master", preview.relative_to(tmp_path).as_posix(), _sha(preview)
    )
    store.record_artifact(
        control_job_id, "review_package", package_path.relative_to(tmp_path).as_posix(), _sha(package_path)
    )
    render_job_id = f"phase1_subject_{control_job_id.removeprefix('job-')}"
    review_path = tmp_path / "state" / "mock_human_review.json"
    _write_json(review_path, {
        "schema_version": "1.0",
        "control_job_id": control_job_id,
        "render_job_id": render_job_id,
        "reviewer": "MOCK_STRUCTURED_REVIEWER",
        "decision": decision,
        "reviewed_at": "2026-08-31T00:00:00Z",
        "reviewed_artifact_sha256": _sha(preview),
        "checklist": {name: True for name in (
            "video_playable", "audio_clear", "subtitles_readable",
            "pink_pig_consistent", "technical_content_acceptable", "originality_acceptable",
        )},
        "notes": "MOCK fixture only; not a user approval.",
    })
    return store, control_job_id, review_path, package_path, preview


def test_local_subject_prereview_binds_mock_review_to_packaged_preview(tmp_path: Path) -> None:
    store, job_id, review, _package, preview = _subject_fixture(tmp_path)
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "ready"
    assert report["input_mode"] == "topic"
    assert report["render_job_id"] == f"phase1_subject_{job_id.removeprefix('job-')}"
    assert report["final_master_sha256"] == _sha(preview)


def test_local_subject_prereview_requires_exact_local_subject_metadata_and_fixture(tmp_path: Path) -> None:
    for fixture_id, metadata_input_mode in (
        ("local_subject", "topic"),
        ("local_topic", "local_subject"),
    ):
        root = tmp_path / f"{fixture_id}_{metadata_input_mode}"
        store, job_id, review, _package, _preview = _subject_fixture(
            root,
            fixture_id=fixture_id,
            metadata_input_mode=metadata_input_mode,
        )
        report = evaluate_job_prereview(store, job_id, review, project_root=root)
        assert report["status"] == "blocked"
        assert "review_package_invalid" in report["blockers"]


def test_local_subject_prereview_rejects_wrong_package_kind(tmp_path: Path) -> None:
    store, job_id, review, package, _preview = _subject_fixture(tmp_path)
    value = json.loads(package.read_text(encoding="utf-8"))
    value["package_kind"] = "legacy_subject"
    _write_json(package, value)
    store.record_artifact(job_id, "review_package", package.relative_to(tmp_path).as_posix(), _sha(package))
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "review_package_invalid" in report["blockers"]


def test_local_subject_prereview_requires_mock_approved_review(tmp_path: Path) -> None:
    store, job_id, review, _package, _preview = _subject_fixture(tmp_path, decision="changes_required")
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "human_review_not_approved" in report["blockers"]


def test_local_subject_prereview_rejects_unverified_native_subtitles(tmp_path: Path) -> None:
    store, job_id, review, package, _preview = _subject_fixture(tmp_path)
    value = json.loads(package.read_text(encoding="utf-8"))
    native = next(item for item in value["artifacts"] if item["role"] == "native_subtitles")
    native["sha256"] = "0" * 64
    _write_json(package, value)
    store.record_artifact(job_id, "review_package", package.relative_to(tmp_path).as_posix(), _sha(package))
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "review_package_artifact_mismatch" in report["blockers"]


def test_local_subject_prereview_rejects_wrong_package_id_and_missing_quality(tmp_path: Path) -> None:
    store, job_id, review, package, _preview = _subject_fixture(tmp_path)
    value = json.loads(package.read_text(encoding="utf-8"))
    value["job_id"] = "job-" + "f" * 24
    value["artifacts"] = [item for item in value["artifacts"] if item["role"] != "quality"]
    _write_json(package, value)
    store.record_artifact(job_id, "review_package", package.relative_to(tmp_path).as_posix(), _sha(package))
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "review_package_invalid" in report["blockers"]


def test_local_subject_prereview_requires_final_master_to_be_packaged_preview(tmp_path: Path) -> None:
    store, job_id, review, package, _preview = _subject_fixture(tmp_path)
    visual = package.parent / "evidence" / "visual_master.mp4"
    store.record_artifact(job_id, "final_master", visual.relative_to(tmp_path).as_posix(), _sha(visual))
    review_value = json.loads(review.read_text(encoding="utf-8"))
    review_value["reviewed_artifact_sha256"] = _sha(visual)
    _write_json(review, review_value)
    report = evaluate_job_prereview(store, job_id, review, project_root=tmp_path)
    assert report["status"] == "blocked"
    assert "quality_report_not_passed" in report["blockers"]
