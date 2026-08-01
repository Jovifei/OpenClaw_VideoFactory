import tempfile
import unittest
from pathlib import Path

from scripts.migration.zhongshu_postcheck import check as postcheck
from scripts.migration.zhongshu_preflight import check as preflight


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def valid_preflight() -> dict:
    return {
        "schema": "p0_zhongshu_preflight_v1",
        "capture_mode": "operator_read_only",
        "entry": "zhongshu",
        "inventory": {
            "agents_observed": True,
            "bindings_observed": True,
            "cron_observed": True,
            "gateway_observed": True,
            "sessions_observed": True,
        },
        "core": {
            "binding_enabled": True,
            "binding_count": 1,
            "feishu_consumer_count": 1,
            "websocket_count": 1,
            "gateway_state": "running",
        },
        "project": {"feishu_consumer_count": 0, "websocket_count": 0, "gateway_state": "stopped"},
        "combined_feishu_consumer_count": 1,
        "active_tasks": 0,
        "pending_media": 0,
        "session": {"snapshot_present": True, "lineage_hash": HASH_A},
        "config_backup": {"manifest_present": True, "sha256": HASH_B},
        "rollback": {"plan_present": True, "plan_id": "P0-ZHONGSHU-MIGRATION-QUALIFICATION-029"},
    }


def valid_postcutover() -> dict:
    return {
        "schema": "p0_zhongshu_postcheck_v1",
        "capture_mode": "operator_read_only",
        "entry": "zhongshu",
        "core": {
            "binding_enabled": False,
            "binding_count": 0,
            "feishu_consumer_count": 0,
            "websocket_count": 0,
            "gateway_state": "stopped",
        },
        "project": {
            "feishu_consumer_count": 1,
            "websocket_count": 1,
            "gateway_state": "running",
            "ready": True,
            "lease_owner": "project_gateway",
        },
        "combined_feishu_consumer_count": 1,
        "test_phase": "text",
        "event_hashes": [HASH_C],
        "reply_hashes": [HASH_D],
        "session": {"continuity_verified": True, "lineage_hash": HASH_A},
    }


class ZhongshuMigration029Tests(unittest.TestCase):
    def test_preflight_accepts_only_one_current_core_consumer(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact"
            artifact.write_text("placeholder", encoding="utf-8")
            result = preflight(
                valid_preflight(),
                config_backup_manifest_exists=artifact.is_file(),
                rollback_plan_exists=artifact.is_file(),
            )
        self.assertEqual("pass", result["status"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual("ZHONGSHU_MIGRATION_WAITING_AUTH", result["migration_state"])

    def test_preflight_rejects_overlap_and_missing_artifacts(self):
        snapshot = valid_preflight()
        snapshot["project"]["feishu_consumer_count"] = 1
        snapshot["combined_feishu_consumer_count"] = 2
        result = preflight(
            snapshot, config_backup_manifest_exists=False, rollback_plan_exists=False
        )
        self.assertEqual("fail", result["status"])
        self.assertIn("project_feishu_consumer_count_unexpected", result["failures"])
        self.assertIn("config_backup_manifest_missing", result["failures"])
        self.assertIn("rollback_plan_missing", result["failures"])

    def test_postcheck_requires_unique_delivery_and_session_lineage(self):
        result = postcheck(valid_postcutover(), valid_preflight())
        self.assertEqual("pass", result["status"])
        duplicate = valid_postcutover()
        duplicate["reply_hashes"] = [HASH_D, HASH_D]
        duplicate["session"]["lineage_hash"] = HASH_B
        failed = postcheck(duplicate, valid_preflight())
        self.assertEqual("fail", failed["status"])
        self.assertIn("reply_hashes_not_unique", failed["failures"])
        self.assertIn("session_lineage_mismatch", failed["failures"])

    def test_snapshot_with_secret_named_field_is_rejected(self):
        snapshot = valid_preflight()
        snapshot["token"] = "not-a-real-token"
        result = preflight(snapshot, config_backup_manifest_exists=True, rollback_plan_exists=True)
        self.assertEqual("fail", result["status"])
        self.assertIn("forbidden_snapshot_field", result["failures"])


if __name__ == "__main__":
    unittest.main()
