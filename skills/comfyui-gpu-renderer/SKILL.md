---
name: comfyui-gpu-renderer
description: "Use a local RTX GPU through curated ComfyUI workflows to generate covers, backgrounds, illustrations, short B-roll, masks, and enhanced assets."
version: 0.2.0
metadata:
  openclaw:
    emoji: "🦞"
---

# ComfyUI GPU renderer

Default endpoint: `http://127.0.0.1:8188`.

## Approved workflow classes

- `cover_background_v1`
- `vertical_illustration_v1`
- `reference_style_image_v1`
- `short_broll_2s_v1`
- `short_broll_4s_low_vram_v1`
- `remove_background_v1`
- `upscale_realesrgan_v1`

## 4070 SUPER rules

- One heavy workflow at a time.
- Default batch size 1.
- Prefer image generation over long video diffusion.
- AI video maximum 4 seconds per clip.
- Start low resolution, then upscale.
- Preserve free VRAM for the OS and browser.
- On OOM:
  1. clear ComfyUI queue/cache;
  2. lower resolution/frames;
  3. use quantized/low-VRAM workflow;
  4. fall back to still image;
  5. fall back to Remotion animation.

## Unattended restrictions

- No automatic custom-node installation.
- No automatic model download unless its hash is present in the approved model registry.
- No workflow may write outside the job asset directory.
- No face/voice cloning unless the user explicitly provides rights and requests it.
