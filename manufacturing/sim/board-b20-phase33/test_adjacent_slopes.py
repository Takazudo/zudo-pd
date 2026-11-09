"""Synthetic short-excursion tests; these do not qualify circuit slopes."""
import unittest
from analysis_inputs import adjacent_slope_screen


class AdjacentSlopeTests(unittest.TestCase):
    def test_averaging_cannot_hide_a_short_excursion(self):
        rows = [(0, .20), (2e-6, .204), (100e-6, .205)]
        self.assertLess((rows[-1][1] - rows[0][1]) / .0001 / 1000, .51)
        result = adjacent_slope_screen(rows, 1, 1, .51, True, (.45, .95, .114))
        self.assertAlmostEqual(result['maximum']['slope_v_per_ms'], 2)
        self.assertEqual(result['recorded_bound_exceeding_segments'], 1)
        self.assertIn('EXCEEDS', result['disposition'])

    def test_exception_requires_no_load_and_voltage_region(self):
        for rows, no_load, expected in [([(0, .2), (5e-6, .2045)], True, 0),
                                        ([(0, .2), (5e-6, .2045)], False, 1),
                                        ([(0, .5), (5e-6, .5045)], True, 1)]:
            result = adjacent_slope_screen(rows, 1, 1, .51, no_load, (.45, .95, .114))
            self.assertEqual(result['recorded_bound_exceeding_segments'], expected)
        self.assertIn('NOT LOGGED', adjacent_slope_screen([(0, .2), (5e-6, .2045)], 1, 1, .51, True, (.45, .95, .114))['exception']['capacitive_current_evidence'])

    def test_boundary_straddle_is_not_silently_waived(self):
        result = adjacent_slope_screen([(0, .449), (5e-6, .453)], 1, 1, .51, True, (.45, .95, .114))
        self.assertEqual(result['voltage_boundary_straddling_segments'], 1)
        self.assertEqual(result['disposition'], 'BOUNDARY STRADDLE REQUIRES REVIEW')

    def test_negative_rail_sign_and_nonmonotonic_samples_remain_visible(self):
        result = adjacent_slope_screen([(0, -.4), (5e-6, -.408), (10e-6, -.407)], 1, -1, 1.22, True, (.75, 1.47, .265))
        self.assertEqual(result['recorded_bound_exceeding_segments'], 1)
        self.assertAlmostEqual(result['maximum']['voltage_start_v'], .4)
        self.assertAlmostEqual(result['largest_negative_step_v'], -.001)


if __name__ == '__main__':
    unittest.main()
