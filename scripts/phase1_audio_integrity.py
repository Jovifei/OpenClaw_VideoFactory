"""Audit retained source-aligned audio without synthesizing or rendering media."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from video_factory.pipeline.audio_planner import (
    _decode_pcm_for_integrity,
    _probe_pcm_layout,
    _verify_complete_aligned_segment,
)


def _aligned_path(audio_path: Path, filename: str) -> Path:
    candidates = (
        audio_path.parent / "aligned" / filename,
        audio_path.parent / filename,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(filename)


def _audit_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    passes = fixture.get("passes")
    if not isinstance(passes, list):
        raise ValueError("fixture_passes_missing")
    final_pass = next((item for item in passes if int(item.get("rewrite_count", 0)) == 1 and "aligned_audio" in item), None)
    if not isinstance(final_pass, dict):
        raise ValueError("final_aligned_pass_missing")
    aligned_audio = final_pass["aligned_audio"]
    audio_path = Path(str(aligned_audio["path"]))
    aligned_segments = aligned_audio.get("segments")
    if not isinstance(aligned_segments, list) or not aligned_segments:
        raise ValueError("aligned_segments_missing")
    segment_evidence: list[dict[str, Any]] = []
    pcm_parts: list[bytes] = []
    layout: tuple[int, int] | None = None
    for segment in aligned_segments:
        raw_path = Path(str(segment["audio_path"]))
        aligned_path = _aligned_path(audio_path, str(segment["aligned_audio_file"]))
        evidence, current_layout, aligned_pcm = _verify_complete_aligned_segment(
            raw_path,
            aligned_path,
            scene_id=str(segment["scene_id"]),
        )
        if layout is None:
            layout = current_layout
        elif layout != current_layout:
            raise ValueError("pcm_layout_changed")
        segment_evidence.append({
            "scene_id": segment["scene_id"],
            "raw_path": str(raw_path),
            "aligned_path": str(aligned_path),
            "raw_audio_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "declared_raw_audio_sha256": segment.get("raw_audio_sha256") or segment.get("audio_sha256"),
            "aligned_audio_sha256": hashlib.sha256(aligned_path.read_bytes()).hexdigest(),
            "declared_aligned_audio_sha256": segment.get("aligned_audio_sha256"),
            "evidence": evidence,
        })
        pcm_parts.append(aligned_pcm)
    assert layout is not None
    expected_pcm = b"".join(pcm_parts)
    actual_pcm = _decode_pcm_for_integrity(audio_path, sample_rate=layout[0], channels=layout[1])
    if actual_pcm != expected_pcm:
        raise ValueError("concatenated_segments_not_preserved")
    actual_hash = hashlib.sha256(audio_path.read_bytes()).hexdigest()
    declared_hash = aligned_audio.get("sha256")
    expected_endpoint = float(final_pass["allocation"]["duration_seconds"])
    actual_endpoint = float(aligned_audio["duration_seconds"])
    endpoint_delta = round(actual_endpoint - expected_endpoint, 6)
    if abs(endpoint_delta) > 0.05:
        raise ValueError("audio_endpoint_mismatch")
    return {
        "topic": fixture.get("topic"),
        "topic_digest": fixture.get("topic_digest"),
        "status": "OBJECTIVE_AUDIO_INTEGRITY_PASS",
        "audio_path": str(audio_path),
        "audio_sha256": actual_hash,
        "declared_audio_sha256": declared_hash,
        "audio_sha256_matches_report": actual_hash == declared_hash,
        "pcm_sample_rate": layout[0],
        "pcm_channels": layout[1],
        "segments_in_order": True,
        "expected_concatenated_pcm_sha256": hashlib.sha256(expected_pcm).hexdigest(),
        "actual_concatenated_pcm_sha256": hashlib.sha256(actual_pcm).hexdigest(),
        "expected_endpoint_seconds": expected_endpoint,
        "actual_endpoint_seconds": actual_endpoint,
        "endpoint_delta_seconds": endpoint_delta,
        "segments": segment_evidence,
        "human_audio_quality_review": fixture.get("listening_review"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    fixtures = report.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError("fixtures_missing")
    result = {
        "schema_version": "phase1_audio_integrity_evidence_v1",
        "source_report": str(args.report),
        "source_report_sha256": hashlib.sha256(args.report.read_bytes()).hexdigest(),
        "contract": {
            "raw_pcm_prefix_must_survive": True,
            "post_raw_pcm_must_be_silence": True,
            "segments_must_remain_in_order": True,
            "asr_required": False,
            "human_quality_review_separate": True,
        },
        "fixtures": [_audit_fixture(fixture) for fixture in fixtures],
        "status": "OBJECTIVE_AUDIO_INTEGRITY_PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output), "fixtures": len(fixtures)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
