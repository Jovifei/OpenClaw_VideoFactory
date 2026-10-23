"""One-shot CPU diagnostic for the preserved FreeRTOS render timeout."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = Path(__file__).resolve().parent
FAILED_LOG = REPORT_DIR / "freertos_run.log"
RUNTIME = Path("E:/OpenClaw_VideoFactory_Runtime/phase1_render_timeout_diag_20260927")
OUTPUT = RUNTIME / "cpu_probe.mp4"
REPORT = REPORT_DIR / "cpu_probe.json"
STDERR = REPORT_DIR / "cpu_probe_stderr.log"
STDOUT = REPORT_DIR / "cpu_probe_stdout.log"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def main() -> None:
    for path in (OUTPUT, REPORT, STDERR, STDOUT):
        if path.exists():
            raise RuntimeError(f"probe_target_exists:{path.name}")
    line = next(
        value for value in FAILED_LOG.read_text(encoding="utf-8").splitlines()
        if value.startswith("subprocess.TimeoutExpired: Command '")
    )
    representation = line.split("Command '", 1)[1].rsplit("' timed out after", 1)[0]
    command = ast.literal_eval(representation)
    if not isinstance(command, list) or command.count("h264_nvenc") != 1:
        raise RuntimeError("unexpected_failed_command")
    original_output = Path(command[-1])
    if "phase1-media-20260927" not in str(original_output):
        raise RuntimeError("unexpected_original_job")
    if len([arg for arg in command if arg == "8.0"]) != 5:
        raise RuntimeError("unexpected_scene_duration_contract")
    command[command.index("h264_nvenc")] = "libx264"
    command[-1] = str(OUTPUT)
    RUNTIME.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    timed_out = False
    return_code: int | None = None
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
        return_code = result.returncode
        stdout, stderr = result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout, stderr = decode(exc.stdout), decode(exc.stderr)
    elapsed = round(time.monotonic() - started, 3)
    STDOUT.write_text(stdout, encoding="utf-8")
    STDERR.write_text(stderr, encoding="utf-8")

    report: dict[str, object] = {
        "schema_version": "phase1_cpu_render_probe_v1",
        "source_failure": "reports/phase1/stage_20260927/freertos_attempt_001.json",
        "probe_count": 1,
        "only_change": "h264_nvenc replaced by libx264; new diagnostic output path",
        "timeout_seconds": 300,
        "elapsed_seconds": elapsed,
        "timed_out": timed_out,
        "exit_code": return_code,
        "output_exists": OUTPUT.is_file(),
        "output_bytes": OUTPUT.stat().st_size if OUTPUT.is_file() else 0,
        "stdout_sha256": sha(STDOUT),
        "stderr_sha256": sha(STDERR),
        "status": "diagnostic_only",
    }
    if not timed_out and return_code == 0 and OUTPUT.is_file():
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(OUTPUT)],
            capture_output=True, text=True, check=False, timeout=30,
        )
        full_decode = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"],
            capture_output=True, text=True, check=False, timeout=120,
        )
        report.update({
            "output_sha256": sha(OUTPUT),
            "ffprobe_exit_code": probe.returncode,
            "ffprobe": json.loads(probe.stdout) if probe.returncode == 0 else None,
            "full_decode_exit_code": full_decode.returncode,
            "full_decode_stderr": full_decode.stderr[-500:],
        })
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "elapsed_seconds", "timed_out", "exit_code", "output_exists", "output_bytes")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
