"""RDY / POR / min-off orderings at sourced R/C tolerance corners (2026-11-11, #235).

The servo-before-enable row is a FAILED PROJECT SCREEN at the short corner, not proof of malfunction.
These assertions pin that result so a later edit cannot silently restore the old nominal PASS.
"""
import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'calculate-board-b20-draft.py'
spec = importlib.util.spec_from_file_location('calculator_timing', SOURCE)
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)
TIMING = calculator.timing()


class TimingCornerTests(unittest.TestCase):
    def test_corner_values(self):
        self.assertAlmostEqual(TIMING['rdy_s'][0], 0.18864, places=5)
        self.assertAlmostEqual(TIMING['rdy_s'][1], 0.80691, places=5)
        self.assertAlmostEqual(TIMING['por_s'][0], 0.00923, places=5)
        self.assertAlmostEqual(TIMING['por_s'][1], 0.04035, places=5)

    def test_corner_statuses(self):
        self.assertEqual(TIMING['por_rdy_overlap_status'], 'PASS')
        self.assertEqual(TIMING['min_off_hold_status'], 'PASS')
        self.assertEqual(TIMING['servo_settled_before_enable_status'], 'FAIL')
        five_settle = 5 * max(v['settle_to_0p1pct_s'] for v in TIMING['servo'].values())
        self.assertAlmostEqual(five_settle, 0.1919, places=4)
        self.assertLess(TIMING['rdy_s'][0], five_settle)

    def test_nominal_result_is_kept_as_history(self):
        nominal = TIMING['nominal']
        self.assertEqual(nominal['rdy_s'], [0.21407, 0.72629])
        self.assertEqual(nominal['por_s'], [0.0107, 0.03631])
        self.assertEqual(nominal['servo_settled_before_enable_status'], 'PASS')
        self.assertIn('superseded', nominal['note'])

    def test_corner_inputs_are_not_relaxed(self):
        self.assertEqual(calculator.RDY_CORNER, {'R_TOL': 0.01, 'C_TOL': 0.10, 'DC_BIAS_TYP_AT_VTH': -0.011})
        self.assertEqual(calculator.POR_CORNER, {'R_TOL': 0.01, 'C_TOL': 0.10, 'DC_BIAS_TYP_AT_VTH': -0.032})
        self.assertEqual(calculator.RDY_NET, {'R': 200e3, 'C': 10e-6})
        self.assertIn('PROJECT screen', TIMING['corner_basis'])


if __name__ == '__main__':
    unittest.main()
