"""Conservative local reference-video ingest, analysis, and originality evidence.

The module deliberately keeps the reference media in the ignored runtime area.
Only abstract timing/style metadata and provenance contracts enter the review
package.  It never invokes a provider and never creates a rendering pipeline.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from .config import PROJECT_ROOT
from src.factory.director.context import normalize_topic


POLICY_VERSION = "reference-analysis-v1"
MAX_BYTES = 1 << 30
MAX_DURATION_SECONDS = 180.0
REFERENCE_STORAGE_ROOT = PROJECT_ROOT / "input" / "reference_videos"
REFERENCE_RUNTIME_ROOT = PROJECT_ROOT / "state" / "phase1_local" / "reference_jobs"
_FORBIDDEN_BRIEF_KEYS = frozenset(
    {"path", "source_path", "frame_path", "audio_path", "transcript", "asset_id", "render", "provider", "provider_prompt"}
)


def _fail(code: str, message: str, **context: object) -> FactoryContractError:
    return FactoryContractError(code, message, context)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = int(getattr(path.lstat(), "st_file_attributes", 0))
    except OSError:
        return True
    return bool(attributes & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def _assert_source_file(path: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        # ``resolve()`` would dereference a symlink before the reparse check.
        candidate = (Path.cwd() / candidate).absolute()
    if candidate.suffix.lower() != ".mp4":
        raise _fail("reference_video_extension_invalid", "Only local MP4 references are accepted.", field="video")
    if _is_reparse(candidate):
        raise _fail("reference_video_reparse_rejected", "Reference source links and reparse points are rejected.", field="video")
    try:
        info = candidate.stat()
    except OSError as exc:
        raise _fail("reference_video_missing", "Reference source is unavailable.", field="video") from exc
    if not candidate.is_file() or info.st_size <= 0:
        raise _fail("reference_video_empty", "Reference source must be a non-empty regular file.", field="video")
    if info.st_size > MAX_BYTES:
        raise _fail("reference_video_too_large", "Reference source exceeds the 1 GiB limit.", field="video")
    return candidate


def _run_ffprobe(path: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _fail("reference_ffprobe_unavailable", "ffprobe could not inspect the reference.", field="ffprobe") from exc
    if completed.returncode != 0:
        raise _fail("reference_video_invalid", "The reference is not a readable MP4 container.", field="video")
    try:
        value = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise _fail("reference_video_invalid", "ffprobe returned invalid media metadata.", field="ffprobe") from exc
    if not isinstance(value, dict):
        raise _fail("reference_video_invalid", "ffprobe metadata is not an object.", field="ffprobe")
    streams = value.get("streams")
    fmt = value.get("format")
    if not isinstance(streams, list) or not isinstance(fmt, dict):
        raise _fail("reference_video_invalid", "The reference does not contain a valid media description.", field="ffprobe")
    video = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"), None)
    if not isinstance(video, dict):
        raise _fail("reference_video_invalid", "The reference does not contain a video stream.", field="video")
    try:
        duration = float(fmt.get("duration", 0))
        width = int(video.get("width", 0))
        height = int(video.get("height", 0))
    except (TypeError, ValueError) as exc:
        raise _fail("reference_video_invalid", "The reference media dimensions are invalid.", field="video") from exc
    format_names = {part.strip().lower() for part in str(fmt.get("format_name", "")).split(",")}
    if "mp4" not in format_names and "mov" not in format_names:
        raise _fail("reference_video_invalid", "The reference is not an MP4-compatible container.", field="format")
    if duration <= 0 or duration > MAX_DURATION_SECONDS:
        raise _fail("reference_video_duration_invalid", "Reference duration must be between 0 and 180 seconds.", field="duration_seconds")
    if width <= 0 or height <= 0:
        raise _fail("reference_video_invalid", "Reference resolution is invalid.", field="resolution")
    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "has_audio": any(isinstance(item, dict) and item.get("codec_type") == "audio" for item in streams),
        "fps": _fraction(video.get("r_frame_rate", "0/1")),
    }


def _fraction(value: object) -> float:
    numerator, separator, denominator = str(value).partition("/")
    if not separator:
        return float(numerator or 0)
    divisor = float(denominator or 0)
    return float(numerator or 0) / divisor if divisor else 0.0


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_object(path: Path, schema: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _fail("reference_contract_invalid", "Reference evidence is missing or invalid.", field=path.name) from exc
    if not isinstance(value, dict):
        raise _fail("reference_contract_invalid", "Reference evidence must be an object.", field=path.name)
    if schema:
        validate(value, schema)
    return value


def _validate_rights(rights: dict[str, Any], source_sha256: str) -> dict[str, Any]:
    validate(rights, "reference_rights")
    if rights.get("source_sha256") != source_sha256:
        raise _fail("reference_rights_sha_mismatch", "Rights evidence does not match the source SHA-256.", field="source_sha256")
    return dict(rights)


def ingest_reference(video_path: Path, rights_path: Path) -> dict[str, Any]:
    """Validate and copy one local MP4 into a private, read-only store."""

    source = _assert_source_file(video_path)
    rights = _read_object(Path(rights_path), "reference_rights")
    before = source.stat()
    source_sha = _sha256(source)
    metadata = _run_ffprobe(source)
    after_probe = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after_probe.st_size, after_probe.st_mtime_ns) or _sha256(source) != source_sha:
        raise _fail("reference_source_changed", "Reference source changed during validation.", field="video")
    rights = _validate_rights(rights, source_sha)

    REFERENCE_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    stored = REFERENCE_STORAGE_ROOT / f"{source_sha}.mp4"
    if stored.exists():
        if _is_reparse(stored) or not stored.is_file() or _sha256(stored) != source_sha:
            raise _fail("reference_storage_collision", "Reference storage already contains different content.", field="stored_path")
    else:
        temp = REFERENCE_STORAGE_ROOT / f".{source_sha}.tmp"
        if temp.exists():
            if _is_reparse(temp):
                raise _fail("reference_storage_collision", "Reference temporary storage is a reparse point.", field="stored_path")
            temp.unlink()
        try:
            shutil.copyfile(source, temp)
            if _sha256(source) != source_sha:
                temp.unlink(missing_ok=True)
                raise _fail("reference_source_changed", "Reference source changed during copy.", field="video")
            if _sha256(temp) != source_sha:
                temp.unlink(missing_ok=True)
                raise _fail("reference_copy_hash_mismatch", "Reference copy hash does not match the source.", field="stored_path")
            temp.replace(stored)
        except FactoryContractError:
            raise
        except OSError as exc:
            temp.unlink(missing_ok=True)
            raise _fail("reference_copy_failed", "Reference could not be copied to private storage.", field="stored_path") from exc
    try:
        os.chmod(stored, stat.S_IREAD)
    except OSError as exc:
        raise _fail("reference_readonly_failed", "Reference private copy could not be made read-only.", field="stored_path") from exc
    if _sha256(source) != source_sha:
        raise _fail("reference_source_changed", "Reference source changed during ingest.", field="video")

    reference_id = f"ref_{source_sha[:24]}"
    receipt = {
        "schema_version": "1.0",
        "reference_id": reference_id,
        "source_mode": "owned_or_licensed_local_video",
        "source_name": source.name,
        "source_sha256": source_sha,
        "stored_path": stored.relative_to(PROJECT_ROOT).as_posix(),
        "stored_sha256": _sha256(stored),
        "bytes": int(stored.stat().st_size),
        "duration_seconds": round(float(metadata["duration_seconds"]), 3),
        "resolution": {"width": int(metadata["width"]), "height": int(metadata["height"])},
        "has_audio": bool(metadata["has_audio"]),
        "processing_timestamp": _now(),
        "analyzer_policy_version": POLICY_VERSION,
    }
    validate(receipt, "reference_receipt")
    runtime = REFERENCE_RUNTIME_ROOT / reference_id
    runtime.mkdir(parents=True, exist_ok=True)
    _write_json(runtime / "reference_receipt.json", receipt)
    _write_json(runtime / "reference_rights.json", rights)
    return {
        "reference_id": reference_id,
        "source_sha256": source_sha,
        "stored_path": stored,
        "runtime_root": runtime,
        "receipt": receipt,
        "rights": rights,
    }


def _scene_boundaries(path: Path, duration: float, fps: float) -> list[tuple[float, float]]:
    try:
        from scenedetect import SceneManager, open_video
        from scenedetect.detectors import ContentDetector
    except ImportError as exc:
        sidecar_python = PROJECT_ROOT / ".venv-reference-analysis" / "Scripts" / "python.exe"
        sidecar = PROJECT_ROOT / "scripts" / "reference_scene_detect.py"
        if not sidecar_python.is_file() or not sidecar.is_file():
            raise _fail("reference_scene_detector_unavailable", "PySceneDetect 0.7.1 is not available in the reference-analysis environment.", field="scenedetect") from exc
        try:
            completed = subprocess.run(
                [str(sidecar_python), str(sidecar), "--video", str(path), "--duration", str(duration), "--fps", str(fps)],
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            if completed.returncode != 0:
                raise ValueError("sidecar_exit")
            sidecar_value = json.loads(completed.stdout)
            return [(round(float(item[0]), 3), round(float(item[1]), 3)) for item in sidecar_value["scenes"]]
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError, json.JSONDecodeError) as sidecar_exc:
            raise _fail("reference_scene_analysis_failed", "PySceneDetect sidecar could not analyze the reference.", field="scenes") from sidecar_exc
    try:
        video = open_video(str(path))
        manager = SceneManager()
        manager.add_detector(ContentDetector(threshold=27.0, min_scene_len=max(1, int(round(fps * 0.8)))))
        manager.detect_scenes(video=video)
        detected = manager.get_scene_list()
    except Exception as exc:
        raise _fail("reference_scene_analysis_failed", "PySceneDetect could not analyze the reference.", field="scenes") from exc
    if not detected:
        return [(0.0, round(duration, 3))]
    scenes: list[tuple[float, float]] = []
    for start, end in detected:
        begin = max(0.0, float(start.get_seconds()))
        finish = min(duration, float(end.get_seconds()))
        if finish > begin:
            scenes.append((round(begin, 3), round(finish, 3)))
    if not scenes:
        return [(0.0, round(duration, 3))]
    # PySceneDetect can omit a tail frame at EOF; preserve the full duration.
    if scenes[-1][1] < duration - 0.05:
        scenes[-1] = (scenes[-1][0], round(duration, 3))
    return scenes


def _cached_whisper_model() -> Path | None:
    configured = os.environ.get("REFERENCE_WHISPER_MODEL_PATH", "").strip()
    candidates: list[Path] = [Path(configured)] if configured else []
    home = Path.home()
    candidates.extend((home / ".cache" / "huggingface" / "hub" / "models--Systran--faster-whisper-small" / "snapshots").glob("*"))
    for candidate in candidates:
        if candidate.is_dir() and all((candidate / name).is_file() for name in ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")):
            return candidate.resolve()
    return None


def _transcribe(path: Path, has_audio: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not has_audio:
        return ({"status": "unavailable", "model": None, "reason": "no_audio_track"}, [])
    model_path = _cached_whisper_model()
    if model_path is None:
        return ({"status": "unavailable", "model": None, "reason": "cached_small_model_missing"}, [])
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sidecar_python = PROJECT_ROOT / ".venv-reference-analysis" / "Scripts" / "python.exe"
        sidecar = PROJECT_ROOT / "scripts" / "reference_transcribe.py"
        if not sidecar_python.is_file() or not sidecar.is_file():
            return ({"status": "unavailable", "model": None, "reason": "faster_whisper_unavailable"}, [])
        try:
            environment = dict(os.environ)
            environment.update({"HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
            completed = subprocess.run(
                [str(sidecar_python), str(sidecar), "--video", str(path), "--model", str(model_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
                env=environment,
            )
            if completed.returncode != 0:
                raise ValueError("sidecar_exit")
            sidecar_value = json.loads(completed.stdout)
            segments = sidecar_value.get("segments", [])
            if not isinstance(segments, list):
                raise ValueError("segments")
            return ({"status": "available", "model": "faster-whisper-small@local-cache", "reason": None}, segments)
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return ({"status": "unavailable", "model": "faster-whisper-small@local-cache", "reason": "local_transcription_failed"}, [])
    old_env = {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "HF_DATASETS_OFFLINE", "TRANSFORMERS_OFFLINE")}
    os.environ.update({"HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    try:
        model = WhisperModel(str(model_path), device="cpu", compute_type="int8")
        segments, _info = model.transcribe(str(path), beam_size=5, vad_filter=True)
        transcript = []
        for segment in segments:
            text = str(getattr(segment, "text", "")).strip()
            if text:
                transcript.append({"start_seconds": round(float(segment.start), 3), "end_seconds": round(float(segment.end), 3), "text": text, "speaker": None})
        # Do not publish the local cache path into a review package.
        return ({"status": "available", "model": "faster-whisper-small@local-cache", "reason": None}, transcript)
    except Exception:
        return ({"status": "unavailable", "model": "faster-whisper-small@local-cache", "reason": "local_transcription_failed"}, [])
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def analyze_reference(bundle: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic local scene analysis and optional offline ASR."""

    receipt = dict(bundle["receipt"])
    path = Path(bundle["stored_path"])
    metadata = _run_ffprobe(path)
    scenes = _scene_boundaries(path, float(metadata["duration_seconds"]), float(metadata["fps"]))
    durations = [round(end - start, 3) for start, end in scenes]
    median_duration = float(median(durations))
    pace = "fast" if median_duration < 2.5 else "medium" if median_duration <= 6.0 else "slow"
    asr, transcript = _transcribe(path, bool(metadata["has_audio"]))
    report = {
        "schema_version": "1.0",
        "reference_id": receipt["reference_id"],
        "source_sha256": receipt["source_sha256"],
        "duration_seconds": round(float(metadata["duration_seconds"]), 3),
        "resolution": {"width": int(metadata["width"]), "height": int(metadata["height"])},
        "scenes": [
            {
                "scene_id": f"s{index:02d}",
                "start_seconds": start,
                "end_seconds": end,
                "duration_seconds": duration,
                "representative_frame_time_seconds": round(start + duration / 2, 3),
                "visual_description": "local_visual_analysis_unavailable",
                "caption_summary": "not_extracted_in_conservative_mode",
                "audio_summary": "audio_present" if metadata["has_audio"] else "no_audio_track",
            }
            for index, ((start, end), duration) in enumerate(zip(scenes, durations), start=1)
        ],
        "style_fingerprint": {
            "pace": pace,
            "shot_density_per_second": round(len(scenes) / float(metadata["duration_seconds"]), 6),
            "median_shot_duration_seconds": round(median_duration, 3),
            "scene_count": len(scenes),
            "structure_summary": "single_scene" if len(scenes) == 1 else "multi_scene",
        },
        "transcript": transcript,
        "asr": asr,
    }
    validate(report, "reference_report")
    _write_json(Path(bundle["runtime_root"]) / "reference_report.json", report)
    return report


