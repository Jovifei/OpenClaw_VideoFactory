"""Offline faster-whisper sidecar; never downloads a model or emits a path."""

from __future__ import annotations

import argparse
import json

from faster_whisper import WhisperModel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(args.video, beam_size=5, vad_filter=True)
    result = []
    for segment in segments:
        text = str(getattr(segment, "text", "")).strip()
        if text:
            result.append({"start_seconds": round(float(segment.start), 3), "end_seconds": round(float(segment.end), 3), "text": text, "speaker": None})
    print(json.dumps({"segments": result}, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
