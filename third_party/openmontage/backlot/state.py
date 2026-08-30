# Source: adapted from https://github.com/calesthio/OpenMontage/blob/cd9f3c1f03368be87b140af494914b8ee4e3c7a4/backlot/state.py
# Modified: validates and reads only the atomically published SQLite projection generation.
import json
import stat
from pathlib import Path, PurePosixPath
from typing import Any


def _is_link_or_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _read_object(path: Path, error: str) -> dict[str, Any]:
    if not path.is_file() or _is_link_or_reparse(path):
        raise ValueError(error)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(error) from exc
    if not isinstance(value, dict):
        raise ValueError(error)
    return value


def load_board_state(project_dir: Path | str) -> dict[str, Any]:
    project = Path(project_dir)
    if not project.is_dir() or _is_link_or_reparse(project):
        raise ValueError("projection_project_invalid")
    project_root = project.resolve()
    pointer = _read_object(project / "current.json", "projection_pointer_invalid")
    relative = pointer.get("generation")
    relative_path = PurePosixPath(relative) if isinstance(relative, str) else None
    if (
        relative_path is None
        or relative_path.is_absolute()
        or len(relative_path.parts) != 2
        or relative_path.parts[0] != "generations"
        or relative_path.parts[1] in {"", ".", ".."}
    ):
        raise ValueError("projection_pointer_invalid")
    generations_original = project / "generations"
    if not generations_original.is_dir() or _is_link_or_reparse(generations_original):
        raise ValueError("projection_pointer_invalid")
    generations = generations_original.resolve()
    selected_original = project / Path(*relative_path.parts)
    if _is_link_or_reparse(selected_original):
        raise ValueError("projection_pointer_invalid")
    generation = selected_original.resolve()
    try:
        generations.relative_to(project_root)
        generation.relative_to(project_root)
        generation.relative_to(generations)
    except ValueError as exc:
        raise ValueError("projection_pointer_invalid") from exc
    if not generation.is_dir() or _is_link_or_reparse(generation):
        raise ValueError("projection_pointer_invalid")
    value = _read_object(generation / "project.json", "projection_project_invalid")
    if (
        value.get("project_id") != project.name
        or value.get("state_authority") != "sqlite"
        or value.get("projection_only") is not True
    ):
        raise ValueError("projection_identity_invalid")
    return value