def _scene_count_band(count: int) -> str:
    return "1" if count == 1 else "2-4" if count <= 4 else "5-8" if count <= 8 else "9+"


def _contains_forbidden_brief_reference(value: object) -> bool:
    """Reject source paths/control fields even when nested in factual input."""

    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_BRIEF_KEYS:
                return True
            if _contains_forbidden_brief_reference(item):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_forbidden_brief_reference(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.replace("\\", "/").lower()
    if normalized.startswith(("file://", "//", "/")):
        return True
    if len(normalized) >= 3 and normalized[1:3] == ":/" and normalized[0].isalpha():
        return True
    return any(marker in normalized for marker in ("input/reference_videos", "state/phase1_local/reference_jobs"))


def _user_brief(value: dict[str, Any]) -> tuple[str, dict[str, Any], str | None]:
    if _contains_forbidden_brief_reference(value):
        raise _fail("original_brief_invalid", "Original brief input contains a forbidden source or renderer field.", field="brief")
    topic = normalize_topic(value.get("topic")) if isinstance(value.get("topic"), str) else ""
    factual = value.get("factual_brief")
    if not topic or not isinstance(factual, dict):
        raise _fail("original_brief_invalid", "Reference reconstruction requires a topic and verified factual brief.", field="brief")
    validate(factual, "director_factual_brief")
    if factual.get("review_status") != "verified":
        raise _fail("original_brief_invalid", "Reference reconstruction requires a verified factual brief.", field="factual_brief.review_status")
    expected = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    if factual.get("topic_digest") != expected:
        raise _fail("original_brief_invalid", "Factual brief topic digest does not match the original topic.", field="factual_brief.topic_digest")
    return topic, factual, str(value.get("title")) if value.get("title") else None


def build_original_brief(user_value: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    topic, factual, title = _user_brief(user_value)
    style = report["style_fingerprint"]
    pace = str(style["pace"])
    target = 30 if pace == "fast" else 50 if pace == "slow" else 40
    original = {
        "schema_version": "1.0",
        "input_mode": "local_reference",
        **({"title": title} if title else {}),
        "topic": topic,
        "factual_brief": factual,
        "reference_sha256": report["source_sha256"],
        "reference_abstraction": {
            "pace": pace,
            "scene_count_band": _scene_count_band(int(style["scene_count"])),
            "median_shot_duration_seconds": float(style["median_shot_duration_seconds"]),
            "shot_density_per_second": float(style["shot_density_per_second"]),
            "structure": ["hook", "explain", "evidence", "repair", "summary"],
            "duration_target_seconds": target,
        },
    }
    validate(original, "original_brief")
    return original


def brief_digest(brief: dict[str, Any]) -> str:
    encoded = json.dumps(brief, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_reference_job_key(reference_sha256: str, brief: dict[str, Any]) -> str:
    return f"phase1-reference:{reference_sha256}:{brief_digest(brief)}:{POLICY_VERSION}"


def write_original_brief(bundle: dict[str, Any], brief: dict[str, Any]) -> Path:
    target = Path(bundle["runtime_root"]) / "original_brief.json"
    _write_json(target, brief)
    return target


def materialize_review_evidence(runtime_root: Path, work_dir: Path) -> None:
    for name, schema in (
        ("reference_receipt.json", "reference_receipt"),
        ("reference_rights.json", "reference_rights"),
        ("reference_report.json", "reference_report"),
        ("original_brief.json", "original_brief"),
    ):
        value = _read_object(Path(runtime_root) / name, schema)
        _write_json(Path(work_dir) / name, value)


def load_reference_bundle(runtime_root: Path, *, expected_source_sha256: str | None = None) -> dict[str, Any]:
    """Load and re-check the immutable evidence bundle before rendering."""

    root = Path(runtime_root).resolve()
    allowed = REFERENCE_RUNTIME_ROOT.resolve()
    if root == allowed or allowed not in root.parents or root.is_symlink():
        raise _fail("reference_runtime_path_invalid", "Reference runtime evidence is outside the owned directory.", field="runtime_root")
    receipt = _read_object(root / "reference_receipt.json", "reference_receipt")
    rights = _read_object(root / "reference_rights.json", "reference_rights")
    report = _read_object(root / "reference_report.json", "reference_report")
    brief = _read_object(root / "original_brief.json", "original_brief")
    if expected_source_sha256 and receipt.get("source_sha256") != expected_source_sha256:
        raise _fail("reference_runtime_hash_mismatch", "Reference receipt does not match job metadata.", field="source_sha256")
    if rights.get("source_sha256") != receipt.get("source_sha256") or report.get("source_sha256") != receipt.get("source_sha256") or brief.get("reference_sha256") != receipt.get("source_sha256"):
        raise _fail("reference_runtime_hash_mismatch", "Reference evidence documents do not share one source SHA-256.", field="source_sha256")
    stored = (PROJECT_ROOT / str(receipt["stored_path"])).resolve()
    storage_root = REFERENCE_STORAGE_ROOT.resolve()
    if stored == storage_root or storage_root not in stored.parents or stored.is_symlink() or not stored.is_file():
        raise _fail("reference_storage_path_invalid", "Reference private storage path is invalid.", field="stored_path")
    if _sha256(stored) != receipt["stored_sha256"] or _sha256(stored) != receipt["source_sha256"]:
        raise _fail("reference_storage_hash_mismatch", "Reference private storage hash is not immutable.", field="stored_sha256")
    return {"runtime_root": root, "stored_path": stored, "receipt": receipt, "rights": rights, "report": report, "original_brief": brief}


def _walk_strings(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def _asset_registry_ids() -> set[str]:
    try:
        registry = json.loads((PROJECT_ROOT / "src/factory/assets/pink_pig/registry.json").read_text(encoding="utf-8"))
        return {str(item["asset_id"]) for item in registry.get("assets", []) if isinstance(item, dict) and item.get("asset_id")}
    except (OSError, ValueError, TypeError):
        return set()


def _asset_registry_map() -> dict[str, str]:
    try:
        registry = json.loads((PROJECT_ROOT / "src/factory/assets/pink_pig/registry.json").read_text(encoding="utf-8"))
        return {
            str(item["asset_id"]): str(item.get("path", ""))
            for item in registry.get("assets", [])
            if isinstance(item, dict) and item.get("asset_id")
        }
    except (OSError, ValueError, TypeError):
        return {}


def _text_similarity(report: dict[str, Any], work_dir: Path) -> dict[str, Any]:
    asr = report.get("asr")
    transcript = report.get("transcript")
    if not isinstance(asr, dict) or asr.get("status") != "available" or not isinstance(transcript, list):
        return {"status": "unavailable", "score": None, "threshold": 0.3, "method": "unavailable"}
    source_text = "".join(str(item.get("text", "")) for item in transcript if isinstance(item, dict))
    try:
        script_doc = json.loads((work_dir / "script.json").read_text(encoding="utf-8"))
        generated = str(script_doc.get("narration", ""))
    except (OSError, ValueError, TypeError):
        return {"status": "blocked", "score": None, "threshold": 0.3, "method": "unavailable"}
    score = difflib.SequenceMatcher(None, source_text, generated).ratio() if source_text else 0.0
    return {"status": "passed" if score <= 0.3 else "blocked", "score": round(score, 6), "threshold": 0.3, "method": "sequence_matcher"}


def build_difference_report(*, bundle: dict[str, Any], work_dir: Path, output_path: Path, asset_selection: dict[str, Any]) -> dict[str, Any]:
    receipt = dict(bundle["receipt"])
    report = _read_object(Path(bundle["runtime_root"]) / "reference_report.json", "reference_report")
    output_sha = _sha256(output_path)
    text_values: list[str] = []
    for name in (
        "render_job.yaml",
        "asset_selection_report.json",
        "storyboard.json",
        "timeline.json",
        "run_report.json",
        "render_manifest.json",
        "audio_manifest.json",
        "quality_report.json",
        "script.json",
        "video_job_state.json",
    ):
        path = Path(work_dir) / name
        if path.is_file():
            try:
                text_values.append(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError):
                pass
    joined = "\n".join(text_values)
    normalized_joined = joined.replace("\\", "/").lower()
    source_markers = (
        "input/reference_videos",
        "state/phase1_local/reference_jobs",
        str(receipt["source_sha256"]).lower(),
        str(receipt.get("source_name", "")).lower(),
        "reference_audio",
    )
    reference_path_absent = "blocked" if any(marker and marker in normalized_joined for marker in source_markers) else "passed"
    registry_map = _asset_registry_map()
    selections = asset_selection.get("selections") if isinstance(asset_selection, dict) else None
    registry_assets_only = "passed"
    if not registry_map or not isinstance(selections, list) or not selections:
        registry_assets_only = "blocked"
    else:
        for selection in selections:
            if not isinstance(selection, dict):
                registry_assets_only = "blocked"
                break
            asset_id = str(selection.get("asset_id", ""))
            relative_path = str(selection.get("relative_path", ""))
            if asset_id not in registry_map or registry_map[asset_id] != relative_path:
                registry_assets_only = "blocked"
                break
    try:
        render_job = yaml_like_json(work_dir / "render_job.yaml")
    except Exception:
        render_job = {}
    audio_provider = ""
    if isinstance(render_job.get("audio"), dict) and isinstance(render_job["audio"].get("tts"), dict):
        audio_provider = str(render_job["audio"]["tts"].get("provider", ""))
    local_sapi = "passed" if audio_provider == "windows-sapi" and "input/reference_videos" not in normalized_joined else "blocked"
    source_audio_absent = "passed" if str(receipt.get("source_name", "")).lower() not in normalized_joined and "reference_audio" not in normalized_joined else "blocked"
    text_check = _text_similarity(report, Path(work_dir))
    automatic = [output_sha != receipt["source_sha256"], reference_path_absent == "passed", registry_assets_only == "passed", local_sapi == "passed", source_audio_absent == "passed", text_check["status"] in {"passed", "unavailable"}]
    result = {
        "schema_version": "1.0",
        "job_id": str(bundle.get("job_id", "")),
        "status": "ready_for_human_review" if all(automatic) else "blocked",
        "reference_sha256": receipt["source_sha256"],
        "output_sha256": output_sha,
        "checks": {
            "source_output_sha_distinct": "passed" if output_sha != receipt["source_sha256"] else "blocked",
            "reference_path_absent": reference_path_absent,
            "registry_assets_only": registry_assets_only,
            "local_sapi_audio": local_sapi,
            "source_audio_absent": source_audio_absent,
            "text_similarity": text_check,
        },
        "human_review": {
            "logo_watermark": "human_review_required",
            "faces": "human_review_required",
            "perceptual_frame_similarity": "human_review_required",
            "shot_sequence_similarity": "human_review_required",
        },
    }
    validate(result, "difference_report")
    _write_json(Path(work_dir) / "difference_report.json", result)
    return result


def yaml_like_json(path: Path) -> dict[str, Any]:
    """Read the small render-job YAML without importing a second parser here."""
    try:
        import yaml
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (ImportError, OSError, UnicodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


__all__ = [
    "POLICY_VERSION",
    "REFERENCE_RUNTIME_ROOT",
    "ingest_reference",
    "analyze_reference",
    "build_original_brief",
    "brief_digest",
    "stable_reference_job_key",
    "write_original_brief",
    "materialize_review_evidence",
    "load_reference_bundle",
    "build_difference_report",
]
