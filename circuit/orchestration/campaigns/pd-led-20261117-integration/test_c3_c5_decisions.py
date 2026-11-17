"""Negative controls for the private C3/C5 decision dossier."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("c3_c5_decisions.py")
SPEC = importlib.util.spec_from_file_location("c3_c5_decisions", SCRIPT)
decisions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(decisions)


class DecisionDossierTests(unittest.TestCase):
    def test_locked_input_change_fails(self):
        key = next(iter(decisions.INPUT_SHA256))
        with patch.dict(decisions.INPUT_SHA256, {key: "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "Locked decision input changed"):
                decisions.create()

    def test_new_active_generated_route_invalidates_hold(self):
        result = decisions.create()
        route = next(row["candidate_target"] for row in result["routes"]
                     if row["class"] == "generated" and row["candidate_target"])
        original = decisions.route_exists

        def route_exists(candidate):
            return candidate == route or original(candidate)

        with patch.object(decisions, "route_exists", route_exists):
            with self.assertRaisesRegex(AssertionError, "proposed C3 route became active"):
                decisions.create()


if __name__ == "__main__":
    unittest.main()
