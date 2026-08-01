"""Sequential offline candidate pipeline. It owns no production scheduling or messaging."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .captions import build_captions, write_srt
from .config import PROJECT_ROOT, jobs_root, state_root
from .db import CandidateStore
from .delivery import record_dry_run_delivery
from .fixtures import fixture_content
from .mascot import create_contact_sheet
from .metrics import RunMetrics
from .quality import quality_report
from .render import (
    build_legacy_render_input,
    build_render_input,
    encode_video,
    render_raw,
    resolve_duration_seconds,
    stage_audio,
    wav_duration_seconds,
    write_render_input,
)
from .state import next_state
from .tts import CandidateTts


def _write_json(path: Path, value: dict[str, Any] | list[Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(
    store: CandidateStore, job_id: str, package: Path, name: str, kind: str | None = None
) -> None:
    path = package / name
    store.record_artifact(
        job_id, kind or name, path.relative_to(PROJECT_ROOT).as_posix(), _sha256(path)
    )


def _cover(source: Path, target: Path) -> None:
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            "0.5",
            "-i",
            str(source),
            "-frames:v",
            "1",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not target.exists():
        raise RuntimeError("cover_generation_failed")


def _cleanup_transient(job_id: str, package: Path) -> None:
    (package / "render_raw.mp4").unlink(missing_ok=True)
    runtime = PROJECT_ROOT / "remotion" / "public" / "runtime" / job_id
    if runtime.exists():
        shutil.rmtree(runtime)


def _cleanup_cancelled_render(package: Path) -> None:
    for name in (
        "render_raw.mp4",
        "final_master.mp4",
        "feishu_preview.mp4",
        "cover.png",
        "render_manifest.json",
    ):
        (package / name).unlink(missing_ok=True)


def cancel_job(store: CandidateStore, job_id: str) -> dict[str, Any]:
    """Cancel an offline candidate and remove only incomplete render outputs."""
    current = store.status(job_id)
    package = jobs_root() / job_id
    cancelled = store.cancel(job_id, "operator_requested")
    if current["state"] == "RENDERING":
        _cleanup_cancelled_render(package)
    _cleanup_transient(job_id, package)
    metrics_path = package / "run_metrics.json"
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics["cancellation_count"] = int(metrics.get("cancellation_count", 0)) + 1
        _write_json(metrics_path, metrics)
    return cancelled


def _run_stage(
    store: CandidateStore,
    job: dict[str, Any],
    package: Path,
    encoder: str,
    tts_provider: str,
    render_concurrency: int,
    metrics: RunMetrics,
) -> dict[str, Any]:
    stage = job["state"]
    content = fixture_content(job["fixture_id"])
    if stage == "RESEARCHING":
        sources = [
            {
                "kind": "synthetic_fixture",
                "source": f"repository fixture:{job['fixture_id']}",
                "content_sha256": hashlib.sha256(job["fixture_id"].encode()).hexdigest(),
            }
        ]
        _write_json(package / "sources.json", sources)
        (package / "research.md").write_text(
            "# 离线合成 Fixture\n\n本候选只使用仓库控制的演示稿；不执行网络研究。\n",
            encoding="utf-8",
        )
        _artifact(store, job["job_id"], package, "sources.json")
        return {"sources": len(sources)}
    if stage == "SCRIPTING":
        script = {
            "schema_version": "1.0",
            "job_id": job["job_id"],
            "topic": job["topic"],
            "narration": content["narration"],
            "source_mode": "synthetic_fixture",
        }
        storyboard = {
            "schema_version": job["render_contract_version"],
            "job_id": job["job_id"],
            "template": job["template"],
            "scenes": content["scenes"],
            "requested_duration_seconds": job["requested_duration_seconds"] or 10,
        }
        _write_json(package / "script.json", script)
        _write_json(package / "storyboard.json", storyboard)
        _artifact(store, job["job_id"], package, "script.json")
        _artifact(store, job["job_id"], package, "storyboard.json")
        return {"scenes": len(content["scenes"])}
    if stage == "VOICE":
        manifest = CandidateTts(state_root() / "tts_cache").synthesize(
            str(content["narration"]), package / "voice.wav", provider=tts_provider
        )
        _write_json(package / "voice_manifest.json", manifest)
        _write_json(package / "audio_quality.json", manifest["audio_quality"])
        resolved_duration = None
        if job["render_contract_version"] == "2.0":
            resolved_duration = resolve_duration_seconds(
                package / "voice.wav", int(job["requested_duration_seconds"])
            )
            store.set_resolved_duration(job["job_id"], resolved_duration)
        _artifact(store, job["job_id"], package, "voice.wav")
        _artifact(store, job["job_id"], package, "voice_manifest.json")
        _artifact(store, job["job_id"], package, "audio_quality.json")
        return {
            "provider": manifest["provider"],
            "provider_fallback": manifest["provider_fallback"],
            "resolved_duration_seconds": resolved_duration,
        }
    if stage == "CAPTIONS":
        caption_duration = float(job["resolved_duration_seconds"] or 10)
        voice_manifest = json.loads((package / "voice_manifest.json").read_text(encoding="utf-8"))
        captions = build_captions(
            str(content["narration"]),
            duration_seconds=caption_duration,
            boundaries=voice_manifest.get("boundaries"),
        )
        _write_json(package / "captions.json", {"schema_version": "1.0", "items": captions})
        write_srt(captions, package / "captions.srt")
        _artifact(store, job["job_id"], package, "captions.json")
        _artifact(store, job["job_id"], package, "captions.srt")
        return {"captions": len(captions)}
    if stage == "ASSETS":
        create_contact_sheet(package / "mascot-contact-sheet.png")
        _artifact(store, job["job_id"], package, "mascot-contact-sheet.png")
        return {"mascot_pose": content["mascot_pose"]}
    if stage == "RENDERING":
        captions = json.loads((package / "captions.json").read_text(encoding="utf-8"))["items"]
        audio_asset = stage_audio(job["job_id"], package / "voice.wav")
        common_render_input = {
            "job_id": job["job_id"],
            "template": job["template"],
            "title": job["topic"],
            "scenes": content["scenes"],
            "captions": captions,
            "mascot_pose": str(content["mascot_pose"]),
            "audio_asset": audio_asset,
        }
        payload = (
            build_legacy_render_input(**common_render_input)
            if job["render_contract_version"] == "1.0"
            else build_render_input(
                **common_render_input,
                requested_duration_seconds=int(job["requested_duration_seconds"]),
                resolved_duration_seconds=float(job["resolved_duration_seconds"]),
                audio_duration_seconds=wav_duration_seconds(package / "voice.wav"),
            )
        )
        write_render_input(package / "render_input.json", payload)
        render_detail = render_raw(
            package / "render_input.json", package / "render_raw.mp4", concurrency=render_concurrency
        )
        metrics.render_observed(render_detail["metrics"])
        master = encode_video(package / "render_raw.mp4", package / "final_master.mp4", encoder)
        selected = "nvenc" if master["encoder"] == "h264_nvenc" else "cpu"
        preview = encode_video(
            package / "render_raw.mp4", package / "feishu_preview.mp4", selected, preview=True
        )
        _cover(package / "final_master.mp4", package / "cover.png")
        _write_json(package / "render_manifest.json", {
            "schema_version": job["render_contract_version"],
            "renderer": render_detail["renderer"],
            "composition": "P1Candidate",
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "frames": round(float(job["resolved_duration_seconds"] or 10) * 30),
            "requested_duration_seconds": job["requested_duration_seconds"],
            "resolved_duration_seconds": job["resolved_duration_seconds"],
            "master": master,
            "preview": preview,
            "metrics": render_detail["metrics"],
            "browser": "local_chrome",
            "network_called": False,
        })
        for name in ("render_input.json", "render_manifest.json", "final_master.mp4", "feishu_preview.mp4", "cover.png"):
            _artifact(store, job["job_id"], package, name)
        _cleanup_transient(job["job_id"], package)
        return {"master_encoder": master["encoder"], "preview_encoder": preview["encoder"]}
    if stage == "QUALITY_CHECK":
        captions = json.loads((package / "captions.json").read_text(encoding="utf-8"))["items"]
        report = quality_report(package, captions, float(job["resolved_duration_seconds"] or 10))
        _write_json(package / "quality_report.json", report)
        if report["status"] != "pass":
            raise RuntimeError("quality_gate_failed")
        (package / "publish_info.md").write_text(
            "# Offline Candidate\n\n仅供人工审核；没有发送飞书或发布。\n", encoding="utf-8"
        )
        record_dry_run_delivery(store, job["job_id"], package)
        for name in ("quality_report.json", "publish_info.md", "delivery_manifest.json"):
            _artifact(store, job["job_id"], package, name)
        return {"quality": "pass", "delivery": "dry-run"}
    raise RuntimeError(f"unsupported_stage:{stage}")


def run_job(
    store: CandidateStore,
    job_id: str,
    encoder: str,
    tts_provider: str,
    *,
    render_concurrency: int = 1,
) -> dict[str, Any]:
    package = jobs_root() / job_id
    package.mkdir(parents=True, exist_ok=True)
    active_stage: str | None = None
    active_attempt: int | None = None
    metrics: RunMetrics | None = None
    try:
        job = store.status(job_id)
        if job["state"] == "PENDING_REVIEW":
            return {"status": "already_completed", "job": job}
        if job["state"] in {"CANCELLED", "FAILED"}:
            raise RuntimeError(f"job_not_runnable:{job['state']}")
        metrics = RunMetrics(job_id, package / "run_metrics.json", int(job["attempt"]))
        if job["state"] != "NEW":
            metrics.record_recovery()
        _write_json(
            package / "job.json",
            {
                "schema_version": "1.0",
                "job_id": job_id,
                "fixture_id": job["fixture_id"],
                "offline_candidate": True,
            },
        )
        if job["state"] == "NEW":
            job = store.advance(job_id, "RESEARCHING", "candidate_run_started")
        while job["state"] != "PENDING_REVIEW":
            active_stage = job["state"]
            active_attempt = store.start_stage_attempt(job_id, active_stage)
            metrics.stage_started(active_stage, active_attempt)
            detail = _run_stage(
                store, job, package, encoder, tts_provider, render_concurrency, metrics
            )
            store.complete_stage_attempt(job_id, active_stage, active_attempt, "completed", detail)
            metrics.stage_completed(active_stage, status="completed", detail=detail)
            completed_stage = active_stage
            active_stage = None
            active_attempt = None
            job = store.advance(job_id, next_state(job["state"]) or "PENDING_REVIEW")
            if os.environ.get("P1_CANDIDATE_INTERRUPT_AFTER") == completed_stage:
                return {"status": "interrupted_for_recovery_test", "job": store.status(job_id)}
        _write_json(
            package / "job.json",
            {
                "schema_version": "1.0",
                "job_id": job_id,
                "fixture_id": job["fixture_id"],
                "offline_candidate": True,
                "state": job["state"],
            },
        )
        _artifact(store, job_id, package, "job.json")
        _artifact(store, job_id, package, "run_metrics.json")
        return {"status": "completed", "job": job, "package": str(package)}
    except Exception as exc:
        if active_stage is not None and active_attempt is not None:
            try:
                store.complete_stage_attempt(
                    job_id,
                    active_stage,
                    active_attempt,
                    "failed",
                    {"error": str(exc)},
                )
            except ValueError:
                pass
        if metrics is not None and active_stage is not None:
            metrics.stage_completed(active_stage, status="failed", detail={})
        current = store.status(job_id)
        if current["state"] not in {"CANCELLED", "FAILED", "PENDING_REVIEW"}:
            store.fail(job_id, "candidate_stage_failed")
        _cleanup_transient(job_id, package)
        raise
