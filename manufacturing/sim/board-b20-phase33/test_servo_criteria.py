"""Tests for the pre-registered D1 servo/dead-zone criteria; synthetic waveforms, no solver."""
from pathlib import Path
import re
import unittest

import extract_reference as ex
import servo_criteria as sc

HERE = Path(__file__).resolve().parent
SEG = 10e-3
CEIL_SUPPLIES = [0.0, 20.0]


def series(driver, vgs_rise=0.0):
    """+5-like rail: reference ramps from 7 ms, output floor 0.05 V until conduction at 9.6 ms, catch-up after."""
    k = 3.32
    ref = lambda t: max(t - 7e-3, 0) * 1e3 * 0.1  # 0.1 V/ms reference
    on = 9.6e-3
    out = lambda t: 0.05 if t < on else 0.05 + (t - on) * 1e3 * 1.0
    current = lambda t: 0.0 if t < on else -0.1
    gate = lambda t: 2.0 + vgs_rise * min(max((t - 7.5e-3) / (on - 7.5e-3), 0), 1)
    at = lambda f: (lambda t0, t1: f((t0 + t1) / 2))
    return {'out': at(out), 'ref': at(lambda t: ref(t)), 'current': at(current), 'gate': at(gate),
            'driver': at(driver), 'source': at(lambda t: 0.0)}, k


class CriteriaTests(unittest.TestCase):
    def evaluate(self, driver, vgs_rise=0.0):
        s, k = series(driver, vgs_rise)
        return sc.evaluate(s, SEG, SEG + 2e-6, k, 1, CEIL_SUPPLIES, 0.0)

    def test_parked_driver_that_recovers_at_onset_supports_windup(self):
        result = self.evaluate(lambda t: 19.95 if t < 9.55e-3 else 12.0)
        v = result['verdicts']
        self.assertEqual(v['servo saturation and windup recovery'], sc.SUPPORTED)
        self.assertEqual(v['peak slope coincides with driver recovery'], 'YES')
        self.assertTrue(v['dead zone set by'].startswith('PRE-BIAS FLOOR'))
        self.assertGreater(result['driver_saturated_in_dead_zone_us'], 10)
        self.assertLess(result['dead_zone_ms'][0], 9.6)
        self.assertAlmostEqual(result['dead_zone_ms'][1], 9.6, places=2)

    def test_linear_driver_with_rising_vgs_is_threshold_limited(self):
        result = self.evaluate(lambda t: 10.0 + (t - 7e-3) * 1e3, vgs_rise=0.5)
        v = result['verdicts']
        self.assertEqual(v['servo saturation and windup recovery'], sc.REFUTED)
        self.assertEqual(v['peak slope coincides with driver recovery'], 'NO')
        self.assertTrue(v['dead zone set by'].startswith('CONDUCTION THRESHOLD'))

    def test_saturation_that_ends_early_is_not_called_the_cause(self):
        result = self.evaluate(lambda t: 0.05 if t < 8.5e-3 else 5.0, vgs_rise=0.5)
        self.assertEqual(result['verdicts']['servo saturation and windup recovery'], sc.UNRESOLVED)
        self.assertEqual(result['verdicts']['peak slope coincides with driver recovery'], 'NO')
        self.assertTrue(result['verdicts']['dead zone set by'].startswith('MIXED'))

    def test_no_conduction_at_the_segment_is_unresolved(self):
        s, k = series(lambda t: 1.0)
        s['current'] = lambda t0, t1: 0.0
        self.assertEqual(sc.evaluate(s, SEG, SEG + 2e-6, k, 1, CEIL_SUPPLIES, 0.0)['status'], sc.UNRESOLVED)

    def test_topology_is_read_from_the_executed_decks(self):
        decks = ex.derive_decks()
        p5 = sc.topology(decks['nom']['executed'], '+5')
        m12 = sc.topology(decks['adv']['executed'], '-12')
        self.assertEqual(p5['supplies_v'], [0.0, 20.0])
        self.assertEqual(m12['supplies_v'], [-12.142, 4.98])
        self.assertEqual(p5['gate_offset_v'], 0.0)
        self.assertEqual(m12['gate_offset_v'], 0.5)
        with self.assertRaisesRegex(ValueError, 'is not'):
            sc.topology(decks['nom']['executed'].replace('vin 0 p5_drv OPAx187', 'vin 0 p5_x OPAx187'), '+5')

    def test_pre_registered_document_states_the_same_thresholds(self):
        text = (HERE / 'd1-servo-criteria.md').read_text()
        for value in (f'{sc.BIN_S * 1e6:g} us', f'{sc.WINDOW_BEFORE_S * 1e3:g} ms', f'{sc.WINDOW_AFTER_S * 1e3:g} ms',
                      f'{sc.CONDUCTION_A * 1e3:g} mA', f'{sc.LAG_START_V:g} V', f'{sc.RAIL_BAND_V:g} V',
                      f'{sc.MIN_SATURATION_S * 1e6:g} us', f'{sc.RECOVERY_LEAD_S * 1e6:g} us', f'{sc.VGS_RISE_MIN_V:g} V'):
            self.assertIn(value, text)
        self.assertIn(' '.join(f'v({v})' for v in sc.SERVO_VECTORS), text)


if __name__ == '__main__':
    unittest.main()
