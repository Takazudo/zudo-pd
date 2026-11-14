import unittest

import e21_conditions as e21


def series(step_at=0.140, lead=0.2, settle=0.005, offset=0.05, ref_start=0.130):
    """Rail held at a 0.1 V bias while the target creeps from ref_start at 0.02 V/ms; from step_at the target ramps at
    0.27 V/ms and the rail steps ahead of it by `lead`, decaying linearly over `settle` to `offset`."""
    times = [k * 1e-4 for k in range(400, 2345)]
    base = max(0.0, (step_at - ref_start) * 20)
    targets = [max(0.0, (t - ref_start) * 20) if t < step_at else base + (t - step_at) * 270 for t in times]
    volts = [0.1 if t < step_at else max(0.1, g + offset + lead * max(0.0, 1 - (t - step_at) / settle))
             for t, g in zip(times, targets)]
    return times, volts, targets


class RailReadingTests(unittest.TestCase):
    def test_fast_return_is_within_from_the_rail_start(self):
        r = e21.rail_reading(*series())
        self.assertTrue(r['lead_within'])
        self.assertTrue(r['return_within_from_rail_start'])
        self.assertAlmostEqual(r['normal_difference_v'], 0.05, places=3)
        self.assertEqual(r['largest_reversal_v'], 0.0)

    def test_an_early_reference_start_can_fail_the_other_reading(self):
        r = e21.rail_reading(*series(ref_start=0.120, step_at=0.137, settle=0.005))
        self.assertTrue(r['return_within_from_rail_start'])
        self.assertFalse(r['return_within_from_reference_start'])

    def test_a_large_lead_is_flagged(self):
        self.assertFalse(e21.rail_reading(*series(lead=0.3))['lead_within'])

    def test_a_slow_return_is_flagged(self):
        self.assertFalse(e21.rail_reading(*series(settle=0.020))['return_within_from_rail_start'])


class OtherTests(unittest.TestCase):
    def test_gains_from_drawn_resistors(self):
        deck = 'RT12A a b 69.8k\nRT12B b 0 10k\nRT5A a b 23.2k\nRT5B b 0 10k\nRT12NA a b 93.1k\nRT12NB b c 750k\n'
        g = e21.gains(deck)
        self.assertAlmostEqual(g['+12'], 7.98)
        self.assertAlmostEqual(g['+5'], 3.32)
        self.assertAlmostEqual(g['-12'], 750 / 93.1)

    def test_current_rows_use_the_e21_limits(self):
        rail = lambda a: {'peak_current_in_region_a': a}
        out = e21.currents({'adv': {'+5': rail(0.18), '-12': rail(0.351)}})
        self.assertTrue(out['adv +5']['within'])
        self.assertFalse(out['adv -12']['within'])


if __name__ == '__main__':
    unittest.main()
