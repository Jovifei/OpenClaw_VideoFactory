from pathlib import Path
import os
import subprocess

import pytest
from fastapi.testclient import TestClient

from third_party.openmontage.backlot.server import create_app
from third_party.openmontage.backlot.state import load_board_state


def test_backlot_health_and_state_reads_do_not_write(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    project = projects / "job-safe"
    project.mkdir(parents=True)
    generation = project / "generations" / "g-safe"
    generation.mkdir(parents=True)
    (generation / "project.json").write_text(
        '{"project_id":"job-safe","state_authority":"sqlite","projection_only":true}', encoding="utf-8"
    )
    (project / "current.json").write_text('{"generation":"generations/g-safe"}', encoding="utf-8")
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


@pytest.mark.parametrize(
    "pointer",
    [
        '{"generation":"../outside"}',
        '{"generation":"generations/../../outside"}',
        '{"generation":"C:/outside"}',
    ],
)
def test_backlot_rejects_current_pointer_escape(tmp_path: Path, pointer: str) -> None:
    project = tmp_path / "job-safe"
    project.mkdir()
    (project / "current.json").write_text(pointer, encoding="utf-8")
    with pytest.raises(ValueError, match="projection_pointer_invalid"):
        load_board_state(project)


@pytest.mark.parametrize(
    "payload",
    [
        '{"project_id":"other","state_authority":"sqlite","projection_only":true}',
        '{"project_id":"job-safe","state_authority":"filesystem","projection_only":true}',
        '{"project_id":"job-safe","state_authority":"sqlite","projection_only":false}',
    ],
)
def test_backlot_rejects_spoofed_project_identity(tmp_path: Path, payload: str) -> None:
    project = tmp_path / "job-safe"
    generation = project / "generations" / "g-safe"
    generation.mkdir(parents=True)
    (project / "current.json").write_text('{"generation":"generations/g-safe"}', encoding="utf-8")
    (generation / "project.json").write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="projection_identity_invalid"):
        load_board_state(project)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_backlot_rejects_generations_directory_junction(tmp_path: Path) -> None:
    project = tmp_path / "job-safe"
    external = tmp_path / "outside-generations"
    generation = external / "g-safe"
    generation.mkdir(parents=True)
    project.mkdir()
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(project / "generations"), str(external)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("junction creation unavailable")
    (project / "current.json").write_text('{"generation":"generations/g-safe"}', encoding="utf-8")
    (generation / "project.json").write_text(
        '{"project_id":"job-safe","state_authority":"sqlite","projection_only":true}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="projection_pointer_invalid"):
        load_board_state(project)
