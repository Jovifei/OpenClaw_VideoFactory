"""Audit only the five registered FreeRTOS PNGs before any repair."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "src/factory/assets/pink_pig/registry.json"
REPORT = Path(__file__).resolve().parent / "freertos_asset_audit_before.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if REPORT.exists():
        raise RuntimeError("audit_already_exists")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assets = [item for item in registry["assets"] if item.get("render_ready") and "freertos_mutex_plain" in item.get("tags", [])]
    if len(assets) != 5:
        raise RuntimeError(f"expected_five_assets_found_{len(assets)}")
    rows: list[dict[str, object]] = []
    for asset in assets:
        path = ROOT / asset["path"]
        source = ROOT / asset["source_svg"]
        row: dict[str, object] = {
            "asset_id": asset["asset_id"],
            "path": asset["path"],
            "source_svg": asset["source_svg"],
            "source_svg_exists": source.is_file(),
            "source_svg_sha256": sha(source) if source.is_file() else None,
            "registry_sha256": asset["sha256"],
            "measured_sha256": sha(path),
            "declared_dimensions": [asset["width"], asset["height"]],
            "bytes": path.stat().st_size,
        }
        try:
            with Image.open(path) as image:
                row["pillow_header_dimensions"] = list(image.size)
                row["pillow_mode"] = image.mode
                image.load()
            row["pillow_full_decode"] = "passed"
        except Exception as exc:
            row["pillow_full_decode"] = "failed"
            row["pillow_error"] = f"{type(exc).__name__}:{exc}"
        command = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "null", "-"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
            row["ffmpeg_exit_code"] = result.returncode
            row["ffmpeg_error"] = result.stderr[-500:]
        except subprocess.TimeoutExpired as exc:
            row["ffmpeg_exit_code"] = None
            row["ffmpeg_error"] = "timeout_10s"
        row["status"] = "valid" if (
            row["source_svg_exists"] and row["measured_sha256"] == row["registry_sha256"]
            and row["pillow_full_decode"] == "passed" and row["ffmpeg_exit_code"] == 0
            and row.get("pillow_header_dimensions") == row["declared_dimensions"]
        ) else "invalid_decode"
        rows.append(row)
        print(f"[{len(rows)}/5] {asset['asset_id']}: {row['status']}", flush=True)
    report = {"schema_version": "phase1_freertos_asset_audit_v1", "registry_version": registry["registry_version"], "assets": rows}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
