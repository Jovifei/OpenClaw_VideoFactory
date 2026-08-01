"""Generate 7 style-memory templates (placeholders only, no unconfirmed brand conclusions)."""

from pathlib import Path

OUT = Path(r"E:\project\OpenClaw_VideoFactory\templates\style_memory")
OUT.mkdir(parents=True, exist_ok=True)

HEADER = """---
style_memory_version: "0.1-placeholder"
status: template
note: "Placeholder only. Do NOT fill unconfirmed brand conclusions without user approval."
---

# {title}

> Template. Fill placeholders only after explicit user confirmation. Record change_reason on every version bump.

"""

templates = {
    "BRAND": """# BRAND

- brand_positioning: <placeholder - to be confirmed by user>
- target_audience: <placeholder>
- tone_of_voice: <placeholder>
- forbidden_expressions: <placeholder - e.g., no clickbait, no sensitive terms>
- hook_habits: <placeholder - typical hook patterns>
- change_reason: <why this version changed>
""",
    "NARRATIVE": """# NARRATIVE

- narrative_structure: <placeholder - e.g., hook->develop->tech->cta>
- structure_ratios_default: <placeholder - hook/develop/tech/cta %>
- pacing_default: <placeholder - words per minute>
- change_reason: <placeholder>
""",
    "MOTION": """# MOTION (Motion.MD style)

- color_palette: <placeholder>
- font_family: <placeholder>
- font_size: <placeholder>
- animation_easing: <placeholder>
- motion_recipes: <placeholder - component entrance/exit/number animation>
- design_specs: <placeholder>
- renderer_preference: <placeholder - remotion | hyperframes>
- change_reason: <placeholder>
""",
    "CAPTION": """# CAPTION

- subtitle_font: <placeholder>
- subtitle_color: <placeholder>
- subtitle_position: <placeholder>
- safe_area: <placeholder - per platform>
- max_chars_per_line: <placeholder>
- change_reason: <placeholder>
""",
    "AUDIO": """# AUDIO

- tts_voice: <placeholder - e.g., stable AI TTS voice>
- tts_speed: <placeholder>
- bgm_style: <placeholder>
- bgm_ducking: <placeholder>
- sfx_library: <placeholder - approved only>
- change_reason: <placeholder>
""",
    "CHARACTER": """# CHARACTER (小粉飞猪 / pink pig mascot)

- character: 小粉飞猪 (pink pig mascot)
- visual_traits: low-saturation misty pink, small wings, small round nose, dot eyes, serious-calm personality
- core_actions: disassemble/install/test/repair/solder/carry-information
- must_not_occlude: code, protocol frames, charts, subtitles
- failure_degradation: static signature or no appearance; must not block the final cut
- change_reason: <placeholder>
""",
    "PLATFORM_PROFILES": """# PLATFORM_PROFILES

- douyin:
  - safe_area: <placeholder>
  - aspect_ratio: 9:16
  - duration_range: <placeholder>
- video_account (视频号):
  - safe_area: <placeholder>
  - aspect_ratio: <placeholder>
- bilibili:
  - safe_area: <placeholder>
  - aspect_ratio: 16:9
- change_reason: <placeholder>
""",
}

for name, body in templates.items():
    p = OUT / f"{name}.template.md"
    p.write_text(HEADER.format(title=name) + body, encoding="utf-8")
    print(f"wrote {p.name}")

print(f"\nGenerated {len(templates)} style-memory templates in {OUT}")
