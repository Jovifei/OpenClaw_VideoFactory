"""FFmpeg renderer for a short, local vertical image-video timeline."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .audio import validate_audio
from .errors import FactoryContractError
from .timeline import rendered_duration_seconds
from .transition import ffmpeg_transition


WIDTH, HEIGHT, FPS = 1080, 1920, 30

# Knowledge illustrations reserve the middle of the vertical canvas for the
# 16:9 body image and keep captions in a dedicated lower safe band.  These
# values are intentionally conservative: the previous default libass style
# used an oversized font and allowed captions to cover the artwork.
DEFAULT_SUBTITLE_STYLE: dict[str, object] = {
    "layout": "bottom_safe_band",
    "font_name": "Microsoft YaHei",
    "font_size": 44,
    "margin_left": 90,
    "margin_right": 90,
    "margin_vertical": 250,
    "alignment": 2,
    "outline": 1,
    "shadow": 0,
    "primary_colour": "&H00151515",
    "outline_colour": "&H00F7E4EA",
    "border_style": 1,
}


def _subtitle_filename(path: Path) -> str:
    # FFmpeg filter syntax needs a Windows drive colon escaped, while the
    # process argument itself remains shell-free and therefore safe.
    return path.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")


def _subtitle_force_style(
    style: dict[str, object] | None,
    *,
    composition: dict[str, object] | None = None,
) -> str:
    """Return a bounded libass style for the subtitle safe band."""

    values = dict(DEFAULT_SUBTITLE_STYLE)
    if style:
        values.update(style)
    # A composition is the authoritative safe-area contract.  Job-level
    # legacy style values (notably the old 44px font) must not override its
    # bounded 52–60px geometry and margins.
    if composition and isinstance(composition.get("subtitle_style"), dict):
        values.update(composition["subtitle_style"])
    layout = str(values.get("layout", "bottom_safe_band"))
    font_size = int(values.get("font_size", 44))
    margin_vertical = int(values.get("margin_vertical", 250))
    margin_left = int(values.get("margin_left", 90))
    margin_right = int(values.get("margin_right", 90))
    if composition:
        layout = "knowledge_illustration"
        values["layout"] = layout
        expected_size = int(composition.get("subtitle_style", {}).get("font_size", 56)) if isinstance(composition.get("subtitle_style"), dict) else 56
        if font_size != expected_size or margin_left != 90 or margin_right != 90:
            raise FactoryContractError(
                "subtitle_layout_invalid",
                "Knowledge subtitle style would leave the declared safe region.",
                {"field": "subtitle_style"},
            )
    if layout not in {"bottom_safe_band", "knowledge_illustration"}:
        raise ValueError("subtitle_layout_unsupported")
    if not 32 <= font_size <= 60:
        raise ValueError("subtitle_font_size_invalid")
    if not 180 <= margin_vertical <= 420:
        raise ValueError("subtitle_margin_invalid")
    if margin_left < 40 or margin_right < 40:
        raise ValueError("subtitle_margin_invalid")

    # SRT is converted by libass to its 384x288 virtual canvas.  The public
    # contract expresses the desired values in final 1080x1920 pixels; map
    # those values back to the virtual canvas before passing force_style.
    # Without this conversion a nominal 44px font becomes roughly 293px and
    # a 250px bottom margin moves the caption into the top letterbox band.
    ass_scale = 288.0 / HEIGHT
    ass_font_size = max(1, round(font_size * ass_scale))
    ass_margin_vertical = max(1, round(margin_vertical * ass_scale))
    ass_margin_left = max(1, round(margin_left * (384.0 / WIDTH)))
    ass_margin_right = max(1, round(margin_right * (384.0 / WIDTH)))
    return ",".join(
        [
            f"FontName={values.get('font_name', 'Microsoft YaHei')}",
            f"FontSize={ass_font_size}",
            f"PrimaryColour={values.get('primary_colour', '&H00151515')}",
            f"OutlineColour={values.get('outline_colour', '&H00F7E4EA')}",
            f"BorderStyle={int(values.get('border_style', 1))}",
            f"Outline={int(values.get('outline', 1))}",
            f"Shadow={int(values.get('shadow', 0))}",
            f"Alignment={int(values.get('alignment', 2))}",
            f"MarginL={ass_margin_left}",
            f"MarginR={ass_margin_right}",
            f"MarginV={ass_margin_vertical}",
        ]
    )


def build_render_command(
    *,
    asset_dir: Path,
    timeline: list[dict[str, object]],
    subtitle_path: Path,
    output_path: Path,
    transition_seconds: float,
    audio_path: Path | None,
    audio_loop: bool = True,          # NEW: default=True preserves today's behavior
    repo_root: Path | None = None,    # NEW: used to resolve image_path when present
    subtitle_style: dict[str, object] | None = None,
    audio_gain: float = 1.0,
    audio_normalize: bool = False,
    audio_sample_rate: int | None = None,
    composition: dict[str, object] | None = None,
    signature_path: Path | None = None,
) -> tuple[list[str], float]:
    if not subtitle_path.is_file():
        raise ValueError("subtitle_missing")
    duration = rendered_duration_seconds(timeline, transition_seconds)
    if not isinstance(audio_gain, (int, float)) or not 0.1 <= float(audio_gain) <= 8.0:
        raise ValueError("audio_gain_invalid")
    if audio_sample_rate is not None and not 8_000 <= int(audio_sample_rate) <= 192_000:
        raise ValueError("audio_sample_rate_invalid")
    command = ["ffmpeg", "-y", "-nostdin", "-loglevel", "error"]
    for item in timeline:
        # NEW (branch 1): if timeline item has "image_path", resolve via repo_root;
        # otherwise fall back to legacy behavior (asset_dir / image).
        image_input: str
        if "image_path" in item and item["image_path"] and repo_root is not None:
            image_input = str((repo_root / str(item["image_path"])).resolve())
        else:
            image_input = str(asset_dir / str(item["image"]))
        command.extend(["-loop", "1", "-framerate", str(FPS), "-t", str(item["duration"]), "-i", image_input])
    audio = validate_audio(audio_path)
    signature_input_index: int | None = None
    if composition is not None:
        if signature_path is None or not Path(signature_path).is_file():
            raise FactoryContractError(
                "pink_pig_style_missing",
                "Knowledge composition requires a renderable Pink Pig signature asset.",
                {"field": "signature_path"},
            )
        signature_input_index = len(timeline)
        command.extend(["-loop", "1", "-framerate", str(FPS), "-t", str(duration), "-i", str(signature_path)])
    audio_input_index = len(timeline) + (1 if signature_input_index is not None else 0)
    if audio is not None:
        audio_input_index = audio_input_index
    # NEW (branch 2): audio_loop=False skips -stream_loop -1 (for TTS-aligned audio);
    # audio_loop=True keeps existing behavior.
    if audio is not None:
        if audio_loop:
            command.extend(["-stream_loop", "-1", "-i", str(audio)])
        else:
            command.extend(["-i", str(audio)])
    filters: list[str] = []
    if composition is None:
        for index in range(len(timeline)):
            filters.append(
                f"[{index}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0xF7E4EA,fps={FPS},setsar=1,format=yuv420p[v{index}]"
            )
    else:
        canvas = composition.get("canvas", {})
        regions = composition.get("regions", {})
        if not isinstance(canvas, dict) or not isinstance(regions, dict):
            raise FactoryContractError(
                "composition_schema_invalid",
                "Composition is missing canvas or regions.",
                {"field": "canvas/regions"},
            )
        content = regions.get("content_area", {})
        if not isinstance(content, dict):
            raise FactoryContractError(
                "composition_schema_invalid",
                "Composition is missing content_area.",
                {"field": "regions.content_area"},
            )
        cw, ch = int(content.get("width", 1080)), int(content.get("height", 800))
        cx, cy = int(content.get("x", 0)), int(content.get("y", 240))
        background = str(canvas.get("background_color", "0xF7E4EA"))
        if background.startswith("0x"):
            background = background[2:]
        for index, item in enumerate(timeline):
            filters.append(
                f"[{index}:v]scale={cw}:{ch}:force_original_aspect_ratio=decrease,pad={cw}:{ch}:(ow-iw)/2:(oh-ih)/2:color=white,fps={FPS},setsar=1,format=rgba[body{index}]"
            )
            filters.append(
                f"color=c=0x{background}:s={WIDTH}x{HEIGHT}:r={FPS}:d={float(item['duration'])}[bg{index}]"
            )
            filters.append(
                f"[bg{index}][body{index}]overlay={cx}:{cy}:shortest=1,format=yuv420p[v{index}]"
            )
    current = "v0"
    cursor = float(timeline[0]["duration"])
    for index in range(1, len(timeline)):
        transition = ffmpeg_transition(str(timeline[index - 1]["transition"]))
        offset = round(cursor - transition_seconds, 3)
        output = f"x{index}"
        filters.append(f"[{current}][v{index}]xfade=transition={transition}:duration={transition_seconds}:offset={offset}[{output}]")
        current = output
        cursor += float(timeline[index]["duration"]) - transition_seconds
    subtitle_input = current
    if signature_input_index is not None:
        signature_region = regions.get("signature_area", {}) if isinstance(regions, dict) else {}
        sx = int(signature_region.get("x", 90)) if isinstance(signature_region, dict) else 90
        sy = int(signature_region.get("y", 1760)) if isinstance(signature_region, dict) else 1760
        max_height = 80
        if isinstance(composition.get("signature"), dict):
            max_height = int(composition["signature"].get("max_height", 80))
        filters.append(f"[{current}]format=rgba[main_rgba]")
        filters.append(f"[{signature_input_index}:v]scale=-1:{max_height},format=rgba[signature_rgba]")
        filters.append(f"[main_rgba][signature_rgba]overlay={sx}:{sy}:eof_action=repeat,format=yuv420p[with_signature]")
        subtitle_input = "with_signature"
    force_style = _subtitle_force_style(subtitle_style, composition=composition)
    filters.append(
        f"[{subtitle_input}]subtitles=filename='{_subtitle_filename(subtitle_path)}':"
        f"charenc=UTF-8:force_style='{force_style}'[vout]"
    )
    command.extend(["-filter_complex", ";".join(filters), "-map", "[vout]"])
    if audio is None:
        command.extend(["-an"])
    else:
        command.extend(["-map", f"{audio_input_index}:a:0", "-shortest", "-c:a", "aac", "-b:a", "128k"])
        audio_filters: list[str] = []
        if audio_normalize:
            # Single-pass EBU-R128 normalization prevents a valid but
            # near-silent BGM track from surviving into the MP4.
            audio_filters.append("loudnorm=I=-18:TP=-1.5:LRA=11")
        if float(audio_gain) != 1.0:
            audio_filters.append(f"volume={float(audio_gain):.3f}")
        if audio_sample_rate is not None:
            audio_filters.append(f"aresample={int(audio_sample_rate)}")
        if audio_filters:
            command.extend(["-af", ",".join(audio_filters)])
    command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", str(output_path)])
    return command, duration


def render_video(**kwargs: Any) -> dict[str, object]:
    output_path = Path(kwargs["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command, duration = build_render_command(**kwargs)
    result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=300)
    if result.returncode != 0 or not output_path.is_file() or output_path.stat().st_size == 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["ffmpeg_failed"]
        raise RuntimeError(f"render_failed:{detail[0][:180]}")
    return {"renderer": "ffmpeg", "duration_seconds": duration, "output": str(output_path), "audio_enabled": kwargs.get("audio_path") is not None}
