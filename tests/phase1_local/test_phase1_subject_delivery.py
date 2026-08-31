from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.factory.phase1_subject_delivery import SubjectDeliveryRequest, build_subject_review_package


_MOCK_CONTROL_JOB_ID = "job-" + "a" * 24
from video_factory.pipeline import validation


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def _media_root(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    root = tmp_path / "media"
    visual = _write(root / "visual_master.mp4", b"synthetic-visual-master")
    clip = _write(root / "clips" / "scene_01.mp4", b"synthetic-clip")
    still = _write(root / "stills" / "scene_01.png", b"synthetic-still")
    contact = _write(root / "contact_sheet.png", b"synthetic-contact-sheet")
    post = _write(root / "post_render_check.json", {"status": "passed"})
    paths = {
        "timing_manifest": _write(root / "timing_manifest.json", {"status": "timing_manifest_ready", "segments": [{"index": 1, "start_microseconds": 0, "end_microseconds": 30_000_000, "subtitle_sha256": hashlib.sha256("测试字幕".encode()).hexdigest()}], "voice": {"rendered_audio_segment_count": 1, "voice_end_microseconds": 30_000_000, "coverage_ratio": 1.0}}),
        "render_report": _write(root / "render_report.json", {"status": "passed", "visual": {"filename": visual.name, "sha256": _sha(visual), "audio_present": False, "burned_in_subtitles": False, "scene_timing": [{"scene_index": 1, "still": {"filename": "stills/scene_01.png", "sha256": _sha(still)}, "clip": {"filename": "clips/scene_01.mp4", "sha256": _sha(clip)} }]}}),
        "visual_review": _write(root / "visual_review.json", {"status": "passed", "visual": {"sha256": _sha(visual)}, "contact_sheet": {"sha256": _sha(contact)}, "post_render_report": {"sha256": _sha(post)}, "post_render": {"full_decode": True, "all_frame_scan": {"status": "passed"}}}),
        "preview": _write(root / "audible_preview.mp4", b"synthetic-preview-bytes"),
        "preview_report": _write(root / "audible_preview.json", {"status": "audio_preview_ready_for_manual_listening", "output": {"audio_present": True, "full_decode": "passed", "codec": "aac", "mean_volume_db": -20.0, "max_volume_db": -2.0}, "sync_validation": {"status": "passed"}, "audio_source": {"segment_count": 1}}),
        "jianying_report": _write(root / "jianying_manifest.json", {"status": "draft_ready_for_manual_jianying_review", "sync_validation": {"status": "passed"}, "audio_validation": {"status": "passed", "muted": False, "segment_count": 1}, "subtitle_validation": {"status": "passed", "segment_count": 1, "authoritative_layer": "jianying_native_subtitles_track", "burned_in_visual_must_be_false": True}, "tracks": [{"name": "VideoTrack", "segment_count": 1, "duration_microseconds": 30_000_000}, {"name": "VoiceOver", "segment_count": 1}, {"name": "Subtitles", "segment_count": 1}], "export": {"automatic_export": "disabled"}}),
        "visual": visual, "contact_sheet": contact, "post_render_check": post, "clip": clip, "still": still,
    }
    receipt = {
        "schema_version": "1.0",
        "status": "PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW",
        "candidate_status": "PHASE1_TOPIC_DRAFT_READY_FOR_JOVI_REVIEW",
        "ready_status": "READY",
        "automatic_export": False,
        "draft_name": "Synthetic_only",
        "paths": {key: str(paths[key]) for key in ("timing_manifest", "render_report", "visual_review", "preview", "preview_report", "jianying_report")},
        "hashes": {key: _sha(paths[key]) for key in ("timing_manifest", "render_report", "visual_review", "preview", "preview_report", "jianying_report")},
    }
    _write(root / "subject_media_result.json", receipt)
    return root, paths


def _inputs(tmp_path: Path) -> Path:
    root = tmp_path / "inputs"
    for name in ("topic_request", "research_brief", "script_candidates", "selected_script", "scene_plan"):
        _write(root / f"{name}.json", {"name": name})
    _write(root / "director_script.json", {"beats": [{"subtitle": "测试字幕"}]})
    return root


def _probe(_: Path) -> dict[str, object]:
    return {"width": 1920, "height": 1080, "fps": 30.0, "duration_seconds": 30.0, "video_codec": "h264", "audio_codec": "aac"}


@pytest.mark.parametrize("role", ["preview", "native_subtitles", "quality"])
@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_subject_package_requires_exactly_one_evidence_role(tmp_path: Path, role: str, mutation: str) -> None:
    from video_factory.pipeline.errors import FactoryContractError

    media_root, _ = _media_root(tmp_path)
    result = build_subject_review_package(
        SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9"),
        probe_media=_probe, decode_media=lambda _: True,
    )
    document = json.loads(Path(result["review_package"]).read_text(encoding="utf-8"))
    entry = next(item for item in document["artifacts"] if item["role"] == role)
    if mutation == "missing":
        entry["role"] = "input"  # Preserve count: only the required role is absent.
    else:
        document["artifacts"].append({**entry, "name": "duplicate.bin", "path": "evidence/duplicate.bin"})
    with pytest.raises(FactoryContractError):
        validation.validate(document, "phase1_subject_review_package")


def test_subject_delivery_builds_strict_self_contained_preview_package(tmp_path: Path) -> None:
    media_root, _ = _media_root(tmp_path)
    outcome = build_subject_review_package(SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9"), probe_media=_probe, decode_media=lambda _: True)
    package = Path(outcome["package_path"])
    review = json.loads((package / "review_package.json").read_text(encoding="utf-8"))
    quality = json.loads((package / "subject_quality_report.json").read_text(encoding="utf-8"))
    validation.validate(review, "phase1_subject_review_package")
    validation.validate(quality, "phase1_subject_quality_report")
    assert review["status"] == "ready_for_human_review"
    assert review["preview_status"] == "preview_not_jianying_export" and review["input_mode"] == "topic"
    assert review["human_review_required"] is True and review["automatic_export"] is False
    assert quality["subtitle"]["mode"] == "native_jianying_track_not_burned_in"
    assert all(not Path(item["path"]).is_absolute() and (package / item["path"]).is_file() for item in review["artifacts"])
    assert (package / "evidence" / "native_subtitles.srt").is_file()


@pytest.mark.parametrize("mutation", ["escape", "tamper"])
def test_subject_delivery_rejects_receipt_escape_or_tamper(tmp_path: Path, mutation: str) -> None:
    media_root, paths = _media_root(tmp_path)
    receipt_path = media_root / "subject_media_result.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if mutation == "escape":
        outside = _write(tmp_path / "outside.mp4", b"outside")
        receipt["paths"]["preview"] = str(outside)
        receipt["hashes"]["preview"] = _sha(outside)
        _write(receipt_path, receipt)
    else:
        paths["preview"].write_bytes(b"tampered")
    with pytest.raises(ValueError, match="subject_delivery_media_receipt_invalid"):
        build_subject_review_package(SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9"), probe_media=_probe, decode_media=lambda _: True)


def test_subject_delivery_rejects_package_reparse_escape(tmp_path: Path) -> None:
    media_root, _ = _media_root(tmp_path)
    package_root = tmp_path / "dist"
    package_root.mkdir()
    (package_root / "attempt_1").write_bytes(b"not a directory")
    with pytest.raises(ValueError, match="subject_delivery_package_path_invalid"):
        build_subject_review_package(SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, package_root, 30, "16:9"), probe_media=_probe, decode_media=lambda _: True)


@pytest.mark.parametrize("mutation", ["render_hash", "native_subtitle"])
def test_subject_delivery_rechecks_genuine_render_and_native_subtitle_evidence(tmp_path: Path, mutation: str) -> None:
    media_root, paths = _media_root(tmp_path)
    target = paths["render_report"] if mutation == "render_hash" else paths["jianying_report"]
    value = json.loads(target.read_text(encoding="utf-8"))
    if mutation == "render_hash":
        value["visual"]["scene_timing"][0]["clip"]["sha256"] = "0" * 64
    else:
        value["subtitle_validation"]["authoritative_layer"] = "not_native"
    target.write_text(json.dumps(value), encoding="utf-8")
    receipt = json.loads((media_root / "subject_media_result.json").read_text(encoding="utf-8"))
    receipt["hashes"]["render_report" if mutation == "render_hash" else "jianying_report"] = _sha(target)
    (media_root / "subject_media_result.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError):
        build_subject_review_package(SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9"), probe_media=_probe, decode_media=lambda _: True)


def test_subject_delivery_fails_closed_without_schema_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    media_root, _ = _media_root(tmp_path)
    monkeypatch.setattr(validation, "is_available", lambda: False)
    with pytest.raises(ValueError, match="subject_delivery_schema_validation_unavailable"):
        build_subject_review_package(SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9"), probe_media=_probe, decode_media=lambda _: True)


def test_subject_delivery_cancellation_during_decode_never_writes_ready_manifest(tmp_path: Path) -> None:
    media_root, _ = _media_root(tmp_path)
    cancelled = {"value": False}
    def decode(_: Path) -> bool:
        cancelled["value"] = True
        return True
    request = SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9")
    with pytest.raises(ValueError, match="subject_delivery_cancelled"):
        build_subject_review_package(request, probe_media=_probe, decode_media=decode, cancel_requested=lambda: cancelled["value"])
    package = tmp_path / "dist" / "attempt_1" / "review_package"
    assert not (package / "review_package.json").exists()
    assert json.loads((package / "cancelled.json").read_text(encoding="utf-8"))["status"] == "cancelled_before_ready_manifest"


def test_subject_delivery_canonicalizes_alternate_preview_filename(tmp_path: Path) -> None:
    media_root, paths = _media_root(tmp_path)
    alternate = media_root / "preview_from_tool.mp4"; paths["preview"].replace(alternate)
    receipt_path = media_root / "subject_media_result.json"; receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["paths"]["preview"] = str(alternate); receipt["hashes"]["preview"] = _sha(alternate)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    outcome = build_subject_review_package(SubjectDeliveryRequest(_MOCK_CONTROL_JOB_ID, 1, _inputs(tmp_path), media_root, tmp_path / "dist", 30, "16:9"), probe_media=_probe, decode_media=lambda _: True)
    package_preview = Path(outcome["preview"])
    quality = json.loads((package_preview.parents[1] / "subject_quality_report.json").read_text(encoding="utf-8"))
    assert package_preview.name == "audible_preview.mp4" and package_preview.is_file()
    assert quality["preview"]["path"] == "evidence/audible_preview.mp4" and quality["preview"]["sha256"] == _sha(package_preview)
