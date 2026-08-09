"""Optional edge-tts adapter; the MVP demo does not require network TTS."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def generate_voice(text: str, output: Path, *, voice: str = "zh-CN-XiaoxiaoNeural") -> Path:
    if not text.strip():
        raise ValueError("voice_text_empty")
    executable = shutil.which("edge-tts")
    if executable is None:
        raise RuntimeError("edge_tts_not_installed")
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [executable, "--voice", voice, "--text", text, "--write-media", str(output)],
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("edge_tts_generation_failed")
    return output
