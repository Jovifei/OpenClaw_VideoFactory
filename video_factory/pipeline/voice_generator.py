"""Narrow adapters for the two permitted narration backends.

``edge-tts`` remains the historical default and therefore keeps its command
shape for existing callers.  ``windows-sapi`` is deliberately local: the
narration text is sent on standard input to PowerShell and is never placed in a
process command line or a temporary script file.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


_EDGE_TTS = "edge-tts"
_WINDOWS_SAPI = "windows-sapi"
_WINDOWS_SAPI_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$text = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($text)) { exit 3 }
$outputPath = [Environment]::GetEnvironmentVariable('PINK_PIG_SAPI_OUTPUT')
$voiceName = [Environment]::GetEnvironmentVariable('PINK_PIG_SAPI_VOICE')
if ([string]::IsNullOrWhiteSpace($outputPath)) { exit 4 }
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  if (-not [string]::IsNullOrWhiteSpace($voiceName)) {
    $speaker.SelectVoice($voiceName)
  }
  $speaker.SetOutputToWaveFile($outputPath)
  $speaker.Speak($text)
} finally {
  $speaker.Dispose()
}
"""


def generate_voice(
    text: str,
    output: Path,
    *,
    voice: str = "zh-CN-XiaoxiaoNeural",
    provider: str = _EDGE_TTS,
) -> Path:
    """Generate a narration artifact using an explicitly selected provider.

    The caller chooses the file extension appropriate to the selected
    provider.  Windows SAPI produces WAV data; edge-tts preserves the previous
    MP3-compatible behaviour.  Errors are intentionally stable because the
    audio planner decides whether to fall back to local BGM.
    """
    if not text.strip():
        raise ValueError("voice_text_empty")
    if provider not in {_EDGE_TTS, _WINDOWS_SAPI}:
        raise ValueError("voice_provider_invalid")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if provider == _WINDOWS_SAPI:
        _generate_windows_sapi(text, output, voice)
    else:
        _generate_edge_tts(text, output, voice)

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("voice_generation_failed")
    return output


def _generate_edge_tts(text: str, output: Path, voice: str) -> None:
    executable = shutil.which("edge-tts")
    if executable is None:
        raise RuntimeError("edge_tts_not_installed")
    completed = subprocess.run(
        [executable, "--voice", voice, "--text", text, "--write-media", str(output)],
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError("edge_tts_generation_failed")


def _generate_windows_sapi(text: str, output: Path, voice: str) -> None:
    """Generate WAV narration through Windows SAPI without exposing *text*.

    ``input=`` is intentional: `text` never appears in the command arguments,
    exception, or a persisted PowerShell script.  `-NoProfile` prevents a
    user profile from changing the local execution behaviour.
    """
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if executable is None:
        raise RuntimeError("windows_sapi_unavailable")
    child_environment = os.environ.copy()
    child_environment["PINK_PIG_SAPI_OUTPUT"] = str(output)
    child_environment["PINK_PIG_SAPI_VOICE"] = voice
    completed = subprocess.run(
        [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            _WINDOWS_SAPI_SCRIPT,
        ],
        env=child_environment,
        input=text,
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError("windows_sapi_generation_failed")
