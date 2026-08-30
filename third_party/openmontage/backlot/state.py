# Source: adapted from https://github.com/calesthio/OpenMontage/blob/cd9f3c1f03368be87b140af494914b8ee4e3c7a4/backlot/state.py
# Modified: read-only projected-state loader; all caches, watchers, and filesystem writes removed.
import json
from pathlib import Path
from typing import Any


def load_board_state(project_dir: Path | str) -> dict[str, Any]:
    project = Path(project_dir)
    path = project / "project.json"
    if not path.is_file():
        return {"project_id": project.name, "status": "unavailable", "state_authority": "factory_sqlite"}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"project_id": project.name, "status": "unreadable", "state_authority": "factory_sqlite"}
    return value if isinstance(value, dict) else {"project_id": project.name, "status": "unreadable"}
