import unittest

import d2_load_corners as d2
import interface_diagnostics as idg


class CornerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = d2.corners()
        cls.by = {(r['corner']['+12'], r['corner']['-12'], r['corner']['+5']): r for r in cls.out['corners']}

    def test_eighteen_corners(self):
        self.assertEqual(self.out['corners_total'], 18)

    def test_zero_and_symmetric_maximum_pass(self):
        for key in (('0', '0', '0'), ('maximum', 'maximum', 'maximum'), ('planning', 'planning', '0')):
            self.assertIsNone(self.by[key]['first_rvee_violation'], key)

    def test_one_sided_load_reorders_decay(self):
        row = self.by[('maximum', '0', '0')]
        self.assertLessEqual(row['first_rvee_violation']['+12'], 0.5)
        self.assertGreater(row['first_rvee_violation']['-12'], 6.0)
        self.assertIsNotNone(row['first_direct_hazard'])
        self.assertIsNotNone(self.by[('0', 'maximum', '0')]['first_rvee_violation'])

    def test_ten_corners_fail(self):
        self.assertEqual(self.out["corners_failing"], 10)

    def test_module_hooks_are_restored(self):
        self.assertIsNone(idg.rvee_violation(12, 12, None))


if __name__ == '__main__':
    unittest.main()
