from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from src.factory.reference_video import build_difference_report, build_original_brief
from video_factory.pipeline.errors import FactoryContractError


ROOT = Path(__file__).resolve().parents[2]


def _factual(topic: str) -> dict[str, object]:
    digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    return {
        "schema_version": "1.0",
        "topic_digest": digest,
        "review_status": "verified",
        "facts": [{"fact_id": "fact_one", "claim": "A verified engineering claim.", "source_ids": ["source_a"]}],
        "sources": [
            {"source_id": "source_a", "title": "A", "publisher": "A", "url": "https://example.test/a", "kind": "standard"},
            {"source_id": "source_b", "title": "B", "publisher": "B", "url": "https://example.test/b", "kind": "official_document"},
        ],
    }


def _report(topic: str = "原创工程主题") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "reference_id": "ref_" + "a" * 24,
        "source_sha256": "b" * 64,
        "duration_seconds": 10.0,
        "resolution": {"width": 320, "height": 180},
        "scenes": [{
            "scene_id": "s01", "start_seconds": 0.0, "end_seconds": 10.0, "duration_seconds": 10.0,
            "representative_frame_time_seconds": 5.0, "visual_description": "local_visual_analysis_unavailable",
            "caption_summary": "not_extracted_in_conservative_mode", "audio_summary": "no_audio_track",
        }],
        "style_fingerprint": {
            "pace": "slow", "shot_density_per_second": 0.1, "median_shot_duration_seconds": 10.0,
            "scene_count": 1, "structure_summary": "single_scene",
        },
        "transcript": [],
        "asr": {"status": "unavailable", "model": None, "reason": "no_audio_track"},
    }


def test_reference_contract_schemas_are_valid() -> None:
    for path in (ROOT / "schemas" / "video").glob("reference*.schema.json"):
        jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    for name in ("original_brief", "difference_report", "phase1_review_package"):
        path = ROOT / "schemas" / "video" / f"{name}.schema.json"
        jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_original_brief_keeps_only_abstract_reference_fields() -> None:
    topic = "原创工程主题"
    brief = {"topic": topic, "factual_brief": _factual(topic)}
    original = build_original_brief(brief, _report())
    assert set(original) == {"schema_version", "input_mode", "topic", "factual_brief", "reference_sha256", "reference_abstraction"}
    assert "transcript" not in original
    assert "path" not in json.dumps(original, ensure_ascii=False)


def test_original_brief_blocks_source_path_injection() -> None:
    topic = "原创工程主题"
    brief = {"topic": topic, "factual_brief": _factual(topic), "source_path": "input/reference_videos/source.mp4"}
    with pytest.raises(FactoryContractError) as caught:
        build_original_brief(brief, _report())
    assert caught.value.code == "original_brief_invalid"


@pytest.mark.parametrize(
    "injected",
    [
        {"sources": [{"source_id": "source_a", "title": "A", "publisher": "A", "url": "file:///E:/private/reference.mp4", "kind": "standard"},
                    {"source_id": "source_b", "title": "B", "publisher": "B", "url": "https://example.test/b", "kind": "official_document"}]},
        {"facts": [{"fact_id": "fact_one", "claim": "input/reference_videos/source.mp4", "source_ids": ["source_a"]}]},
    ],
)
def test_original_brief_blocks_nested_source_path_injection(injected: dict[str, object]) -> None:
    topic = "原创工程主题"
    brief = {"topic": topic, "factual_brief": _factual(topic)}
    brief["factual_brief"] = {**brief["factual_brief"], **injected}  # type: ignore[arg-type]
    with pytest.raises(FactoryContractError) as caught:
        build_original_brief(brief, _report())
    assert caught.value.code == "original_brief_invalid"


def test_difference_report_scans_render_and_audio_manifests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_sha = "b" * 64
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    report = _report()
    report["source_sha256"] = source_sha
    (runtime / "reference_report.json").write_text(json.dumps(report), encoding="utf-8")
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    output = work_dir / "final_master.mp4"
    output.write_bytes(b"new-output")
    (work_dir / "render_job.yaml").write_text(
        "audio:\n  tts:\n    provider: windows-sapi\n", encoding="utf-8"
    )
    (work_dir / "render_manifest.json").write_text(
        json.dumps({"asset_path": "input/reference_videos/" + source_sha + ".mp4"}), encoding="utf-8"
    )
    bundle = {
        "job_id": "phase1_ref_test",
        "runtime_root": runtime,
        "receipt": {"source_sha256": source_sha, "source_name": "source.mp4"},
    }
    monkeypatch.setattr("src.factory.reference_video._asset_registry_map", lambda: {"asset": "assets/pink_pig/pig01.png"})
    result = build_difference_report(
        bundle=bundle,
        work_dir=work_dir,
        output_path=output,
        asset_selection={"selections": [{"asset_id": "asset", "relative_path": "assets/pink_pig/pig01.png"}]},
    )
    assert result["status"] == "blocked"
    assert result["checks"]["reference_path_absent"] == "blocked"
