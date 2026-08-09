"""Run the local pink-pig image-to-MP4 MVP without any OpenClaw dependency.

Supports two modes:
  --config  Legacy mode (directory-scan driven, unchanged behavior)
  --job     New mode (storyboard-driven, Phase 1 productization)
  --topic   Director mode (topic → Storyboard → existing Video Factory)
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from video_factory.pipeline.asset_loader import build_asset_manifest
from video_factory.pipeline.export import write_json
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.renderer import render_video
from video_factory.pipeline.render_report import build_render_report
from video_factory.pipeline.subtitle import build_srt, build_srt_from_timeline
from video_factory.pipeline.timeline import build_timeline, to_render_timeline
from video_factory.pipeline.mascot import load_mascot_contract


ROOT = Path(__file__).resolve().parent


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("config_missing")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("config_invalid")
    required = {"asset_dir", "script", "output", "image_duration_seconds", "transition_seconds", "transitions"}
    if not required.issubset(value):
        raise ValueError("config_required_field_missing")
    return value


def resolve(config_path: Path, value: str) -> Path:
    return (config_path.parent / value).resolve()


# ---------------------------------------------------------------------------
# Legacy --config mode (unchanged)
# ---------------------------------------------------------------------------

def run(config_path: Path) -> dict[str, object]:
    config_path = config_path.resolve()
    config = load_config(config_path)
    asset_dir = resolve(config_path, str(config["asset_dir"]))
    output_path = (ROOT / str(config["output"])).resolve()
    manifest_path = (ROOT / str(config.get("asset_manifest", "dist/asset_manifest.json"))).resolve()
    timeline_path = (ROOT / str(config.get("timeline", "dist/video_timeline.json"))).resolve()
    subtitle_path = (ROOT / str(config.get("subtitle", "dist/subtitle.srt"))).resolve()
    audio_value = config.get("audio")
    audio_path = resolve(config_path, str(audio_value)) if audio_value else None
    mascot_contract = load_mascot_contract(ROOT, config.get("mascot"))
    manifest = build_asset_manifest(asset_dir)
    timeline = build_timeline(
        manifest,
        duration_seconds=float(config["image_duration_seconds"]),
        transitions=list(config["transitions"]),
    )
    wrap_value = config.get("subtitle_max_chars_per_line")
    wrap_chars = int(wrap_value) if wrap_value is not None else None
    captions = build_srt(
        resolve(config_path, str(config["script"])),
        timeline,
        subtitle_path,
        transition_seconds=float(config["transition_seconds"]),
        max_chars_per_line=wrap_chars,
        max_lines=2,
    )
    write_json(manifest_path, manifest)
    write_json(timeline_path, timeline)
    audio_mode = "file" if audio_path is not None else "silent"
    audio_loop = True
    audio_fallback_reason = None
    if config.get("audio_mode") == "tts_with_offline_fallback":
        from video_factory.pipeline.audio_planner import plan_audio

        audio_cfg = dict(config.get("audio_config", {}))
        audio_cfg.setdefault("strategy", "tts_with_offline_fallback")
        audio_cfg.setdefault("allow_network", True)
        audio_cfg.setdefault("fallback_bgm", "assets/pink_pig/demo_music.wav")
        narration_doc = {
            "total_duration_seconds": sum(float(item["duration"]) for item in timeline)
            - float(config["transition_seconds"]) * (len(timeline) - 1),
            "scenes": [
                {
                    "scene_id": f"s{index:02d}",
                    "duration": float(item["duration"]),
                    "narration": str(captions[index - 1]["text"]).replace("\n", " "),
                }
                for index, item in enumerate(timeline, start=1)
            ],
        }
        audio_work_dir = ROOT / str(config.get("audio_work_dir", "dist/audio_work"))
        audio_plan = plan_audio(
            narration_doc,
            work_dir=audio_work_dir,
            audio_config=audio_cfg,
            repo_root=ROOT,
        )
        audio_path = audio_plan.path
        audio_loop = audio_plan.loop
        audio_mode = audio_plan.mode
        audio_fallback_reason = audio_plan.fallback_reason
    subtitle_style = config.get("subtitle_style")
    if subtitle_style is not None and not isinstance(subtitle_style, dict):
        raise ValueError("subtitle_style_invalid")
    render = render_video(
        asset_dir=asset_dir,
        timeline=timeline,
        subtitle_path=subtitle_path,
        output_path=output_path,
        transition_seconds=float(config["transition_seconds"]),
        audio_path=audio_path,
        audio_loop=audio_loop,
        subtitle_style=subtitle_style,
        audio_gain=float(config.get("audio_gain", 1.0)),
        audio_normalize=bool(config.get("audio_normalize", False)),
        audio_sample_rate=24000 if audio_mode == "tts" else (48000 if audio_path is not None else None),
    )
    result = {
        "manifest": str(manifest_path),
        "timeline": str(timeline_path),
        "subtitle": str(subtitle_path),
        "captions": len(captions),
        "audio_mode": audio_mode,
        "audio_fallback_reason": audio_fallback_reason,
        "mascot": mascot_contract,
        **render,
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


def _relative_to_root(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _load_director_job_defaults() -> dict[str, Any]:
    path = ROOT / "video_factory" / "configs" / "director_job.defaults.yaml"
    if not path.is_file():
        raise FactoryContractError(
            "director_context_invalid",
            "Director job defaults are unavailable.",
            {"field": "director_job_defaults", "reason": "missing"},
        )
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FactoryContractError(
            "director_context_invalid",
            "Director job defaults are invalid.",
            {"field": "director_job_defaults", "reason": "type"},
        )
    return value


def run_topic(
    topic: str,
    *,
    director: Any | None = None,
    provider_name: str = "codex-cli",
    emit: bool = True,
) -> dict[str, object]:
    """Generate a Storyboard from *topic* and invoke the existing ``run_job``."""

    from src.factory.director import AIDirector, CodexCliDirectorProvider, normalize_topic
    from video_factory.pipeline.validation import validate as _validate_director_report

    normalized = normalize_topic(topic)
    if provider_name != "codex-cli" and director is None:
        raise FactoryContractError(
            "director_provider_unavailable",
            "The requested Director provider is not configured.",
            {"provider": provider_name, "reason": "provider_not_configured"},
        )

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    job_id = f"director_{digest}"
    work_dir = ROOT / "dist" / "director" / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    sandbox = work_dir / ".director_sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    storyboard_path = work_dir / "storyboard.json"
    director_report_path = work_dir / "director_report.json"
    job_path = work_dir / "video_job.yaml"
    output_path = work_dir / "output.mp4"

    if director is None:
        director = AIDirector(
            provider=CodexCliDirectorProvider(working_dir=sandbox),
            repo_root=ROOT,
        )
    try:
        storyboard = director.create_storyboard(normalized)
    except FactoryContractError:
        report = getattr(director, "last_report", None)
        if isinstance(report, dict):
            _validate_director_report(report, "director_run_report")
            write_json(director_report_path, report)
        try:
            sandbox.rmdir()
        except OSError:
            pass
        raise
    try:
        sandbox.rmdir()
    except OSError:
        pass

    write_json(storyboard_path, storyboard)
    report = getattr(director, "last_report", None)
    if not isinstance(report, dict):
        raise FactoryContractError(
            "director_storyboard_invalid",
            "Director did not produce a sanitized run report.",
            {"reason": "report_missing"},
        )
    _validate_director_report(report, "director_run_report")
    write_json(director_report_path, report)

    job = copy.deepcopy(_load_director_job_defaults())
    job.update(
        {
            "schema_version": "1.0",
            "job_id": job_id,
            "job_kind": "video_render",
            "storyboard_ref": "storyboard.json",
            "outputs": {
                "video": _relative_to_root(output_path),
                "work_dir": _relative_to_root(work_dir),
            },
        }
    )
    from video_factory.pipeline.validation import validate as _validate_job

    _validate_job(job, "video_job")
    job_path.write_text(
        yaml.safe_dump(job, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    result = run_job(job_path, emit=False)
    result.update(
        {
            "mode": "topic",
            "job_id": job_id,
            "output": _relative_to_root(output_path),
            "render_report": _relative_to_root(work_dir / "render_report.json"),
            "storyboard": _relative_to_root(storyboard_path),
            "director_report": _relative_to_root(director_report_path),
            "job": _relative_to_root(job_path),
        }
    )
    if emit:
        print(json.dumps(result, ensure_ascii=False))
    return result


# ---------------------------------------------------------------------------
# New --job mode (Phase 1 productization)
# ---------------------------------------------------------------------------

def run_job(job_path: Path, *, emit: bool = True) -> dict[str, object]:
    """Execute a VideoRenderJob from a YAML job definition."""
    job_path = job_path.resolve()

    # --- Load job ---
    if not job_path.is_file():
        raise ValueError("job_missing")
    job = yaml.safe_load(job_path.read_text(encoding="utf-8"))
    if not isinstance(job, dict):
        raise ValueError("job_invalid")

    # --- Validate job against schema ---
    from video_factory.pipeline.validation import validate as _validate_job
    _validate_job(job, "video_job")
    mascot_contract = load_mascot_contract(ROOT, job.get("mascot"))

    # --- Resolve paths ---
    job_dir = job_path.parent
    storyboard_path = (job_dir / str(job["storyboard_ref"])).resolve()
    registry_ref = job.get("registry_ref", "src/factory/assets/pink_pig/registry.json")
    registry_path = (ROOT / registry_ref).resolve()
    render_cfg = job.get("render", {})
    audio_cfg = job.get("audio", {})
    outputs_cfg = job.get("outputs", {})
    output_path = (ROOT / str(outputs_cfg.get("video", "dist/output.mp4"))).resolve()
    work_dir = (ROOT / str(outputs_cfg.get("work_dir", "dist/story_demo"))).resolve()

    # --- Stage B: Registry ---
    from video_factory.pipeline.registry import load_pink_pig_registry
    t0 = time.perf_counter()
    registry = load_pink_pig_registry(repo_root=ROOT)
    t_reg = round(time.perf_counter() - t0, 3)

    # --- Stage C: Storyboard ---
    from video_factory.pipeline.storyboard import (
        load_storyboard as _load_sb,
        validate_storyboard as _validate_sb,
        compile_storyboard as _compile_sb,
    )
    t1 = time.perf_counter()
    sb_doc = _load_sb(storyboard_path)
    _validate_sb(sb_doc)
    write_json(work_dir / "storyboard.resolved.json", sb_doc)
    t_sb = round(time.perf_counter() - t1, 3)

    # --- Stage D: Compile → Timeline ---
    t2 = time.perf_counter()
    tl_doc = _compile_sb(sb_doc, registry, repo_root=ROOT)
    # Post-compile validation
    from video_factory.pipeline.validation import validate as _validate_tl
    _validate_tl(tl_doc, "timeline")
    write_json(work_dir / "timeline.json", tl_doc)
    t_compile = round(time.perf_counter() - t2, 3)

    # --- Stage E: Audio planning ---
    from video_factory.pipeline.audio_planner import plan_audio
    t3 = time.perf_counter()
    audio_plan = plan_audio(
        tl_doc,
        work_dir=work_dir,
        audio_config=audio_cfg,
        repo_root=ROOT,
    )
    t_audio = round(time.perf_counter() - t3, 3)

    # --- Stage F: Subtitles ---
    t4 = time.perf_counter()
    srt_path = work_dir / "subtitle.srt"
    captions = build_srt_from_timeline(tl_doc, srt_path)
    t_sub = round(time.perf_counter() - t4, 3)

    # --- Stage G: Render ---
    t5 = time.perf_counter()
    render_timeline = to_render_timeline(tl_doc)
    transition_sec = float(render_cfg.get("transition_seconds", 0.4))
    render = render_video(
        asset_dir=ROOT,  # asset_dir is now secondary; image_path takes priority
        timeline=render_timeline,
        subtitle_path=srt_path,
        output_path=output_path,
        transition_seconds=transition_sec,
        audio_path=audio_plan.path,
        audio_loop=audio_plan.loop,
        repo_root=ROOT,
        subtitle_style=job.get("subtitle", {}).get("style") if isinstance(job.get("subtitle"), dict) else None,
        audio_gain=float(job.get("audio", {}).get("gain", 1.0)) if isinstance(job.get("audio"), dict) else 1.0,
        audio_sample_rate=24000 if audio_plan.mode == "tts" else (48000 if audio_plan.path else None),
    )
    t_render = round(time.perf_counter() - t5, 3)

    # --- Stage H: Evidence (ffprobe) ---
    t6 = time.perf_counter()
    ffprobe_meta = {}
    if output_path.is_file():
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams",
                 "-of", "json", str(output_path)],
                capture_output=True, text=True, timeout=15,
            )
            fp_data = json.loads(proc.stdout)
            # Extract key metadata
            fmt = fp_data.get("format", {})
            vstreams = [s for s in fp_data.get("streams", []) if s.get("codec_type") == "video"]
            astreams = [s for s in fp_data.get("streams", []) if s.get("codec_type") == "audio"]
            ffprobe_meta = {
                "duration": float(fmt.get("duration", 0)),
                "size": int(fmt.get("size", 0)),
                "format_name": fmt.get("format_name", ""),
                "video": {
                    "codec": vstreams[0]["codec_name"] if vstreams else "",
                    "width": int(vstreams[0]["width"]) if vstreams else 0,
                    "height": int(vstreams[0]["height"]) if vstreams else 0,
                    "fps": vstreams[0].get("r_frame_rate", "") if vstreams else "",
                } if vstreams else {},
                "audio": {
                    "codec": astreams[0]["codec_name"] if astreams else "",
                    "sample_rate": astreams[0].get("sample_rate", "") if astreams else "",
                } if astreams else {},
                "has_audio": len(astreams) > 0,
            }
        except Exception:
            ffprobe_meta = {"error": "ffprobe_failed"}
    t_probe = round(time.perf_counter() - t6, 3)

    render_report = build_render_report(
        ffprobe_meta=ffprobe_meta,
        timeline=tl_doc,
        subtitle_path=srt_path,
        captions_count=len(captions),
    )
    render_report_path = work_dir / "render_report.json"
    write_json(render_report_path, render_report)

    # --- Write run report ---
    run_report = {
        "job_id": job.get("job_id", ""),
        "status": "success",
        "stages": {
            "registry_load": {"seconds": t_reg},
            "storyboard_validate": {"seconds": t_sb},
            "compile": {"seconds": t_compile},
            "audio_plan": {"seconds": t_audio},
            "subtitle": {"seconds": t_sub},
            "render": {"seconds": t_render},
            "evidence": {"seconds": t_probe},
        },
        "audio_plan": {
            "mode": audio_plan.mode,
            "loop": audio_plan.loop,
            "fallback_reason": audio_plan.fallback_reason,
            "path": str(audio_plan.path) if audio_plan.path else None,
            "segments_count": len(audio_plan.segments),
        },
        "mascot": mascot_contract,
        "ffprobe": ffprobe_meta,
        "render_report": "render_report.json",
        "output": str(output_path),
        "renderer": render,
        "captions_count": len(captions),
    }
    write_json(work_dir / "run_report.json", run_report)

    result = {
        "mode": "job",
        "job_id": job.get("job_id", ""),
        "output": str(output_path),
        "captions": len(captions),
        "audio_mode": audio_plan.mode,
        "audio_fallback_reason": audio_plan.fallback_reason,
        "mascot": mascot_contract,
        "render_report": str(render_report_path),
        **render,
    }
    if emit:
        print(json.dumps(result, ensure_ascii=False))
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Pink Pig Video Factory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--config", type=Path, default=None, help="Legacy config YAML path")
    group.add_argument("--job", type=Path, default=None, help="Phase 1 job YAML path")
    group.add_argument("--topic", type=str, default=None, help="Generate a storyboard from a topic")
    parser.add_argument(
        "--director-provider",
        choices=["codex-cli"],
        default="codex-cli",
        help="Provider used with --topic",
    )
    args = parser.parse_args()

    # Default to legacy --config if neither specified
    if args.config is None and args.job is None and args.topic is None:
        args.config = ROOT / "examples" / "pink_pig_demo" / "config.yaml"

    try:
        if args.topic is not None:
            return 0 if run_topic(args.topic, provider_name=args.director_provider) else 0
        if args.job is not None:
            return 0 if run_job(args.job) else 0
        else:
            run(args.config)
            return 0
    except FactoryContractError as exc:
        print(json.dumps({"status": "error", "error": exc.to_dict()}, ensure_ascii=False))
        return 2
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
