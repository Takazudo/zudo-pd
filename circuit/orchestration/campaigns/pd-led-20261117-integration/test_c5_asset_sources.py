import csv
import tempfile
import unittest
from pathlib import Path

import c5_link_audit


class AssetSourceTest(unittest.TestCase):
    def test_changed_or_missing_public_source_fails_closed(self):
        source = "doc/public/assets/enclosure/assembled.png"
        with (c5_link_audit.C1 / "asset-map.tsv").open(newline="") as handle:
            mapped = next(row for row in csv.DictReader(handle, delimiter="\t")
                          if row["source_path"] == source)
        original = (c5_link_audit.ROOT / "products/led-lamp" / source).read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            led = Path(directory)
            target = led / source
            target.parent.mkdir(parents=True)
            with self.assertRaises(AssertionError):
                c5_link_audit.verify_asset_bytes(source, mapped, led)
            target.write_bytes(original)
            c5_link_audit.verify_asset_bytes(source, mapped, led)
            target.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            with self.assertRaisesRegex(AssertionError, "source bytes changed"):
                c5_link_audit.verify_asset_bytes(source, mapped, led)

        with tempfile.TemporaryDirectory() as directory:
            led = Path(directory)
            actual = led / "actual"
            actual.mkdir()
            (actual / "assembled.png").write_bytes(original)
            linked = led / "doc/public/assets/enclosure"
            linked.parent.mkdir(parents=True)
            linked.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(AssertionError, "symlink"):
                c5_link_audit.verify_asset_bytes(source, mapped, led)


if __name__ == "__main__":
    unittest.main()
