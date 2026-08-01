import json
import subprocess
import unittest
from pathlib import Path

from services.feishu_gateway.official_rpc_bridge import OfficialDeviceBridge, _safe_response


class TestOfficialRpcBridge046(unittest.TestCase):
    def test_python_bridge_uses_stdin_and_environment_session_without_shared_token(self):
        observed = {}

        def runner(command, **kwargs):
            observed["command"] = command
            observed["input"] = kwargs["input"]
            observed["environment"] = kwargs["env"]
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(
                    {
                        "status": "device_identity_missing",
                        "operation": "health",
                        "client_id": "project-feishu-gateway",
                        "client_mode": "backend",
                        "role": "operator",
                        "scopes": ["operator.read"],
                        "explicit_shared_token": False,
                        "device_identity": True,
                        "challenge_signature": True,
                    }
                ),
                "",
            )

        result = OfficialDeviceBridge(node="node", runner=runner).health()
        self.assertEqual(result["status"], "device_identity_missing")
        self.assertNotIn("OPENCLAW_GATEWAY_TOKEN", observed["environment"])
        self.assertNotIn("VIDEO_FACTORY_BRIDGE_SESSION", " ".join(observed["command"]))
        self.assertIn("session", json.loads(observed["input"]))
        self.assertFalse(result["explicit_shared_token"])

    def test_response_redacts_raw_pairing_request_id(self):
        projected = _safe_response(
            {
                "status": "pairing_required",
                "operation": "health",
                "error": {
                    "top_level_code": "UNAUTHORIZED",
                    "details_code": "PAIRING_REQUIRED",
                    "pairing_request_id": "must-not-return",
                    "pairing_request_id_redacted": "id-123456789abc",
                },
            }
        )
        self.assertEqual(projected["error"]["pairing_request_id_redacted"], "id-123456789abc")
        self.assertNotIn("must-not-return", json.dumps(projected))

    def test_python_source_never_references_private_device_files(self):
        source = (
            Path(__file__)
            .parents[1]
            .joinpath("services", "feishu_gateway", "official_rpc_bridge.py")
            .read_text(encoding="utf-8")
        )
        self.assertNotIn("device.json", source)
        self.assertNotIn("device-auth.json", source)


if __name__ == "__main__":
    unittest.main()
