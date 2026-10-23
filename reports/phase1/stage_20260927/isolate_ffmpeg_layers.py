"""One ordered, short, null-output isolation pass for the FreeRTOS renderer."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "ffmpeg_layer_isolation.json"
WORK = ROOT / "dist/phase1_local/phase1_8958d25a694923c9"
IMAGES = sorted((ROOT / "assets/freertos_mutex_plain_illustrations").glob("*.png"))
AUDIO = WORK / "audio.wav"
SUBTITLE = WORK / "subtitle.srt"
LIMIT = 30


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(name: str, command: list[str], results: list[dict[str, object]]) -> bool:
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=LIMIT)
        status = "passed" if result.returncode == 0 else "failed"
        exit_code = result.returncode
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        exit_code = None
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    results.append({
        "name": name,
        "command": command,
        "timeout_seconds": LIMIT,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "status": status,
        "exit_code": exit_code,
        "stderr": stderr[-1500:],
    })
    print(f"[{len(results)}] {name}: {status}", flush=True)
    return status == "passed"


def graph(subtitles: bool, audio: bool) -> list[str]:
    command = ["ffmpeg", "-nostdin", "-v", "error"]
    for image in IMAGES:
        command += ["-loop", "1", "-framerate", "30", "-t", "2.0", "-i", str(image)]
    if audio:
        command += ["-i", str(AUDIO)]
    filters = [
        f"[{index}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xF4F6F8,"
        f"fps=30,setsar=1,format=yuv420p[v{index}]"
        for index in range(5)
    ]
    current = "v0"
    for index in range(1, 5):
        output = f"x{index}"
        filters.append(f"[{current}][v{index}]xfade=transition=fade:duration=0.4:offset={index * 1.6:.1f}[{output}]")
        current = output
    if subtitles:
        path = SUBTITLE.as_posix().replace(":", r"\:")
        filters.append(f"[{current}]subtitles=filename='{path}':charenc=UTF-8[vout]")
        current = "vout"
    command += ["-filter_complex", ";".join(filters), "-map", f"[{current}]"]
    if audio:
        command += ["-map", "5:a:0", "-af", "aresample=24000"]
    else:
        command += ["-an"]
    return command + ["-t", "2.5", "-f", "null", "-"]


def main() -> None:
    if OUT.exists():
        raise RuntimeError("isolation_report_exists_refusing_repeat")
    if len(IMAGES) != 5 or not AUDIO.is_file() or not SUBTITLE.is_file():
        raise RuntimeError("source_contract_missing")
    SUBTITLE.read_text(encoding="utf-8")
    results: list[dict[str, object]] = []
    inputs = {path.relative_to(ROOT).as_posix(): sha(path) for path in [*IMAGES, AUDIO, SUBTITLE]}

    for image in IMAGES:
        command = ["ffmpeg", "-nostdin", "-v", "error", "-loop", "1", "-framerate", "30", "-t", "0.5", "-i", str(image), "-frames:v", "15", "-f", "null", "-"]
        if not probe(f"png:{image.name}", command, results):
            break
    else:
        if probe("audio:wav", ["ffmpeg", "-nostdin", "-v", "error", "-i", str(AUDIO), "-t", "1", "-f", "null", "-"], results):
            subtitle_path = SUBTITLE.as_posix().replace(":", r"\:")
            subtitle_command = ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30:d=1", "-vf", f"subtitles=filename='{subtitle_path}':charenc=UTF-8", "-t", "1", "-f", "null", "-"]
            if probe("subtitle:standalone", subtitle_command, results):
                if probe("graph:video", graph(False, False), results):
                    if probe("graph:subtitle", graph(True, False), results):
                        probe("graph:audio", graph(True, True), results)

    first_failure = next((result["name"] for result in results if result["status"] != "passed"), None)
    report = {
        "schema_version": "phase1_ffmpeg_layer_isolation_v1",
        "source_attempt": "reports/phase1/stage_20260927/freertos_attempt_001.json",
        "input_sha256": inputs,
        "output_mode": "null_only",
        "probe_limit_seconds": LIMIT,
        "results": results,
        "first_failing_layer": first_failure,
        "status": "first_failure_found" if first_failure else "inconclusive_no_short_probe_failure",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "first_failing_layer": first_failure, "probe_count": len(results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
