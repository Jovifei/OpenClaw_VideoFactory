"""Optional cached faster-whisper warning probe for retained v7 audio."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def _normalize(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u3400-\u9fff]+", "", value).lower()


def _probe_fixture(model: Any, fixture: dict[str, Any], anchors: list[str]) -> dict[str, Any]:
    passes = fixture["passes"]
    final_pass = next(item for item in passes if int(item.get("rewrite_count", 0)) == 1 and "aligned_audio" in item)
    audio_path = Path(str(final_pass["aligned_audio"]["path"]))
    segments, info = model.transcribe(str(audio_path), beam_size=1, vad_filter=True, language="zh")
    transcript_parts: list[str] = []
    for segment in segments:
        text = str(getattr(segment, "text", "")).strip()
        if text:
            transcript_parts.append(text)
    transcript = " ".join(transcript_parts)
    normalized = _normalize(transcript)
    matched = [anchor for anchor in anchors if _normalize(anchor) in normalized]
    status = "USE_AS_SECONDARY_WARNING" if len(matched) == len(anchors) else "NOT_RELIABLE_ENOUGH"
    return {
        "topic": fixture["topic"],
        "topic_digest": fixture["topic_digest"],
        "audio_sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
        "audio_duration_seconds": final_pass["aligned_audio"]["duration_seconds"],
        "detected_language": getattr(info, "language", None),
        "transcript": transcript,
        "anchors": anchors,
        "matched_anchors": matched,
        "missing_anchors": [anchor for anchor in anchors if anchor not in matched],
        "status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--model-snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    os.environ["HF_HUB_OFFLINE"] = "1"
    from faster_whisper import WhisperModel

    report = json.loads(args.report.read_text(encoding="utf-8"))
    fixtures = report["fixtures"]
    model = WhisperModel(
        str(args.model_snapshot),
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        local_files_only=True,
    )
    results = []
    for fixture in fixtures:
        topic = str(fixture["topic"])
        anchors = (
            ["看门狗", "擦除", "BUSY", "错误", "服务窗口"]
            if "看门狗" in topic
            else ["Mutex", "ISR", "FromISR", "任务", "优先级"]
        )
        results.append(_probe_fixture(model, fixture, anchors))
    output = {
        "schema_version": "phase1_audio_asr_probe_v1",
        "model": "faster-whisper-small",
        "model_source": "already_cached_local_snapshot",
        "download_performed": False,
        "phase1_gate_authority": False,
        "fixtures": results,
        "status": "USE_AS_SECONDARY_WARNING" if all(item["status"] == "USE_AS_SECONDARY_WARNING" for item in results) else "NOT_RELIABLE_ENOUGH",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
