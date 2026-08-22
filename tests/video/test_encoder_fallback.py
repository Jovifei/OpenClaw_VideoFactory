from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from video_factory.pipeline import renderer


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets" / "pink_pig"


def _inputs(tmp_path: Path) -> dict[str, object]:
    subtitle = tmp_path / "subtitle.srt"
    subtitle.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n测试\n", encoding="utf-8"
    )
    return {
        "asset_dir": ASSETS,
        "timeline": [{"image": "pig01.png", "duration": 1.0, "transition": "none"}],
        "subtitle_path": subtitle,
        "output_path": tmp_path / "output.mp4",
        "transition_seconds": 0.4,
        "audio_path": None,
    }


def test_encoder_selection_is_explicit(tmp_path: Path) -> None:
    nvenc, _ = renderer.build_render_command(**_inputs(tmp_path), encoder="nvenc")
    cpu, _ = renderer.build_render_command(**_inputs(tmp_path), encoder="cpu")
    assert nvenc[nvenc.index("-c:v") + 1] == "h264_nvenc"
    assert cpu[cpu.index("-c:v") + 1] == "libx264"


def test_nvenc_failure_retries_with_cpu(monkeypatch, tmp_path: Path) -> None:
    observed: list[list[str]] = []
    values = _inputs(tmp_path)

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        observed.append(command)
        if len(observed) == 2:
            Path(str(values["output_path"])).write_bytes(b"cpu-output")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="NVENC unavailable")

    monkeypatch.setattr(renderer.subprocess, "run", fake_run)
    result = renderer.render_video(**values, encoder="auto")

    assert observed[0][observed[0].index("-c:v") + 1] == "h264_nvenc"
    assert observed[1][observed[1].index("-c:v") + 1] == "libx264"
    assert result["encoder_requested"] == "auto"
    assert result["encoder_used"] == "libx264"
    assert result["encoder_fallback_reason"] == "nvenc_failed"
