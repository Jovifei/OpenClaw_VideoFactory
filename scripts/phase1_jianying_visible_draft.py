"""Expose an E-drive Jianying draft through the desktop application's projects root.

The project data stays on E:. The only C: write is a non-overwriting NTFS
directory junction that the Jianying desktop app can enumerate as a draft.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def _contains(root: Path, child: Path) -> bool:
    try:
        return os.path.commonpath([str(root.resolve()), str(child.resolve())]) == str(root.resolve())
    except ValueError:
        return False


def validate_visible_draft_paths(source_draft: Path, app_drafts_root: Path, name: str) -> Path:
    if source_draft.drive.upper() != "E:":
        raise ValueError("source_draft_must_be_e_drive")
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("visible_target_outside_app_root")
    target = (app_drafts_root.resolve() / name).resolve()
    if not _contains(app_drafts_root, target):
        raise ValueError("visible_target_outside_app_root")
    if target.drive.upper() != "C:":
        raise ValueError("app_projects_root_must_be_c_drive")
    return target


def _is_reparse_point(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["fsutil", "reparsepoint", "query", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except OSError:
        return False
    return result.returncode == 0


def is_valid_jianying_draft_layout(path: Path) -> bool:
    return path.is_dir() and any((path / filename).is_file() for filename in ("draft_content.json", "draft_info.json"))


def create_visible_junction(source_draft: Path, app_drafts_root: Path, name: str) -> dict[str, object]:
    source = source_draft.resolve()
    target = validate_visible_draft_paths(source, app_drafts_root, name)
    if not is_valid_jianying_draft_layout(source):
        raise ValueError("source_draft_invalid")
    app_drafts_root.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(target):
        raise ValueError("visible_target_already_exists")
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(target), str(source)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0 or not target.is_dir() or not _is_reparse_point(target):
        raise ValueError("visible_junction_create_failed")
    return {
        "status": "visible_junction_ready",
        "source_draft": str(source),
        "visible_draft": str(target),
        "source_drive": source.drive.upper(),
        "visible_index_drive": target.drive.upper(),
        "source_media_copied_to_c": False,
        "junction_verified": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-draft", required=True, type=Path)
    parser.add_argument("--app-drafts-root", required=True, type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.resolve().drive.upper() == "C:":
        print(json.dumps({"status": "failed", "reason": "report_must_not_use_c_drive"}, ensure_ascii=False))
        return 1
    try:
        result = create_visible_junction(args.source_draft, args.app_drafts_root, args.name)
    except Exception as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, ensure_ascii=False))
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
