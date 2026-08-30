"""Unit tests for the MoneyPrinterTurbo script-drafter adapter (mocked subprocess)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.phase1_mpt_script_drafter import (
    _parse_result_line,
    run_drafts,
)


def _cli_stdout(script: str) -> str:
    payload = json.dumps({"task_id": "t-1", "result": {"script": script}}, ensure_ascii=False)
    return f"logs...\n{payload}\n"


def test_parse_result_line_extracts_script() -> None:
    stdout = _cli_stdout("第一段。\n\n第二段。")
    assert _parse_result_line(stdout) == "第一段。\n\n第二段。"


def test_parse_result_line_returns_none_without_json() -> None:
    assert _parse_result_line("no json here") is None


def test_run_drafts_writes_candidates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scripts = iter(["候选一", "候选二"])

    def fake_run(*args, **kwargs):
        class Completed:
            returncode = 0
            stdout = _cli_stdout(next(scripts))
            stderr = ""

        return Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    out_root = tmp_path / "drafts"
    out_path = run_drafts(
        subject="看门狗",
        language="zh-CN",
        paragraphs=2,
        candidates=2,
        timeout_seconds=5,
        out_root=out_root,
    )
    document = json.loads(out_path.read_text(encoding="utf-8"))
    assert document["successful_candidates"] == 2
    assert document["review_status"] == "PENDING_HUMAN_REVIEW"
    assert [c["script"] for c in document["candidates"]] == ["候选一", "候选二"]
    assert document["failures"] == []
    assert out_path.parent.is_dir()


def test_run_drafts_fails_closed_when_all_candidates_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="cli.py", timeout=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="all candidates failed"):
        run_drafts(
            subject="看门狗",
            language="zh-CN",
            paragraphs=1,
            candidates=2,
            timeout_seconds=1,
            out_root=tmp_path / "drafts",
        )


def test_run_drafts_rejects_bad_inputs(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        run_drafts(
            subject=" ",
            language="zh-CN",
            paragraphs=1,
            candidates=1,
            timeout_seconds=1,
            out_root=tmp_path,
        )


def test_run_drafts_applies_rewrite_guidance_without_changing_output_subject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    commands = []
    def fake_run(command, **kwargs):
        commands.append(command)
        class Completed:
            returncode = 0
            stdout = _cli_stdout("改写候选")
            stderr = ""
        return Completed()
    monkeypatch.setattr(subprocess, "run", fake_run)
    out = run_drafts(subject="看门狗", language="zh-CN", paragraphs=2, candidates=1, timeout_seconds=5, out_root=tmp_path, rewrite_guidance="加强 hook 与 factual_consistency")
    document = json.loads(out.read_text(encoding="utf-8"))
    assert "加强 hook" in commands[0][commands[0].index("--video-subject") + 1]
    assert document["subject"] == "看门狗"
    with pytest.raises(ValueError):
        run_drafts(
            subject="x",
            language="zh-CN",
            paragraphs=1,
            candidates=0,
            timeout_seconds=1,
            out_root=tmp_path,
        )
