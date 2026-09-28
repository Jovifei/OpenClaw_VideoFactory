"""Source-aligned audio adapter for the source-bound subject route.

The subject route owns editorial planning and TechnicalExplainer visuals.  This
module only adapts that plan to the existing shared measured-narration helper;
it does not create a second TTS planner or choose visual assets as semantic
authority.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from video_factory.pipeline.narration_timing import plan_source_aligned_narration
from video_factory.pipeline.registry import load_pink_pig_registry


FPS = 30
FRAME_TOLERANCE_MICROSECONDS = (1_000_000 + FPS - 1) // FPS


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_subject_audio_storyboard(
    script: Mapping[str, Any],
    *,
    registry: Any,
    aspect: str,
) -> dict[str, Any]:
    """Build a narration-only storyboard for the shared timing helper.

    The registry asset is a timing compiler binding only.  The subject visual
    route remains the separate ``phase1_scene_plan`` / TechnicalExplainer path.
    """

    beats = script.get("beats")
    if not isinstance(beats, list) or not (5 <= len(beats) <= 9):
        raise ValueError("subject_audio_script_beats_invalid")
    if aspect not in {"16:9", "9:16"}:
        raise ValueError("subject_audio_aspect_invalid")
    scenes = []
    for index, beat in enumerate(beats, start=1):
        if not isinstance(beat, Mapping) or not str(beat.get("narration", "")).strip():
            raise ValueError("subject_audio_beat_invalid")
        scenes.append(
            {
                "scene_id": f"s{index:02d}",
                "order": index,
                "narration": str(beat["narration"]),
                "caption": str(beat.get("subtitle", beat["narration"])),
                "pose": "normal",
                "asset_id": str(registry.default_asset_id),
                "duration_intent": {"mode": "narration"},
                "transition_out": None,
            }
        )
    return {
        "schema_version": "1.0",
        "storyboard_id": "phase1_subject_source_aligned_audio",
        "title": str(script.get("title", "")),
        "ip": {"character_id": registry.character_id, "registry_version": registry.registry_version},
        "globals": {
            "aspect_ratio": aspect,
            "fps": FPS,
            "default_scene_seconds": 2.5,
            "default_transition": "fade",
            "transition_seconds": 0.4,
            "transition_mode": "technical_cut",
            "narration_cps": 4.7,
            "min_scene_seconds": 1.2,
            "max_scene_seconds": 30.0,
        },
        "scenes": scenes,
    }


def build_subject_audio_factual_brief(research: Mapping[str, Any]) -> dict[str, Any]:
    """Map the subject research schema to the shared fact-validation schema."""

    facts = research.get("facts")
    if not isinstance(facts, list):
        raise ValueError("subject_audio_research_facts_invalid")
    mapped: list[dict[str, Any]] = []
    for fact in facts:
        if not isinstance(fact, Mapping):
            raise ValueError("subject_audio_research_fact_invalid")
        fact_id = str(fact.get("id", "")).strip()
        claim = str(fact.get("claim", "")).strip()
        if not fact_id or not claim:
            raise ValueError("subject_audio_research_fact_invalid")
        mapped.append(
            {
                "fact_id": fact_id,
                "claim": claim,
                "source_ids": [str(value) for value in fact.get("source_ids", [])],
            }
        )
    source_values: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    for source in research.get("sources", []):
        if not isinstance(source, Mapping):
            raise ValueError("subject_audio_research_source_invalid")
        source_id = str(source.get("id", "")).strip()
        if not source_id or source_id in source_ids:
            raise ValueError("subject_audio_research_source_id_invalid")
        source_ids.add(source_id)
        source_values.append(
            {
                "source_id": source_id,
                "title": str(source.get("title", source_id)),
                "publisher": str(source.get("publisher", source.get("title", source_id))),
                "url": str(source.get("url", "")),
                "kind": str(source.get("kind", "primary_source")),
            }
        )
    if any(source_id not in source_ids for fact in mapped for source_id in fact["source_ids"]):
        raise ValueError("subject_audio_research_source_unresolved")
    return {
        "schema_version": "1.0",
        "topic": str(research.get("topic", "")),
        "topic_digest": str(research.get("topic_digest", "")),
        "sources": source_values,
        "facts": mapped,
    }


def build_subject_source_aligned_audio(
    *,
    script_path: Path,
    scene_plan_path: Path,
    topic: Mapping[str, Any],
    research: Mapping[str, Any],
    repo_root: Path,
    work_dir: Path,
    timing_root: Path,
    voice: str = "Microsoft Huihui Desktop",
    provider: str = "windows-sapi",
) -> dict[str, Any]:
    """Run the shared measured planner and emit a timing-manifest adapter.

    No video is rendered here.  The returned manifest is consumed by the
    existing Remotion/Jianying adapters when a media candidate is explicitly
    authorized later.
    """

    script = json.loads(script_path.read_text(encoding="utf-8"))
    scene_plan = json.loads(scene_plan_path.read_text(encoding="utf-8"))
    if not isinstance(script, dict) or not isinstance(scene_plan, dict):
        raise ValueError("subject_audio_plan_input_invalid")
    aspect = str(topic.get("aspect", ""))
    registry = load_pink_pig_registry(repo_root=repo_root)
    audio_storyboard = build_subject_audio_storyboard(script, registry=registry, aspect=aspect)
    factual_brief = build_subject_audio_factual_brief(research)
    work_dir = Path(work_dir).resolve()
    timing_root = Path(timing_root).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    timing_root.mkdir(parents=True, exist_ok=True)
    measured = plan_source_aligned_narration(
        storyboard=audio_storyboard,
        script=script,
        factual_brief=factual_brief,
        registry=registry,
        repo_root=Path(repo_root).resolve(),
        work_dir=work_dir,
        voice=voice,
        provider=provider,
    )
    timeline = measured["timeline"]
    objective = measured["objective_audio_integrity"]
    if not isinstance(objective, Mapping) or objective.get("status") != "passed":
        raise ValueError("subject_audio_objective_integrity_failed")
    offsets = objective.get("scene_offsets") if isinstance(objective, Mapping) else None
    segments = measured.get("segments")
    if not isinstance(offsets, list) or not isinstance(segments, (tuple, list)) or len(offsets) != len(segments):
        raise ValueError("subject_audio_integrity_shape_invalid")
    if len(segments) != len(script.get("beats", [])) or len(segments) != len(scene_plan.get("scenes", [])):
        raise ValueError("subject_audio_scene_count_mismatch")

    aligned_root = timing_root / "shared_aligned"
    aligned_root.mkdir(parents=True, exist_ok=False)
    manifest_segments: list[dict[str, Any]] = []
    integrity_segments: list[dict[str, Any]] = []
    for index, (segment, offset, beat, scene) in enumerate(
        zip(segments, offsets, script["beats"], scene_plan["scenes"], strict=True), start=1
    ):
        if str(segment.get("scene_id")) != f"s{index:02d}" or str(scene.get("scene_index")) != str(index):
            raise ValueError("subject_audio_scene_identity_mismatch")
        aligned_name = str(segment.get("aligned_audio_file", ""))
        aligned_source = Path(str(measured["audio_path"])).parent / "aligned" / aligned_name
        if not aligned_source.is_file():
            raise ValueError("subject_audio_aligned_segment_missing")
        aligned_target = aligned_root / f"scene_{index:02d}.wav"
        shutil.copyfile(aligned_source, aligned_target)
        start_us = round(float(offset["start_seconds"]) * 1_000_000)
        end_us = round(float(offset["end_seconds"]) * 1_000_000)
        if start_us < 0 or end_us <= start_us:
            raise ValueError("subject_audio_scene_offset_invalid")
        duration_us = end_us - start_us
        segment_sha = _sha(aligned_target)
        manifest_segments.append(
            {
                "index": index,
                "start_microseconds": start_us,
                "end_microseconds": end_us,
                "duration_microseconds": duration_us,
                "scene_start_microseconds": start_us,
                "scene_end_microseconds": end_us,
                "audio_relative_path": aligned_target.relative_to(timing_root).as_posix(),
                "audio_filename": aligned_target.name,
                "audio_sha256": segment_sha,
                "narration_sha256": hashlib.sha256(str(beat["narration"]).encode("utf-8")).hexdigest(),
                "subtitle_sha256": hashlib.sha256(str(beat["subtitle"]).encode("utf-8")).hexdigest(),
                "audio_integrity": segment.get("audio_integrity"),
            }
        )
        integrity_segments.append(
            {
                "scene_id": str(segment.get("scene_id")),
                "raw_audio_sha256": segment.get("raw_audio_sha256"),
                "aligned_audio_sha256": segment.get("aligned_audio_sha256"),
                "adapter_audio_sha256": segment_sha,
                "audio_integrity": segment.get("audio_integrity"),
            }
        )

    visual_duration = round(float(timeline["total_duration_seconds"]), 3)
    voice_end_us = manifest_segments[-1]["end_microseconds"]
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "timing_manifest_ready",
        "source_aligned_narration": True,
        "script": {"filename": script_path.name, "sha256": _sha(script_path), "title": str(script.get("title", ""))},
        "scene_plan": {"filename": scene_plan_path.name, "sha256": _sha(scene_plan_path)},
        "timing": {
            "fps": FPS,
            "inter_segment_gap_microseconds": 0,
            "frame_tolerance_microseconds": FRAME_TOLERANCE_MICROSECONDS,
            "authority": "shared_source_aligned_measured_tts",
        },
        "voice": {
            "speaker": voice,
            "requested_backend": provider,
            "used_backends": [provider],
            "segment_count": len(manifest_segments),
            "rendered_audio_segment_count": len(manifest_segments),
            "voice_end_microseconds": voice_end_us,
            "timeline_duration_seconds": round(voice_end_us / 1_000_000, 6),
            "coverage_ratio": round(voice_end_us / (visual_duration * 1_000_000), 6),
            "minimum_coverage_ratio": 0.75,
            "source_kind": "shared_source_aligned_narration",
        },
        "visual_duration_seconds": visual_duration,
        "probe": {
            "draft_relative_path": "shared_source_aligned",
            "drafts_root_drive": timing_root.drive.upper(),
            "audio_paths_are_runtime_relative": True,
        },
        "segments": manifest_segments,
        "source_aligned_audio": {
            "mode": "source_aligned_measured_tts",
            "objective_audio_integrity": objective,
            "original_script_sha256": measured["original_script_sha256"],
            "final_script_sha256": measured["final_script_sha256"],
            "final_timeline_sha256": measured["final_timeline_sha256"],
            "final_srt_sha256": measured["final_srt_sha256"],
        },
    }
    manifest_path = timing_root.parent / "timing_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    integrity_doc = {
        "schema_version": "phase1_audio_integrity_v1",
        "status": "passed",
        "objective": objective,
        "segments": integrity_segments,
        "artifact_hashes": {
            "script_sha256": _sha(script_path),
            "scene_plan_sha256": _sha(scene_plan_path),
            "aligned_audio_sha256": _sha(Path(str(measured["audio_path"]))),
        },
        "source": "plan_source_aligned_narration",
    }
    integrity_path = timing_root.parent / "audio_integrity.json"
    integrity_path.write_text(json.dumps(integrity_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["source_aligned_audio"]["audio_integrity_ref"] = integrity_path.name
    manifest["source_aligned_audio"]["audio_integrity_sha256"] = _sha(integrity_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "audio_integrity": integrity_doc,
        "audio_integrity_path": integrity_path,
        "timing_root": timing_root,
        "visual_duration_seconds": visual_duration,
        "storyboard": audio_storyboard,
        "factual_brief": factual_brief,
    }


__all__ = [
    "build_subject_audio_storyboard",
    "build_subject_audio_factual_brief",
    "build_subject_source_aligned_audio",
]
