from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "acceptance_gate",
    ROOT / "scripts" / "90_acceptance_gate.py",
)
assert SPEC and SPEC.loader
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def result(stdout: object = "", returncode: int = 0) -> dict[str, object]:
    if not isinstance(stdout, str):
        stdout = json.dumps(stdout)
    return {
        "command": [],
        "returncode": returncode,
        "stdout": stdout,
        "stderr": "",
    }


class P0GateV25Tests(unittest.TestCase):
    def runtime_result(self, command: list[str], timeout: int = 60) -> dict[str, object]:
        joined = " ".join(command)
        if "agents list" in joined:
            return result(
                [
                    {
                        "id": "video-factory",
                        "workspace": str(ROOT),
                    }
                ]
            )
        if "cron list" in joined:
            return result({"jobs": []})
        if "skills check" in joined:
            return result("\n".join(sorted(GATE.REQUIRED_SKILLS)))
        if command[0] == "nvidia-smi":
            return result("NVIDIA GeForce RTX 4070 SUPER, 12282 MiB")
        if command[0] == "ffmpeg" and "-encoders" in command:
            return result("h264_nvenc")
        return result("ok")

    def evidence(self, name: str) -> dict[str, object]:
        if name == "FEISHU_SMOKE_TEST.json":
            return {
                "checks": [
                    {
                        "name": "inbound text and visible bot reply",
                        "passed": True,
                    }
                ]
            }
        if name == "FEISHU_SINGLE_CONSUMER_TEST.json":
            return {
                "schema_version": "2.5",
                "passed": True,
                "checks": [
                    {"id": "feishu_single_consumer", "passed": True},
                    {"id": "feishu_deduplication", "passed": True},
                ],
            }
        if name in {"P0_SAFE_INGRESS_EVIDENCE_079.json", "FEISHU_INGRESS_TEST.json"}:
            return {
                "version": "2.5",
                "passed": True,
                "checks": [
                    {"id": item, "passed": True}
                    for item in (
                        "txt_ingress",
                        "png_ingress",
                        "mp4_ingress",
                        "safe_media_ingest",
                    )
                ],
            }
        if name == "FEISHU_EGRESS_TEST.json":
            return {
                "version": "2.5",
                "passed": True,
                "checks": [
                    {"id": item, "passed": True}
                    for item in (
                        "lark_cli_markdown_egress",
                        "lark_cli_png_egress",
                        "lark_cli_txt_egress",
                        "lark_cli_mp4_egress",
                        "egress_idempotency",
                    )
                ],
            }
        if name == "CODEX_CLI_SMOKE.json":
            return {
                "version": "2.5",
                "passed": True,
                "checks": [
                    {"id": item, "passed": True}
                    for item in (
                        "direct_codex_cli_read",
                        "direct_codex_cli_workspace_write",
                        "workspace_isolation",
                    )
                ],
            }
        if name in {
            "P0_AGENT_BINDING_REGRESSION_077.json",
            "OPENCLAW_EXISTING_AGENTS_REGRESSION.json",
        }:
            return {
                "schema_version": "2.5",
                "passed": True,
                "checks": [
                    {"id": "existing_agents_regression", "passed": True},
                    {"id": "bindings_regression", "passed": True},
                ],
            }
        return {"schema_version": "2.5", "passed": True}

    def test_v25_p0_excludes_plugin_oauth_and_codex_slash_commands(self) -> None:
        with (
            patch.object(GATE, "package_checks", return_value=[]),
            patch.object(GATE, "run", side_effect=self.runtime_result),
            patch.object(GATE, "evidence_json", side_effect=self.evidence),
        ):
            checks = GATE.p0_checks()

        names = {check["name"] for check in checks}
        self.assertNotIn("Codex runtime evidence", names)
        self.assertNotIn("/codex status", names)
        self.assertNotIn("/codex models", names)
        self.assertIn("direct Codex CLI smoke", names)
        self.assertIn("no VideoFactory production Cron", names)
        self.assertTrue(all(check["passed"] for check in checks))

    def test_old_or_partial_ingress_evidence_fails_closed(self) -> None:
        def partial_evidence(name: str) -> dict[str, object]:
            if name in {"P0_SAFE_INGRESS_EVIDENCE_079.json", "FEISHU_INGRESS_TEST.json"}:
                return {"passed": True, "checks": []}
            return self.evidence(name)

        with (
            patch.object(GATE, "package_checks", return_value=[]),
            patch.object(GATE, "run", side_effect=self.runtime_result),
            patch.object(GATE, "evidence_json", side_effect=partial_evidence),
        ):
            checks = GATE.p0_checks()

        ingress = {
            check["name"]: check["passed"]
            for check in checks
            if "ingress" in check["name"] or "receipt/hash" in check["name"]
        }
        self.assertTrue(ingress["Feishu text ingress"])
        self.assertFalse(ingress["Feishu TXT ingress"])
        self.assertFalse(ingress["Feishu PNG ingress"])
        self.assertFalse(ingress["Feishu MP4 ingress"])
        self.assertFalse(ingress["safe media receipt/hash/quarantine"])

    def test_video_factory_cron_is_rejected(self) -> None:
        self.assertTrue(GATE.is_video_factory_cron({"agentId": "video-factory"}))
        self.assertTrue(
            GATE.is_video_factory_cron(
                {"payload": {"message": "Run E:/project/OpenClaw_VideoFactory"}}
            )
        )
        self.assertFalse(GATE.is_video_factory_cron({"agentId": "main", "name": "weather"}))

    def test_single_consumer_requires_deduplication(self) -> None:
        evidence = {
            "schema_version": "2.5",
            "passed": True,
            "checks": [{"id": "feishu_single_consumer", "passed": True}],
        }
        self.assertTrue(GATE.evidence_is_v25_passed(evidence))
        self.assertTrue(GATE.named_evidence_passed(evidence, "feishu_single_consumer"))
        self.assertFalse(GATE.named_evidence_passed(evidence, "feishu_deduplication"))

    def test_agent_binding_public_evidence_has_legacy_fallback(self) -> None:
        def legacy_only(name: str) -> dict[str, object] | None:
            if name == "P0_AGENT_BINDING_REGRESSION_077.json":
                return None
            return self.evidence(name)

        with (
            patch.object(GATE, "package_checks", return_value=[]),
            patch.object(GATE, "run", side_effect=self.runtime_result),
            patch.object(GATE, "evidence_json", side_effect=legacy_only),
        ):
            checks = GATE.p0_checks()

        current = {check["name"]: check["passed"] for check in checks}
        self.assertTrue(current["existing agents/bindings regression"])

    def test_dry_run_does_not_satisfy_actual_egress(self) -> None:
        evidence = {
            "schema_version": "2.5",
            "passed": True,
            "checks": [{"id": "dry_run", "passed": True}],
        }
        for check_id in (
            "lark_cli_markdown_egress",
            "lark_cli_png_egress",
            "lark_cli_txt_egress",
            "lark_cli_mp4_egress",
            "egress_idempotency",
        ):
            self.assertFalse(GATE.named_evidence_passed(evidence, check_id))


if __name__ == "__main__":
    unittest.main()
