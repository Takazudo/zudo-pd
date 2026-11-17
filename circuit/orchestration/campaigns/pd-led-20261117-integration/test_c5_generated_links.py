"""Failure probes for the built historical-link contract."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[3] / "scripts/check-led-generated-links.py"
spec = importlib.util.spec_from_file_location("check_led_generated_links", SCRIPT)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class GeneratedLinksTest(unittest.TestCase):
    def test_real_built_sites(self):
        contract.check()

    def test_missing_historical_fragment_fails(self):
        original = contract.html_tags

        def changed(path):
            tags = original(path)
            if str(path).endswith("components/records/al8860mp-13/index.html"):
                tags.ids.discard("fact-al8860-ctrl")
            return tags

        with patch.object(contract, "html_tags", side_effect=changed):
            with self.assertRaisesRegex(AssertionError, "Missing historical fragment"):
                contract.check()

    def test_localized_pd_link_fails(self):
        original = contract.html_tags

        def changed(path):
            tags = original(path)
            if str(path).endswith("led-lamp/architecture/board-l/index.html"):
                tags.hrefs = [value for value in tags.hrefs
                              if value != contract.OLD_HOST +
                              "/docs/components/records/al8860mp-13/#fact-al8860-ctrl"]
            return tags

        with patch.object(contract, "html_tags", side_effect=changed):
            with self.assertRaisesRegex(AssertionError, "Old-host link changed"):
                contract.check()


if __name__ == "__main__":
    unittest.main()
