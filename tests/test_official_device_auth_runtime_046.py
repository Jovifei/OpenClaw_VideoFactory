import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.feishu_gateway.runtime_server import (
    LEGACY_SHARED_TOKEN_ADAPTER_DISABLED,
    PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED,
    Runtime,
    probe_openclaw_rpc,
)


class TestOfficialDeviceAuthRuntime046(unittest.TestCase):
    def test_default_preflight_uses_device_probe_without_reading_shared_token(self):
        def forbidden_provider():
            raise AssertionError("legacy shared token path was selected")

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"FEISHU_GATEWAY_CONFIG_FINGERPRINT": "fixture"}, clear=True),
        ):
            runtime = Runtime(
                Path(directory) / "status.json",
                Path(directory) / "gateway.jsonl",
                mode="production-preflight",
                token_provider=forbidden_provider,
                official_device_probe=lambda: {"status": "device_identity_missing"},
            )
            self.assertEqual(
                PROJECT_GATEWAY_DEVICE_PAIRING_REQUIRED, runtime.ready()["rpc_preflight_result"]
            )
            self.assertEqual("device_pairing_required", runtime.openclaw_rpc)

    def test_legacy_shared_token_adapter_is_explicitly_disabled(self):
        self.assertEqual(
            LEGACY_SHARED_TOKEN_ADAPTER_DISABLED, probe_openclaw_rpc(lambda: "unused")["result"]
        )

    def test_runtime_source_does_not_import_the_legacy_rpc_client(self):
        source = (
            Path(__file__)
            .parents[1]
            .joinpath("services", "feishu_gateway", "runtime_server.py")
            .read_text(encoding="utf-8")
        )
        self.assertNotIn("openclaw_rpc.client import", source)
        self.assertIn("official_rpc_bridge", source)


if __name__ == "__main__":
    unittest.main()
