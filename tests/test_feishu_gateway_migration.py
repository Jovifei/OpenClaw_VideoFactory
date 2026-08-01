import unittest

from experiments.feishu_gateway_migration.check_single_consumer import check
from experiments.feishu_gateway_migration.simulate_cutover import simulate as cutover
from experiments.feishu_gateway_migration.simulate_rollback import simulate as rollback


class TestMigrationFixtures(unittest.TestCase):
    def test_single_consumer_fixture_passes(self):
        result = check(
            {
                "consumers": [{"identity": "project"}],
                "websocket_count": 1,
                "event_ids": ["e"],
                "reply_ids": ["r"],
            }
        )
        self.assertEqual("pass", result["status"])

    def test_duplicate_fixture_fails(self):
        result = check(
            {
                "consumers": [{"identity": "project"}],
                "websocket_count": 1,
                "event_ids": ["e", "e"],
                "reply_ids": ["r", "r"],
            }
        )
        self.assertEqual("fail", result["status"])
        self.assertEqual(1, result["duplicate_events"])

    def test_cutover_and_rollback_are_exclusive(self):
        self.assertEqual("fake_event_routed", cutover()[-1])
        self.assertEqual("one_consumer_verified", rollback()[-1])
