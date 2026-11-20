import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import c3_c5_item_review as review


class ItemReviewTest(unittest.TestCase):
    def test_dated_export_dispositions_and_page_dependencies(self):
        result = review.build()
        self.assertEqual(result["counts"], {
            "identity_conflicts": 4, "same_text_overlaps": 13,
            "dnp_export_excluded": 4, "dnp_export_requested": 3,
            "cad_collisions": 21, "page_editorial_candidates": 25,
            "pages_with_held_dependencies": 9, "old_route_collisions": 3,
        })
        self.assertEqual({(row["board"], row["refdes"]) for row in result["dnp"] if row["package_excluded"]},
                         {("board-p", ref) for ref in ("D6", "D7", "R17", "R18")})
        self.assertEqual({(row["board"], row["refdes"]) for row in result["dnp"] if row["package_bom"]},
                         {("board-l", "J3"), ("swd-adapter", "J1"), ("swd-adapter", "J2")})

    def test_changed_package_lock_fails_closed(self):
        with patch.dict(review.PACKAGE_LOCKS, {"board-p/excluded.csv": "0" * 64}):
            with self.assertRaisesRegex(AssertionError, "LED package changed"):
                review.build()

    def test_pin_map_mutation_changes_bound_owner_digest(self):
        with tempfile.TemporaryDirectory(dir=review.ROOT) as temporary:
            home = Path(temporary) / "component-sample"
            home.mkdir()
            (home / "manifest.json").write_text(json.dumps({"records": [{"record_id": "rec-test"}]}))
            (home / "sources.json").write_text(json.dumps({"sources": []}))
            pin_file = home / "pin-map.json"
            pin_file.write_text(json.dumps({"pin_maps": [{"record_id": "rec-test", "footprint": "F",
                                                          "pins": [{"symbol_pin": "1", "footprint_pad": "1"}]}]}))
            before = review.record_evidence(Path(temporary), "rec-test")
            pin_file.write_text(pin_file.read_text().replace('"footprint_pad": "1"', '"footprint_pad": "2"'))
            after = review.record_evidence(Path(temporary), "rec-test")
            self.assertNotEqual(before["owner_file_sha256"]["pin-map.json"],
                                after["owner_file_sha256"]["pin-map.json"])

    def test_cad_blob_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=review.ROOT) as temporary:
            path = Path(temporary) / "sample.kicad_mod"
            path.write_bytes(b'(pad "1")\n')
            expected = review.checked_git_blob(path, review.git_blob(path))
            path.write_bytes(b'(pad "2")\n')  # same byte length, changed pad
            with self.assertRaisesRegex(AssertionError, "CAD source blob changed"):
                review.checked_git_blob(path, expected)


if __name__ == "__main__":
    unittest.main()
