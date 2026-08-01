"""Offline proof tests for P0 Shadow Feishu plugin lifecycle 033."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SHADOW = ROOT / "experiments" / "core_feishu_control_contract" / "shadow"
SCRIPTS = ROOT / "scripts" / "migration" / "core_feishu_control"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoreFeishuPluginLifecycle033Tests(unittest.TestCase):
    def test_01_change_request_and_reports(self):
        self.assertTrue(
            (REPORTS / "change_requests" / "P0-SHADOW-FEISHU-PLUGIN-LIFECYCLE-033.json").is_file()
        )
        for name in (
            "P0_FEISHU_PLUGIN_ORIGIN_AUDIT_033.json",
            "P0_SHADOW_PLUGIN_LOAD_ROOT_CAUSE_033.json",
            "P0_SHADOW_FEISHU_PLUGIN_LIFECYCLE_033.json",
            "P0_SHADOW_FEISHU_PLUGIN_RUNTIME_PROOF_033.json",
        ):
            self.assertTrue((REPORTS / name).is_file(), name)

    def test_02_origin_hashes(self):
        origin = _json(REPORTS / "P0_FEISHU_PLUGIN_ORIGIN_AUDIT_033.json")["plugin"]
        lifecycle = _json(REPORTS / "P0_SHADOW_FEISHU_PLUGIN_LIFECYCLE_033.json")["plugin"]
        self.assertEqual(origin["manifest_sha256"], lifecycle["manifest_sha256"])
        self.assertEqual(origin["runtime_entry_sha256"], lifecycle["runtime_entry_sha256"])

    def test_03_shadow_lifecycle(self):
        result = _json(SHADOW / "lifecycle-result.json")
        self.assertTrue(result["shadow_only"])
        self.assertTrue(result["plugin_list_feishu_seen"])
        self.assertTrue(result["gateway_ready"])
        self.assertEqual(result["config_validate_exit"], 0)
        self.assertTrue(result["config_validate_json"])
        self.assertEqual(result["plugin_list_exit"], 0)
        self.assertTrue(result["process_shutdown"])
        self.assertEqual(result["gateway_exit"], 1)
        calls = result["calls"]
        for name in ("start", "start_repeat", "start_after_stop"):
            self.assertTrue(calls[name]["started"], name)
        for name in ("stop", "stop_repeat", "stop_final"):
            self.assertTrue(calls[name]["stopped"], name)
        self.assertTrue(calls["status_after_start"]["account_states"]["zhongshu"]["running"])
        self.assertFalse(calls["status_after_stop"]["account_states"]["zhongshu"]["running"])
        for status in (
            calls["status_after_start"],
            calls["status_after_stop"],
            calls["status_after_restart"],
        ):
            self.assertFalse(status["account_states"]["shadow-secondary"]["running"])
        self.assertEqual(calls["shutdown_preflight"]["exit"], 0)
        self.assertTrue(calls["shutdown_preflight"]["json"])
        self.assertTrue(calls["shutdown_preflight"]["safe"])
        self.assertEqual(calls["shutdown_preflight"]["counts"]["totalActive"], 0)

    def test_04_transport(self):
        result = _json(SHADOW / "lifecycle-result.json")
        guard = result["transport_guard"]
        fake = result["fake_transport"]
        self.assertTrue(guard["loopback_only"])
        self.assertEqual(guard["unexpected_network_access"], 0)
        self.assertFalse(guard["duplicate_connect_detected"])
        self.assertGreaterEqual(guard["process_count"], 1)
        self.assertGreaterEqual(guard["gateway_process_count"], 1)
        self.assertEqual(guard["gateway_unexpected_network_access"], 0)
        self.assertEqual(fake["connect_count"], fake["close_count"])
        self.assertEqual(fake["active_connections"], 0)
        self.assertFalse(fake["duplicate_connect_detected"])

    def test_05_evaluators_pass(self):
        result = _json(SHADOW / "lifecycle-result.json")
        preflight = _load("preflight_033", SCRIPTS / "preflight.py")
        postcheck = _load("postcheck_033", SCRIPTS / "postcheck.py")
        self.assertEqual(preflight.evaluate(result)["status"], "PASS")
        self.assertEqual(postcheck.evaluate(result)["status"], "PASS")

    def test_06_execute_is_rejected(self):
        result_path = SHADOW / "lifecycle-result.json"
        for script in ("preflight.py", "postcheck.py"):
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / script),
                    "--shadow-result",
                    str(result_path),
                    "--execute",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2, script)
            self.assertIn("PRODUCTION_EXECUTION_DISABLED_033", completed.stdout)

    def test_07_no_production_execution_marker(self):
        lifecycle = _json(REPORTS / "P0_SHADOW_FEISHU_PLUGIN_LIFECYCLE_033.json")
        self.assertEqual(lifecycle["execution"], "SHADOW_ONLY_NOT_PRODUCTION")


if __name__ == "__main__":
    unittest.main()
