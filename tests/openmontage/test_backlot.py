from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from third_party.openmontage.backlot.server import create_app
from third_party.openmontage.backlot.state import load_board_state


def test_backlot_health_and_state_reads_do_not_write(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    project = projects / "job-safe"
    project.mkdir(parents=True)
    (project / "project.json").write_text('{"project_id":"job-safe"}', encoding="utf-8")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    app = create_app(projects_root=projects)
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"ok": True, "app": "backlot-read-only"}
        assert client.get("/api/project/job-safe/state").status_code == 200
    assert load_board_state(project)["project_id"] == "job-safe"
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_backlot_rejects_path_traversal_and_defaults_to_loopback(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    (projects / "safe").mkdir(parents=True)
    app = create_app(projects_root=projects)
    assert app.state.default_host == "127.0.0.1"
    with TestClient(app) as client:
        assert client.get("/api/project/%2e%2e/state").status_code in {400, 404}
        assert client.get("/api/project/C%3A/state").status_code == 400


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "127.0.0.2"])
def test_backlot_rejects_every_noncanonical_bind_host(tmp_path: Path, host: str) -> None:
    with pytest.raises(ValueError, match="backlot_loopback_host_required"):
        create_app(projects_root=tmp_path, default_host=host)
