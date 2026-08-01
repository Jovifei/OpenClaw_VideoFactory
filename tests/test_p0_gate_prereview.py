from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "p0_gate_prereview.py"
SPEC = importlib.util.spec_from_file_location("p0_gate_prereview", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def named_evidence(*names: str) -> dict:
    return {
        "schema_version": "2.5",
        "passed": True,
        "checks": [{"id": name, "passed": True} for name in names],
    }


def prepare_repo(tmp_path: Path) -> Path:
    for item in (
        "START_HERE_CODEX.md",
        "PROJECT_STATUS.yaml",
        "AGENTS.md",
        "SHA256SUMS.txt",
    ):
        (tmp_path / item).write_text("", encoding="utf-8")
    for directory in ("skills", "config", "scripts", "runbook", "handoff", "reports"):
        (tmp_path / directory).mkdir()
    (tmp_path / "scripts" / "factory.py").write_text(
        "OpenClaw VideoFactory production pipeline is not implemented yet.",
        encoding="utf-8",
    )
    return tmp_path


def write_real_baseline(reports: Path, *, r3: str) -> None:
    write_json(
        reports / "P0_LIVE_EVENT_TRACE_R0_R5.json",
        {
            "r0": {"status": "passed"},
            "r1_replacement": {"status": "passed"},
            "r2_replacement": {"status": "passed"},
        },
    )
    write_json(
        reports / "P0_REAL_R3_IMAGE_VERIFICATION_054A.json",
        {"verdict": r3},
    )


def write_acceptance_pass(reports: Path) -> None:
    write_json(
        reports / "FEISHU_SMOKE_TEST.json",
        {"passed": True, "checks": [{"id": "text_ingress", "passed": True}]},
    )
    write_json(
        reports / "FEISHU_SINGLE_CONSUMER_TEST.json",
        named_evidence("feishu_single_consumer", "feishu_deduplication"),
    )
    write_json(
        reports / "FEISHU_INGRESS_TEST.json",
        named_evidence("txt_ingress", "png_ingress", "mp4_ingress", "safe_media_ingest"),
    )
    write_json(
        reports / "FEISHU_EGRESS_TEST.json",
        named_evidence(
            "lark_cli_markdown_egress",
            "lark_cli_png_egress",
            "lark_cli_txt_egress",
            "lark_cli_mp4_egress",
            "egress_idempotency",
        ),
    )
    write_json(
        reports / "CODEX_CLI_SMOKE.json",
        named_evidence(
            "direct_codex_cli_read",
            "direct_codex_cli_workspace_write",
            "workspace_isolation",
        ),
    )
    write_json(
        reports / "OPENCLAW_EXISTING_AGENTS_REGRESSION.json",
        named_evidence("existing_agents_regression", "bindings_regression"),
    )
    write_json(reports / "SKILL_VISIBILITY.json", {"passed": True})


class P0GatePrereviewTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return prepare_repo(Path(temporary.name))

    def test_v25_contract_rejects_old_or_partial_evidence(self) -> None:
        self.assertTrue(MODULE.is_v25_passed(named_evidence("x")))
        self.assertFalse(MODULE.is_v25_passed({"schema_version": "1.0", "passed": True}))
        self.assertTrue(MODULE.named_check_passed(named_evidence("x"), "x"))
        self.assertFalse(MODULE.named_check_passed(named_evidence("x"), "missing"))

    def test_partial_r3_is_the_next_action(self) -> None:
        repo = self.make_repo()
        write_real_baseline(
            repo / "reports",
            r3="R3_PARTIAL_PASS:RESULT_REPLY_TOO_THIN",
        )
        report = MODULE.build_report(repo, include_runtime=False)
        self.assertFalse(report["can_start_p1"])
        self.assertEqual(report["next_action"], "RUN_FRESH_REAL_R3_RETEST")

    def test_r3_pass_moves_to_r4(self) -> None:
        repo = self.make_repo()
        write_real_baseline(repo / "reports", r3="R3_IMAGE_ANALYSIS_OK")
        report = MODULE.build_report(repo, include_runtime=False)
        self.assertEqual(
            report["next_action"],
            "RUN_REAL_R4_AUDIO_AFTER_R3_PASS",
        )

    def test_media_sequence_moves_to_acceptance_evidence(self) -> None:
        repo = self.make_repo()
        reports = repo / "reports"
        write_real_baseline(reports, r3="R3_IMAGE_ANALYSIS_OK")
        write_json(
            reports / "P0_REAL_R4_AUDIO_QUALIFICATION_057.json",
            {"verdict": "R4_AUDIO_ANALYSIS_OK"},
        )
        write_json(
            reports / "P0_REAL_R5_VIDEO_QUALIFICATION_058.json",
            {"verdict": "R5_VIDEO_ANALYSIS_OK"},
        )
        report = MODULE.build_report(repo, include_runtime=False)
        self.assertTrue(report["next_action"].startswith("REMEDIATE_P0_EVIDENCE:"))

    def test_current_media_reports_use_their_actual_outcome_fields(self) -> None:
        repo = self.make_repo()
        reports = repo / "reports"
        write_real_baseline(reports, r3="R3_PARTIAL_PASS:RESULT_REPLY_TOO_THIN")
        write_json(reports / "P0_REAL_R3_RETEST_061.json", {"result": "R3_IMAGE_ANALYSIS_OK"})
        write_json(reports / "P0_R4_AUDIO_QUALIFICATION_073.json", {"qualification": "R4_AUDIO_ANALYSIS_OK"})
        write_json(
            reports / "P0_R5_VIDEO_QUALIFICATION_072.json",
            {"qualification": "PASS_REAL_VISIBLE_COMPLETION"},
        )

        checks = MODULE.media_sequence_checks(reports)
        current = {check["name"]: check for check in checks}
        self.assertEqual(current["real media R3 image result"]["status"], "passed")
        self.assertEqual(current["real media R4 audio result"]["status"], "passed")
        self.assertEqual(current["real media R5 video result"]["status"], "passed")
        self.assertEqual(current["real media R5 video result"]["detail"]["source"], "P0_R5_VIDEO_QUALIFICATION_072.json")

    def test_p1_requires_explicit_p0_ready_artifact(self) -> None:
        repo = self.make_repo()
        reports = repo / "reports"
        write_real_baseline(reports, r3="R3_IMAGE_ANALYSIS_OK")
        write_json(
            reports / "P0_REAL_R4_AUDIO_QUALIFICATION_057.json",
            {"verdict": "R4_AUDIO_ANALYSIS_OK"},
        )
        write_json(
            reports / "P0_REAL_R5_VIDEO_QUALIFICATION_058.json",
            {"verdict": "R5_VIDEO_ANALYSIS_OK"},
        )
        write_acceptance_pass(reports)

        before_gate = MODULE.build_report(repo, include_runtime=False)
        self.assertFalse(before_gate["can_start_p1"])
        self.assertEqual(
            before_gate["next_action"],
            "RUN_ACTUAL_P0_ACCEPTANCE_GATE",
        )

        write_json(reports / "gates" / "P0_READY.json", {"passed": True})
        after_gate = MODULE.build_report(repo, include_runtime=False)
        self.assertTrue(after_gate["can_start_p1"])
        self.assertEqual(after_gate["next_action"], "START_P1_A_SQLITE_STATE_STORE")


if __name__ == "__main__":
    unittest.main()
