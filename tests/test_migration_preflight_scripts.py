import tempfile
import unittest
from pathlib import Path

from scripts.migration.preflight_check import check as preflight
from scripts.migration.rollback_verify import check as rollback
from scripts.migration.verify_single_consumer import check as consumer


class TestMigrationScripts(unittest.TestCase):
    def test_preflight_pass_and_fail(self):
        snapshot = {
            "config_backup_exists": True,
            "config_sha256": "hash",
            "gateway_running": True,
            "binding_count": 1,
            "cron_count": 4,
            "running_tasks": 0,
            "pending_media": 0,
        }
        self.assertEqual("pass", preflight(snapshot)["status"])
        snapshot["binding_count"] = 2
        self.assertEqual("fail", preflight(snapshot)["status"])

    def test_single_consumer_requires_no_duplicates(self):
        snapshot = {
            "consumers": [{"identity": "project_gateway"}],
            "websocket_count": 1,
            "event_ids": ["e"],
            "reply_ids": ["r"],
            "lease": {"owner": "project_gateway", "heartbeat_at": 1},
            "now": 1,
        }
        self.assertEqual("pass", consumer(snapshot)["status"])
        snapshot["event_ids"].append("e")
        self.assertEqual("fail", consumer(snapshot)["status"])

    def test_rollback_requires_backup_and_steps(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / "backup.json"
            backup.write_text("{}", encoding="utf-8")
            valid = {
                "backup_path": str(backup),
                "steps": [
                    "stop_project_gateway",
                    "restore_core_binding",
                    "start_core_gateway",
                    "verify_text_attachment_session",
                    "record_event",
                ],
            }
            self.assertEqual("pass", rollback(valid)["status"])
            valid["steps"] = []
            self.assertEqual("fail", rollback(valid)["status"])
