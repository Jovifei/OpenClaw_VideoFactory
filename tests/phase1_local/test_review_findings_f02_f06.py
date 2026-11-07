"""Regression tests for remote static review findings F02-F06 (PR #2 / 10679a1).

Each test reproduces the exact attack the reviewer described and asserts the
fail-closed error code. All cases are offline and use synthetic artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.phase1_mpt_script_drafter import _parse_result_line, run_drafts
from src.factory import phase1_cli
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.export import write_json

from tests.phase1_local.test_phase1_subject_cli import (
    MPT_COMMIT,
    _configure,
    _output,
    _research,
)


def _fake_run_drafts(tmp_path: Path):
    def fake_run_drafts(**kwargs):
        output = tmp_path / "mpt.json"
        output.write_text(json.dumps({"schema_version": "1.0", "kind": "phase1_script_drafts",
                                      "subject": "看门狗", "language": "zh-CN",
                                      "requested_candidates": 3, "successful_candidates": 3,
                                      "mpt_version": "1.3.5", "mpt_commit": MPT_COMMIT,
                                      "candidates": [{"candidate": i, "script": "看门狗发生故障：看门狗检测失去响应，超时需验证。再解释原理、配置和恢复边界。", "duration_seconds": 1} for i in range(1, 4)],
                                      "failures": []}, ensure_ascii=False), encoding="utf-8")
        return output
    return fake_run_drafts


def test_persist_brief_rejects_dangling_symlink(tmp_path, monkeypatch) -> None:
    """Windows denies unprivileged file symlinks, so drive the seam instead:
    force the persisted path to report itself as a link and expect rejection
    before any content comparison (the dangling case the reviewer described)."""
    _configure(tmp_path, monkeypatch)
    brief = {"topic": "看门狗", "input_mode": "topic"}
    target = phase1_cli.INPUT_ROOT / f"{phase1_cli._request_digest(brief)}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    real_is_symlink = Path.is_symlink

    def fake_is_symlink(self: Path) -> bool:
        return self == target or real_is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    with pytest.raises(FactoryContractError) as exc:
        phase1_cli._persist_brief(brief)
    assert exc.value.code == "phase1_input_path_invalid"


def test_write_json_rejects_symlink_path(tmp_path, monkeypatch) -> None:
    link = tmp_path / "link.json"
    real_is_symlink = Path.is_symlink

    def fake_is_symlink(self: Path) -> bool:
        return self == link or real_is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    with pytest.raises(ValueError, match="symlink"):
        write_json(link, {"a": 1})


def test_attach_research_is_closed_after_planning(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(outside)]) == 0
    capsys.readouterr()
    monkeypatch.setattr(phase1_cli, "MPT_RUN_DRAFTS", _fake_run_drafts(tmp_path))
    assert phase1_cli.main(["run", "--job-id", job_id, "--plan-only"]) == 0
    capsys.readouterr()
    late = tmp_path / "late.json"
    late.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(late)]) == 2
    assert _output(capsys)["error"]["code"] == "phase1_research_attach_closed"


def test_assets_plan_only_rejects_damaged_snapshot(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(outside)]) == 0
    capsys.readouterr()
    monkeypatch.setattr(phase1_cli, "MPT_RUN_DRAFTS", _fake_run_drafts(tmp_path))
    assert phase1_cli.main(["run", "--job-id", job_id, "--plan-only"]) == 0
    capsys.readouterr()
    job = phase1_cli._store().status(job_id)
    scene_plan = phase1_cli._subject_plan_root(job) / "scene_plan.json"
    payload = json.loads(scene_plan.read_text(encoding="utf-8"))
    payload["tampered"] = True
    scene_plan.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["run", "--job-id", job_id, "--plan-only"]) == 2
    assert _output(capsys)["error"]["code"] == "phase1_subject_plan_artifact_invalid"


def test_topic_run_rejects_edited_brief(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    repo_brief = Path(__file__).resolve().parents[2] / "examples" / "phase1_local_modbus" / "brief.json"
    assert phase1_cli.main(["create-topic", "--brief", str(repo_brief)]) == 0
    job = _output(capsys)["job"]
    job_id = job["job_id"]
    brief_path = tmp_path / str(job["metadata"]["brief_path"])
    payload = json.loads(brief_path.read_text(encoding="utf-8"))
    payload["duration_target_seconds"] = int(payload.get("duration_target_seconds", 40)) + 5
    brief_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["run", "--job-id", job_id]) == 2
    assert _output(capsys)["error"]["code"] == "phase1_input_digest_conflict"


def test_drafter_output_dirs_are_unique_within_one_second(tmp_path, monkeypatch) -> None:
    calls: list[Path] = []

    def fake_run(*args, **kwargs):
        class Completed:
            returncode = 0
            stdout = _parse_result_line.__globals__["json"].dumps(
                {"task_id": "t", "result": {"script": "候选"}}, ensure_ascii=False
            )
            stderr = ""

        return Completed()

    monkeypatch.setattr("scripts.phase1_mpt_script_drafter.subprocess.run", fake_run)
    monkeypatch.setattr("scripts.phase1_mpt_script_drafter.time.strftime", lambda fmt: "20261107_120000")
    first = run_drafts(subject="看门狗", language="zh-CN", paragraphs=1, candidates=1,
                       timeout_seconds=5, out_root=tmp_path)
    second = run_drafts(subject="看门狗", language="zh-CN", paragraphs=1, candidates=1,
                        timeout_seconds=5, out_root=tmp_path)
    calls = [first.parent, second.parent]
    assert calls[0] != calls[1]
    assert first.is_file() and second.is_file()


def test_drafter_retries_colliding_directory(tmp_path, monkeypatch) -> None:
    """A same-second collision on mkdir must retry instead of failing."""

    def fake_run(*args, **kwargs):
        class Completed:
            returncode = 0
            stdout = json.dumps({"task_id": "t", "result": {"script": "候选"}}, ensure_ascii=False)
            stderr = ""

        return Completed()

    import scripts.phase1_mpt_script_drafter as drafter

    monkeypatch.setattr("scripts.phase1_mpt_script_drafter.subprocess.run", fake_run)
    monkeypatch.setattr(drafter.time, "strftime", lambda fmt: "20261107_120000")

    class FakeUUID:
        def __init__(self, hex_value: str) -> None:
            self.hex = hex_value

    seq = iter(["a" * 12, "a" * 12, "b" * 12])
    monkeypatch.setattr(drafter, "uuid4", lambda: FakeUUID(next(seq)))
    # Pre-occupy the directory the first attempt will claim: the exclusive
    # mkdir must collide, retry, and reserve the second unique name.
    (tmp_path / f"drafter_20261107_120000_{'a' * 12}").mkdir(parents=True)
    out = run_drafts(subject="看门狗", language="zh-CN", paragraphs=1, candidates=1,
                     timeout_seconds=5, out_root=tmp_path)
    assert out.parent.name.endswith("_" + "b" * 12)
