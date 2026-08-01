"""Public-fixture narration with boundary-aware Edge TTS and safe SAPI fallback."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from .config import PROJECT_ROOT


DEFAULT_VOICE = "zh-CN-YunxiNeural"
FALLBACK_VOICE = "Microsoft Huihui Desktop"
EDGE_TTS_VERSION = "7.2.8"
RATE = "+0%"
VOLUME = "+0%"
PITCH = "+0Hz"
BOUNDARY_SCHEMA_VERSION = "1.0"
AUDIO_QUALITY_SCHEMA_VERSION = "2.0"
SAFE_FALLBACK_REASONS = {
    "network_unavailable",
    "provider_rejected",
    "boundary_unavailable",
    "sapi_fallback",
    "unknown_provider_failure",
}
EdgeRunner = Callable[[str, Path], list[dict[str, Any]] | None]
SapiRunner = Callable[[str, Path], None]
Normalizer = Callable[[Path, Path], dict[str, Any]]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_edge_failure(exc: Exception) -> str:
    value = str(exc).lower()
    if any(token in value for token in ("timeout", "network", "connection", "dns", "temporar")):
        return "network_unavailable"
    if any(token in value for token in ("reject", "forbidden", "unauthor", "status code")):
        return "provider_rejected"
    if "boundary" in value:
        return "boundary_unavailable"
    return "unknown_provider_failure"


def _filter_available(name: str) -> bool:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"], text=True, capture_output=True, check=False
    )
    return result.returncode == 0 and re.search(rf"\b{re.escape(name)}\b", result.stdout + result.stderr) is not None


def _parse_loudnorm(stderr: str) -> dict[str, float]:
    match = re.search(r"\{\s*\"input_i\".*?\}", stderr, re.DOTALL)
    if not match:
        raise RuntimeError("audio_normalization_measurement_missing")
    raw = json.loads(match.group(0))
    keys = ("input_i", "input_lra", "input_tp", "input_thresh", "target_offset")
    try:
        return {key: float(raw[key]) for key in keys}
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("audio_normalization_measurement_invalid") from exc


def _parse_loudnorm_output(stderr: str) -> dict[str, float]:
    match = re.search(r"\{\s*\"input_i\".*?\}", stderr, re.DOTALL)
    if not match:
        raise RuntimeError("audio_normalization_measurement_missing")
    raw = json.loads(match.group(0))
    keys = ("output_i", "output_lra", "output_tp")
    try:
        return {key: float(raw[key]) for key in keys}
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("audio_normalization_measurement_invalid") from exc


def normalize_wav(source: Path, target: Path) -> dict[str, Any]:
    """Two-pass, local FFmpeg loudness normalization with numeric-only evidence."""
    if not _filter_available("loudnorm") or not _filter_available("ebur128") or not _filter_available("silencedetect"):
        raise RuntimeError("quality_capability_blocked")
    first = subprocess.run(
        [
            "ffmpeg", "-y", "-nostdin", "-hide_banner", "-i", str(source),
            "-af", "loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json", "-f", "null", "-",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if first.returncode != 0:
        raise RuntimeError("audio_normalization_failed")
    measured = _parse_loudnorm(first.stderr)
    filter_spec = (
        "loudnorm=I=-16:LRA=11:TP=-1.5:"
        f"measured_I={measured['input_i']}:measured_LRA={measured['input_lra']}:"
        f"measured_TP={measured['input_tp']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true:print_format=json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    second = subprocess.run(
        [
            "ffmpeg", "-y", "-nostdin", "-hide_banner", "-i", str(source), "-af", filter_spec,
            "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if second.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        raise RuntimeError("audio_normalization_failed")
    output = _parse_loudnorm_output(second.stderr)
    return {
        "status": "normalized",
        "target_integrated_lufs": -16.0,
        "target_lra": 11.0,
        "target_true_peak_dbtp": -1.5,
        "measured_input": measured,
        "measured_output": output,
    }


class CandidateTts:
    def __init__(
        self,
        cache_root: Path,
        edge_runner: EdgeRunner | None = None,
        sapi_runner: SapiRunner | None = None,
        normalizer: Normalizer | None = None,
    ) -> None:
        self.cache_root = cache_root
        self.edge_runner = edge_runner or self._edge_runner
        self.sapi_runner = sapi_runner or self._sapi_runner
        self.normalizer = normalizer or normalize_wav

    @staticmethod
    def _edge_runner(text: str, target: Path) -> list[dict[str, Any]]:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("edge_tts_not_installed") from exc

        async def stream() -> list[dict[str, Any]]:
            boundaries: list[dict[str, Any]] = []
            communicator = edge_tts.Communicate(
                text, DEFAULT_VOICE, rate=RATE, volume=VOLUME, pitch=PITCH
            )
            with target.open("wb") as media:
                async for chunk in communicator.stream():
                    if chunk["type"] == "audio":
                        media.write(chunk["data"])
                    elif chunk["type"] in {"WordBoundary", "SentenceBoundary"}:
                        offset = chunk.get("offset")
                        duration = chunk.get("duration")
                        if isinstance(offset, int) and isinstance(duration, int) and duration >= 0:
                            boundaries.append(
                                {
                                    "start": round(offset / 10_000_000, 3),
                                    "end": round((offset + duration) / 10_000_000, 3),
                                    "kind": "word" if chunk["type"] == "WordBoundary" else "sentence",
                                }
                            )
            return boundaries

        return asyncio.run(stream())

    @staticmethod
    def _sapi_runner(text: str, target: Path) -> None:
        script = PROJECT_ROOT / "scripts" / "p1_sapi_tts.ps1"
        with tempfile.TemporaryDirectory(prefix="p1-candidate-tts-") as temp_dir:
            text_path = Path(temp_dir) / "public_fixture.txt"
            text_path.write_text(text, encoding="utf-8")
            command = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                "-InputTextPath", str(text_path), "-OutputPath", str(target), "-VoiceName", FALLBACK_VOICE,
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            if result.returncode != 0 or not target.exists():
                raise RuntimeError("sapi_tts_failed")

    @staticmethod
    def _convert_to_wav(source: Path, target: Path) -> None:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", str(source), "-ac", "1",
                "-ar", "44100", "-c:a", "pcm_s16le", str(target),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 or not target.exists():
            raise RuntimeError("tts_wav_conversion_failed")

    @staticmethod
    def _cache_key(text: str, provider: str) -> str:
        material = {
            "provider_request": provider,
            "edge_tts_version": EDGE_TTS_VERSION,
            "voice": DEFAULT_VOICE,
            "rate": RATE,
            "volume": VOLUME,
            "pitch": PITCH,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "boundary_schema_version": BOUNDARY_SCHEMA_VERSION,
            "audio_quality_schema_version": AUDIO_QUALITY_SCHEMA_VERSION,
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()

    def synthesize(self, text: str, output: Path, provider: str = "auto") -> dict[str, Any]:
        if not text.strip():
            raise ValueError("tts_text_required")
        if provider not in {"auto", "edge", "sapi"}:
            raise ValueError("tts_provider_invalid")
        output.parent.mkdir(parents=True, exist_ok=True)
        cache_key = self._cache_key(text, provider)
        cache_target = self.cache_root / f"{cache_key}.wav"
        cache_manifest = self.cache_root / f"{cache_key}.json"
        if cache_target.exists() and cache_manifest.exists():
            shutil.copy2(cache_target, output)
            cached = json.loads(cache_manifest.read_text(encoding="utf-8"))
            return {
                **cached,
                "provider": "cache",
                "cache_hit": True,
                "audio_sha256": sha256_file(output),
            }

        fallback_reason: str | None = None
        boundaries: list[dict[str, Any]] = []
        selected = provider
        with tempfile.TemporaryDirectory(prefix="p1-candidate-audio-") as temp_dir:
            temporary = Path(temp_dir)
            raw_wav = temporary / "raw.wav"
            if provider in {"auto", "edge"}:
                try:
                    media = temporary / "edge.mp3"
                    boundaries = self.edge_runner(text, media) or []
                    self._convert_to_wav(media, raw_wav)
                    selected = "edge"
                except Exception as exc:
                    if provider == "edge":
                        raise RuntimeError(f"edge_tts_failed:{_safe_edge_failure(exc)}") from None
                    fallback_reason = _safe_edge_failure(exc)
                    selected = "sapi"
                    self.sapi_runner(text, raw_wav)
            else:
                selected = "sapi"
                self.sapi_runner(text, raw_wav)
            audio_quality = self.normalizer(raw_wav, output)

        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("tts_output_missing")
        self.cache_root.mkdir(parents=True, exist_ok=True)
        manifest = self._manifest(
            provider=selected,
            provider_fallback=selected == "sapi" and provider == "auto",
            fallback_reason=fallback_reason,
            text=text,
            output=output,
            cache_key=cache_key,
            boundaries=boundaries,
            audio_quality=audio_quality,
        )
        shutil.copy2(output, cache_target)
        cache_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
        return manifest

    @staticmethod
    def _manifest(
        *,
        provider: str,
        provider_fallback: bool,
        fallback_reason: str | None,
        text: str,
        output: Path,
        cache_key: str,
        boundaries: list[dict[str, Any]],
        audio_quality: dict[str, Any],
    ) -> dict[str, Any]:
        if fallback_reason is not None and fallback_reason not in SAFE_FALLBACK_REASONS:
            raise ValueError("fallback_reason_invalid")
        return {
            "provider": provider,
            "provider_fallback": provider_fallback,
            "fallback_reason": fallback_reason,
            "cache_hit": False,
            "voice": DEFAULT_VOICE if provider == "edge" else FALLBACK_VOICE,
            "edge_tts_version": EDGE_TTS_VERSION,
            "rate": RATE,
            "volume": VOLUME,
            "pitch": PITCH,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "audio_sha256": sha256_file(output),
            "cache_key": cache_key,
            "boundary_schema_version": BOUNDARY_SCHEMA_VERSION,
            "audio_quality_schema_version": AUDIO_QUALITY_SCHEMA_VERSION,
            "boundaries": boundaries,
            "audio_quality": audio_quality,
        }
