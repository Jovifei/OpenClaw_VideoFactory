"""Deterministic mascot asset staging and visual review sheet generation."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import PROJECT_ROOT


POSES = ("normal", "question", "warning", "thinking", "repair", "measure", "success", "ending")
ASSET_ROOT = PROJECT_ROOT / "src" / "factory" / "assets" / "mascot"
CONTACT_SHEET_TIMEOUT_SECONDS = 30


def ensure_public_assets(public_root: Path) -> None:
    target = public_root / "mascot"
    target.mkdir(parents=True, exist_ok=True)
    for pose in POSES:
        source = ASSET_ROOT / f"{pose}.svg"
        if not source.exists():
            raise RuntimeError(f"mascot_asset_missing:{pose}")
        shutil.copy2(source, target / source.name)


def _contact_sheet_chrome_command(chrome: Path, profile: Path, target: Path, page: Path) -> list[str]:
    return [
        str(chrome),
        "--headless=new",
        "--use-gl=angle",
        "--use-angle=swiftshader",
        "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--no-first-run",
        f"--user-data-dir={profile}",
        "--window-size=1360,780",
        f"--screenshot={target}",
        page.as_uri(),
    ]


def _safe_browser_diagnostic(output: str, temp: Path) -> str:
    lines = output.strip().splitlines()
    if not lines:
        return "no_browser_output"
    last_line = lines[-1]
    if "file:" in last_line.lower() or str(temp).lower() in last_line.lower() or "\\" in last_line:
        return "local_path_redacted"
    return last_line[:160]


def create_contact_sheet(target: Path) -> None:
    """Rasterize local SVGs with installed Chrome; no network or model input."""
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p1-mascot-") as temp_dir:
        temp = Path(temp_dir)
        cards = "".join(
            f'<figure><img src="{(ASSET_ROOT / (pose + ".svg")).as_uri()}"/><figcaption>{pose}</figcaption></figure>'
            for pose in POSES
        )
        page = temp / "contact-sheet.html"
        page.write_text(
            f"<html><style>body{{margin:0;background:#f7f5f1;font-family:Arial;color:#172033}}main{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:20px}}figure{{margin:0;background:#fff;border-radius:16px;text-align:center}}img{{width:300px;height:300px}}figcaption{{padding:8px;font-weight:bold}}</style><body><main>{cards}</main></body></html>",
            encoding="utf-8",
        )
        chrome = next(
            (
                path
                for path in (
                    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
                    Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
                )
                if path.exists()
            ),
            None,
        )
        if chrome is None:
            raise RuntimeError("local_chrome_required")
        try:
            result = subprocess.run(
                _contact_sheet_chrome_command(chrome, temp / "chrome-profile", target, page),
                text=True,
                capture_output=True,
                check=False,
                timeout=CONTACT_SHEET_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("mascot_contact_sheet_timeout") from exc
        if result.returncode != 0 or not target.exists():
            raise RuntimeError(
                "mascot_contact_sheet_failed:"
                f"{result.returncode}:{_safe_browser_diagnostic(result.stderr or result.stdout, temp)}"
            )
