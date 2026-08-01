import unittest

from experiments.runtime_qualification.qualification import (
    run_card_action_qualification,
    run_rollback_failure_rehearsal,
    run_rpc_end_to_end_qualification,
)
from scripts.migration.post_cutover_check import check as post_cutover_check
from scripts.migration.pre_cutover_check import check as pre_cutover_check
from scripts.migration.rollback_check import check as rollback_check


class TestGatewayQualification026(unittest.TestCase):
    def test_rpc_end_to_end_mock_has_stable_idempotency_and_timeout_recovery(self):
        result = run_rpc_end_to_end_qualification()
        self.assertEqual("MOCK_ONLY", result["mode"])
        self.assertTrue(
            all(
                result[field]
                for field in (
                    "gateway_start",
                    "rpc_connect",
                    "session_create",
                    "send_text",
                    "receive_response",
                    "request_id_consistent",
                    "retry_no_duplicate",
                    "timeout_recovery",
                )
            )
        )
        self.assertEqual(2, result["logical_agent_requests"])
        self.assertEqual(3, result["transport_attempts"])

    def test_card_action_mock_preserves_ticket_scope_without_claiming_reply_intent(self):
        result = run_card_action_qualification()
        self.assertEqual("MOCK_ONLY", result["mode"])
        self.assertTrue(
            all(
                result[field]
                for field in (
                    "attachment_ingress",
                    "action_preserved",
                    "operator_present",
                    "chat_present",
                    "ticket_consumed",
                    "analysis_request_generated",
                )
            )
        )
        self.assertEqual(
            "NOT_QUALIFIED_REPLY_TO_MESSAGE_ID_REQUIRED", result["production_intent_admission"]
        )

    def test_mock_cutover_checks_reject_overlap_and_accept_expected_snapshots(self):
        preflight = {
            "mode": "mock_qualification",
            "old_consumer_count": 1,
            "new_consumer_count": 0,
            "old_websocket_count": 1,
            "new_websocket_count": 0,
            "active_tasks": 0,
            "pending_media": 0,
            "binding_backup_exists": True,
            "duplicate_events": 0,
            "duplicate_replies": 0,
        }
        self.assertEqual("pass", pre_cutover_check(preflight)["status"])
        postflight = {
            "mode": "mock_qualification",
            "old_consumer_count": 0,
            "new_consumer_count": 1,
            "old_websocket_count": 0,
            "new_websocket_count": 1,
            "connection_owner": "project_gateway",
            "duplicate_events": 0,
            "duplicate_replies": 0,
        }
        self.assertEqual("pass", post_cutover_check(postflight)["status"])
        self.assertEqual(
            "fail", post_cutover_check({**postflight, "old_consumer_count": 1})["status"]
        )

    def test_rollback_mock_records_recovery_without_executing_commands(self):
        rehearsal = run_rollback_failure_rehearsal()
        self.assertEqual("MOCK_ONLY", rehearsal["mode"])
        self.assertFalse(rehearsal["commands_executed"])
        snapshot = {
            "mode": "mock_qualification",
            "gateway_start_failed": True,
            "project_gateway_stopped": True,
            "old_binding_restored": True,
            "old_text_path_verified": True,
            "old_attachment_path_verified": True,
            "rollback_manifest_exists": True,
            "recovery_seconds": rehearsal["recovery_seconds"],
            "recovery_point": rehearsal["recovery_point"],
        }
        checked = rollback_check(snapshot)
        self.assertEqual("pass", checked["status"])
        self.assertTrue(rehearsal["recovery_within_objective"])


if __name__ == "__main__":
    unittest.main()
