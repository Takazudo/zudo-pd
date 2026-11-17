import unittest
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


if __name__ == "__main__":
    unittest.main()
