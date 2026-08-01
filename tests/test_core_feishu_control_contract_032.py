"""Offline contract checks for P0 control audit 032.

These tests never call a production Gateway or Feishu. They assert the
fail-closed evidence contract and the installed-source signatures discovered
by the parent audit.
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
EXPERIMENT = ROOT / "experiments" / "core_feishu_control_contract"


def _dist() -> Path:
    appdata = os.environ.get("APPDATA")
    roaming = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return roaming / "npm" / "node_modules" / "openclaw" / "dist"


def _read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def _source(name: str) -> str:
    matches = list(_dist().glob(name))
    return matches[0].read_text(encoding="utf-8") if matches else ""


class CoreFeishuControl032Tests(unittest.TestCase):
    def test_00_dist_resolves_appdata_or_current_user_roaming_path(self):
        expected = Path("C:/fixture-appdata") / "npm" / "node_modules" / "openclaw" / "dist"
        with patch.dict(os.environ, {"APPDATA": "C:/fixture-appdata"}, clear=True):
            self.assertEqual(_dist(), expected)
        expected = Path("C:/fixture-home/AppData/Roaming/npm/node_modules/openclaw/dist")
        with patch.dict(os.environ, {}, clear=True), patch.object(
            Path, "home", return_value=Path("C:/fixture-home")
        ):
            self.assertEqual(_dist(), expected)

    def test_01_change_request_exists(self):
        self.assertTrue(
            (
                REPORTS / "change_requests" / "P0-CORE-FEISHU-CONTROL-CONTRACT-RESOLUTION-032.json"
            ).is_file()
        )

    def test_02_change_request_prohibits_production(self):
        cr = _read_json("change_requests/P0-CORE-FEISHU-CONTROL-CONTRACT-RESOLUTION-032.json")
        self.assertTrue(any("production" in item for item in cr["prohibited_actions"]))

    def test_03_audit_status_blocked(self):
        self.assertEqual(
            _read_json("P0_OPENCLAW_CORE_FEISHU_CONTROL_AUDIT_032.json")["status"],
            "CORE_FEISHU_SHADOW_VALIDATION_BLOCKED",
        )

    def test_04_contract_status_blocked(self):
        self.assertEqual(
            _read_json("P0_CORE_FEISHU_CONTROL_CONTRACT_032.json")["status"],
            "CORE_FEISHU_SHADOW_VALIDATION_BLOCKED",
        )

    def test_05_static_method_account_scope(self):
        self.assertEqual(
            _read_json("P0_CORE_FEISHU_CONTROL_CONTRACT_032.json")["static_control_contract"],
            "ACCOUNT_LEVEL_DISABLE",
        )

    def test_06_no_production_execution(self):
        self.assertFalse(
            _read_json("P0_CORE_FEISHU_CONTROL_CONTRACT_032.json")["production_execution"]
        )

    def test_07_no_real_feishu(self):
        self.assertFalse(_read_json("P0_CORE_FEISHU_CONTROL_CONTRACT_032.json")["real_feishu"])

    def test_08_scripts_not_created_before_shadow_proof(self):
        self.assertFalse(_read_json("P0_CORE_FEISHU_CONTROL_CONTRACT_032.json")["scripts_created"])

    def test_09_config_diff_is_shadow_only(self):
        self.assertEqual(
            _read_json("P0_CORE_FEISHU_CONTROL_CONFIG_DIFF_032.json")["scope"],
            "shadow_fixture_only",
        )

    def test_10_config_diff_has_no_secret(self):
        diff = _read_json("P0_CORE_FEISHU_CONTROL_CONFIG_DIFF_032.json")
        self.assertFalse(diff["secret_values_written"])

    def test_11_shadow_probe_exists(self):
        self.assertTrue((EXPERIMENT / "shadow_gateway_probe.py").is_file())

    def test_12_shadow_probe_requires_plugin_env(self):
        self.assertIn(
            "OPENCLAW_FEISHU_PLUGIN_ROOT",
            (EXPERIMENT / "shadow_gateway_probe.py").read_text(encoding="utf-8"),
        )

    def test_13_shadow_probe_has_path_guard(self):
        self.assertIn(
            "_safe_inside", (EXPERIMENT / "shadow_gateway_probe.py").read_text(encoding="utf-8")
        )

    def test_14_shadow_config_disables_transport(self):
        diff = _read_json("P0_CORE_FEISHU_CONTROL_CONFIG_DIFF_032.json")
        self.assertFalse(diff["top_level_feishu_enabled_in_fixture"])

    def test_15_shadow_account_disabled(self):
        diff = _read_json("P0_CORE_FEISHU_CONTROL_CONFIG_DIFF_032.json")
        self.assertFalse(diff["target_account_enabled_in_fixture"])

    def test_16_shadow_fake_marker(self):
        cfg = json.loads((EXPERIMENT / "shadow" / "openclaw.json").read_text(encoding="utf-8"))
        self.assertTrue(
            cfg["channels"]["feishu"]["accounts"]["zhongshu"]["appSecret"].startswith("FAKE_")
        )

    def test_17_audit_records_plugin_block(self):
        self.assertEqual(
            _read_json("P0_OPENCLAW_CORE_FEISHU_CONTROL_AUDIT_032.json")[
                "shadow_feishu_plugin_loaded"
            ],
            "BLOCKED",
        )

    def test_18_audit_records_no_account_run(self):
        self.assertEqual(
            _read_json("P0_OPENCLAW_CORE_FEISHU_CONTROL_AUDIT_032.json")[
                "shadow_feishu_account_stop_restore"
            ],
            "NOT_RUN",
        )

    def test_19_audit_records_no_production_change(self):
        self.assertFalse(
            _read_json("P0_OPENCLAW_CORE_FEISHU_CONTROL_AUDIT_032.json")["production_changed"]
        )

    def test_20_core_stop_source_exists(self):
        self.assertIn("stopChannel", _source("server-channels-*.js"))

    def test_21_core_stop_aborts_source(self):
        self.assertIn("abort?.abort()", _source("server-channels-*.js"))

    def test_22_core_manual_stop_source(self):
        self.assertIn("manuallyStopped", _source("server-channels-*.js"))

    def test_23_core_start_rpc_source(self):
        self.assertIn('"channels.start"', _source("channels-hpSo8J3l.js"))

    def test_24_core_stop_rpc_source(self):
        self.assertIn('"channels.stop"', _source("channels-hpSo8J3l.js"))

    def test_25_channel_schema_account_id(self):
        self.assertIn("accountId", _source("schema-*.js"))

    def test_26_feishu_start_account_source(self):
        source = _source("channel-YrfEVd9X.js")
        self.assertIn("monitorFeishuProvider", source)

    def test_27_feishu_abort_source(self):
        self.assertIn("abortSignal", _source("monitor-vUjP0O1m.js"))

    def test_28_feishu_close_source(self):
        self.assertIn("wsClient.close()", _source("monitor.account-*.js"))

    def test_29_reload_is_channel_scoped(self):
        self.assertIn("restart-channel", _source("config-reload-plan-*.js"))

    def test_30_final_reports_exist(self):
        for name in (
            "P0_CURRENT_STATUS_V20.md",
            "P0_EVIDENCE_INDEX_V20.md",
            "P0_REMAINING_ACTIONS_V20.md",
            "NEXT_USER_ACTION.md",
        ):
            with self.subTest(name=name):
                self.assertTrue((REPORTS / name).is_file())


if __name__ == "__main__":
    unittest.main()
