# Source: adapted from https://github.com/calesthio/OpenMontage/blob/cd9f3c1f03368be87b140af494914b8ee4e3c7a4/backlot/server.py
# Modified: health and state API only; loopback default; no watcher, thumbnails, cache, UI, or write routes.
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .state import load_board_state


def create_app(*, projects_root: Path | str, default_host: str = "127.0.0.1") -> FastAPI:
    if default_host != "127.0.0.1":
        raise ValueError("backlot_loopback_host_required")
    root = Path(projects_root).resolve()
    app = FastAPI(title="Backlot read-only", docs_url=None, redoc_url=None)
    app.state.default_host = default_host

    def safe_project(project_id: str) -> Path:
        if not project_id or project_id in {".", ".."} or any(char in project_id for char in "/\\:"):
            raise HTTPException(status_code=400, detail="invalid project id")
        candidate = (root / project_id).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise HTTPException(status_code=403, detail="path escapes projects root") from exc
        if not candidate.is_dir():
            raise HTTPException(status_code=404, detail="unknown project")
        return candidate

    @app.get("/api/health")
    async def health() -> dict[str, object]:
        return {"ok": True, "app": "backlot-read-only"}

    @app.get("/api/project/{project_id}/state")
    async def project_state(project_id: str) -> dict[str, object]:
        return load_board_state(safe_project(project_id))

    return app
