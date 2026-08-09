"""Optional local audio validation and FFmpeg input construction."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def validate_audio(path: Path | None) -> Path | None:
    if path is None:
        return None
    if not path.is_file():
        raise ValueError("audio_missing")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "json", str(path)],
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    try:
        if json.loads(result.stdout)["streams"][0]["codec_type"] != "audio":
            raise ValueError
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("audio_invalid") from exc
    return path
