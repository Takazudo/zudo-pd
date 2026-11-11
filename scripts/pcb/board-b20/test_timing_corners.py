"""RDY / POR / min-off orderings at sourced R/C tolerance and X5R temperature corners (#235, readiness D11).

The 2026-11-11 corner run failed the 5x servo-settle PROJECT screen with the 200k RDY network. That
was a failed screen, not proof of malfunction. The 2026-11-12 D11 owner decision raised the network to
2 x 150k C22807. These assertions pin the selection rule, the new corners and the superseded history,
so a later edit cannot quietly relax an input or erase the record.
"""
import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'calculate-board-b20-draft.py'
spec = importlib.util.spec_from_file_location('calculator_timing', SOURCE)
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)
TIMING = calculator.timing()
FIVE_SETTLE = 5 * max(v['settle_to_0p1pct_s'] for v in TIMING['servo'].values())


class TimingCornerTests(unittest.TestCase):
    def test_corner_values(self):
        self.assertAlmostEqual(TIMING['rdy_s'][0], 0.23466, places=5)
        self.assertAlmostEqual(TIMING['rdy_s'][1], 1.39191, places=5)
        self.assertAlmostEqual(TIMING['por_s'][0], 0.00766, places=5)
        self.assertAlmostEqual(TIMING['por_s'][1], 0.04640, places=5)

    def test_corner_statuses(self):
        for key in ('por_rdy_overlap_status', 'min_off_hold_status', 'servo_settled_before_enable_status',
                    'rdy_selection_status'):
            self.assertEqual(TIMING[key], 'PASS', key)
        self.assertAlmostEqual(FIVE_SETTLE, 0.1919, places=4)
        self.assertGreaterEqual(TIMING['rdy_s'][0], 1.05 * FIVE_SETTLE)
        self.assertLess(TIMING['min_off_hold_s'][1], TIMING['rdy_s'][0])
        self.assertLess(TIMING['por_s'][1], TIMING['rdy_s'][0])

    def test_selection_rule_picks_the_smallest_inventory_network(self):
        # The only two-placement totals from inventory 0603 1 % parts near the bound are 250k and 300k.
        per_ohm = TIMING['rdy_s'][0] / calculator.RDY_NET['R']
        self.assertLess(250e3 * per_ohm, 1.05 * FIVE_SETTLE)
        self.assertGreaterEqual(300e3 * per_ohm, 1.05 * FIVE_SETTLE)

    def test_superseded_200k_history(self):
        old = TIMING['superseded_200k']
        self.assertEqual(old['nominal_rdy_short_s'], 0.21407)
        self.assertEqual(old['nominal_servo_status'], 'PASS')
        self.assertEqual(old['corner_25c_rdy_short_s'], 0.18405)
        self.assertEqual(old['corner_25c_servo_status'], 'FAIL')
        self.assertIn('superseded 2026-11-12', old['network'])
        self.assertEqual(calculator.RDY_NET_SUPERSEDED, {'R': 200e3, 'C': 10e-6})

    def test_corner_inputs_are_not_relaxed(self):
        self.assertEqual(calculator.RDY_CORNER, {'R_TOL': 0.01, 'C_TOL': 0.10, 'C_TCC': 0.15, 'DC_BIAS_TYP_AT_VTH': -0.011})
        self.assertEqual(calculator.POR_CORNER, {'R_TOL': 0.01, 'C_TOL': 0.10, 'C_TCC': 0.15, 'DC_BIAS_TYP_AT_VTH': -0.032})
        self.assertEqual(calculator.RDY_NET, {'R': 300e3, 'C': 10e-6})
        self.assertEqual(calculator.POR_NET, {'R': 100e3, 'C': 1e-6})
        self.assertEqual(calculator.RDY_SELECTION_MARGIN, 0.05)
        for needle in ('PROJECT screen', 'high P5_SUP', 'TCC -15 %', 'TCC +15 %'):
            self.assertIn(needle, TIMING['corner_basis'])

    def test_spec_carries_the_decided_network(self):
        text = (Path(__file__).resolve().parents[3] / 'scripts/schgen/board_b20_spec.py').read_text()
        self.assertIn("two('RRDY1', 'R150K', 'P5_SUP', 'RDY_X')", text)
        self.assertIn("two('RRDY2', 'R150K', 'RDY_X', 'RDY')", text)


if __name__ == '__main__':
    unittest.main()
