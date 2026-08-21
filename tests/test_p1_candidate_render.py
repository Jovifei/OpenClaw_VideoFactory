from __future__ import annotations

import importlib
import unittest


class CandidateRenderTests(unittest.TestCase):
    def test_historical_render_module_is_not_importable(self) -> None:
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("src.factory.render")

    def test_render_module_has_no_compatibility_fallback_import(self) -> None:
        self.assertRaises(ModuleNotFoundError, importlib.import_module, "src.factory.render")
