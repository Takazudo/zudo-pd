"""Tests for the pre-registered D1 servo/dead-zone criteria; synthetic waveforms, no solver."""
from pathlib import Path
import unittest

import extract_reference as ex
import servo_criteria as sc

HERE = Path(__file__).resolve().parent
SEG = 30e-3
ON = 29.6e-3
P5_SUPPLIES = [0.0, 20.0]
M12_SUPPLIES = [-12.142, 4.98]


def at(f):
    return lambda t0, t1: f((t0 + t1) / 2)


def rail_series(sign, driver, error, vgs_climb=0.5, gate_base=2.0):
    """Reference ramps from 27 ms at 0.1 V/ms; output floor 0.05 V (sign-adjusted) until conduction at 29.6 ms."""
    k = 3.32
    ref = lambda t: max(t - 27e-3, 0) * 1e3 * 0.1
    out = lambda t: sign * (0.05 if t < ON else 0.05 + (t - ON) * 1e3)
    current = lambda t: 0.0 if t < ON else -sign * 0.1
    gate = lambda t: gate_base + vgs_climb * min(max((t - 27e-3) / (ON - 27e-3), 0), 1)
    return {'out': at(out), 'ref': at(ref), 'current': at(current), 'gate': at(gate), 'driver': at(driver),
            'source': at(lambda t: 0.0), 'error': at(error)}, k


class CriteriaTests(unittest.TestCase):
    def run_p5(self, driver, error, reached=True, **kw):
        s, k = rail_series(1, driver, error, **kw)
        return sc.evaluate(s, SEG, SEG + 2e-6, k, 1, P5_SUPPLIES, 0.0, reached)

    def test_driver_held_at_the_supply_until_conduction_is_floor_set(self):
        result = self.run_p5(lambda t: 0.02 if t < 29.55e-3 else 3.0, lambda t: -0.01 if t < 29.5e-3 else 0.01)
        v = result['verdicts']
        self.assertEqual(v['servo wound up at a supply before conduction'], sc.SUPPORTED)
        self.assertEqual(v['windup released when the reference passes the pre-bias floor'], sc.SUPPORTED)
        self.assertEqual(v['peak slope coincides with driver recovery'], 'YES')
        self.assertEqual(v['dead zone set by'], 'HELD AT SUPPLY UNTIL CONDUCTION')

    def test_windup_that_exits_long_before_conduction_is_threshold_after_windup(self):
        # The retained gate data suggest this shape: parked at the low supply, leaving it ms before conduction.
        result = self.run_p5(lambda t: 0.02 if t < 18e-3 else 0.02 + (t - 18e-3) * 300,
                             lambda t: -0.01 if t < 18.1e-3 else 0.01, vgs_climb=1.0)
        v = result['verdicts']
        self.assertEqual(v['servo wound up at a supply before conduction'], sc.SUPPORTED)
        self.assertEqual(v['windup released when the reference passes the pre-bias floor'], sc.SUPPORTED)
        self.assertEqual(v['peak slope coincides with driver recovery'], 'NO')
        self.assertTrue(v['dead zone set by'].startswith('CONDUCTION THRESHOLD AFTER WINDUP'))
        self.assertAlmostEqual(result['driver_last_supply_exit_ms'], 18.0 + 0.08 / 300 * 1e3, delta=0.003)  # leaves the 0.1 V band
        self.assertAlmostEqual(result['servo_error_last_rise_through_zero_before_conduction_ms'], 18.1, places=2)
        self.assertTrue(result['output_flat_at_floor_before_exit'])

    def test_release_before_the_error_crossing_refutes_the_floor_release(self):
        result = self.run_p5(lambda t: 0.02 if t < 18e-3 else 5.0, lambda t: -0.01 if t < 25e-3 else 0.01)
        self.assertEqual(result['verdicts']['windup released when the reference passes the pre-bias floor'], sc.REFUTED)

    def test_late_release_or_moving_output_is_unresolved(self):
        late = self.run_p5(lambda t: 0.02 if t < 18e-3 else 5.0, lambda t: -0.01 if t < 17e-3 else 0.01)
        self.assertEqual(late['verdicts']['windup released when the reference passes the pre-bias floor'], sc.UNRESOLVED)
        s, k = rail_series(1, lambda t: 0.02 if t < 18e-3 else 5.0, lambda t: -0.01 if t < 17.95e-3 else 0.01)
        s['out'] = at(lambda t: 0.05 + 0.2 * t / 18e-3 if t < ON else 1.0)  # output drifting while parked
        moving = sc.evaluate(s, SEG, SEG + 2e-6, k, 1, P5_SUPPLIES, 0.0, True)
        self.assertFalse(moving['output_flat_at_floor_before_exit'])
        self.assertEqual(moving['verdicts']['windup released when the reference passes the pre-bias floor'], sc.UNRESOLVED)

    def test_held_at_supply_label_does_not_need_the_floor_verdict(self):
        result = self.run_p5(lambda t: 0.02 if t < 29.55e-3 else 3.0, lambda t: 0.01)
        self.assertEqual(result['verdicts']['dead zone set by'], 'HELD AT SUPPLY UNTIL CONDUCTION')
        self.assertEqual(result['verdicts']['windup released when the reference passes the pre-bias floor'], sc.UNRESOLVED)

    def test_no_windup_is_refuted_only_when_the_band_is_reachable(self):
        linear = lambda t: 1.0 + (t - 10e-3) * 100
        result = self.run_p5(linear, lambda t: 0.01)
        self.assertEqual(result['verdicts']['servo wound up at a supply before conduction'], sc.REFUTED)
        self.assertTrue(result['verdicts']['dead zone set by'].startswith('CONDUCTION THRESHOLD (no windup'))
        unreachable = self.run_p5(linear, lambda t: 0.01, reached=False)
        self.assertEqual(unreachable['verdicts']['servo wound up at a supply before conduction'], sc.UNRESOLVED)
        self.assertEqual(unreachable['verdicts']['dead zone set by'], sc.UNRESOLVED)

    def test_negative_rail_sign_offset_and_supplies(self):
        s, k = rail_series(-1, lambda t: -12.13 if t < 20e-3 else -12.13 + (t - 20e-3) * 400,
                           lambda t: -0.01 if t < 20.1e-3 else 0.01, vgs_climb=1.0, gate_base=0.5 + 2.0)
        result = sc.evaluate(s, SEG, SEG + 2e-6, k, -1, M12_SUPPLIES, 0.5, True)
        v = result['verdicts']
        self.assertGreater(result['maximum_lag_v'], 0.05)  # the output trails the negative target
        self.assertEqual(v['servo wound up at a supply before conduction'], sc.SUPPORTED)
        self.assertEqual(v['windup released when the reference passes the pre-bias floor'], sc.SUPPORTED)
        self.assertTrue(v['dead zone set by'].startswith('CONDUCTION THRESHOLD AFTER WINDUP'))
        self.assertAlmostEqual(result['vgs_v']['climb_start'], 2.0, places=6)  # gate - VO3 0.5 - source

    def test_early_returns_carry_unresolved_verdicts(self):
        s, k = rail_series(1, lambda t: 1.0, lambda t: 0.01)
        s['current'] = lambda t0, t1: 0.0
        result = sc.evaluate(s, SEG, SEG + 2e-6, k, 1, P5_SUPPLIES, 0.0, True)
        self.assertEqual(result['status'], sc.UNRESOLVED)
        self.assertEqual(set(result['verdicts'].values()), {sc.UNRESOLVED})

    def test_topology_is_read_from_the_executed_decks(self):
        decks = ex.derive_decks()
        p5 = sc.topology(decks['nom']['executed'], '+5')
        m12 = sc.topology(decks['adv']['executed'], '-12')
        self.assertEqual((p5['supplies_v'], p5['gate_offset_v'], p5['plus_input'], p5['minus_input']),
                         ([0.0, 20.0], 0.0, 'ramp_p5', 'trk5'))
        self.assertEqual((m12['supplies_v'], m12['gate_offset_v'], m12['plus_input'], m12['minus_input']),
                         ([-12.142, 4.98], 0.5, 'trk12n', 'trk12n_fb'))
        with self.assertRaisesRegex(ValueError, 'is not'):
            sc.topology(decks['nom']['executed'].replace('vin 0 p5_drv OPAx187', 'vin 0 p5_x OPAx187'), '+5')
        with self.assertRaisesRegex(ValueError, 'registered order'):
            sc.topology(decks['nom']['executed'].replace('v(p5_g) v(m12_g)', 'v(m12_g) v(p5_g)'), '+5')

    def test_pre_registered_document_states_the_same_thresholds(self):
        text = (HERE / 'd1-servo-criteria.md').read_text()
        for value in (f'{sc.BIN_S * 1e6:g} us', f'{sc.WINDOW_BEFORE_S * 1e3:g} ms', f'{sc.WINDOW_AFTER_S * 1e3:g} ms',
                      f'{sc.CONDUCTION_A * 1e3:g} mA', f'{sc.LAG_START_V:g} V', f'{sc.RAIL_BAND_V:g} V',
                      f'{sc.MIN_SATURATION_S * 1e6:g} us', f'{sc.RECOVERY_LEAD_S * 1e6:g} us', f'{sc.VGS_RISE_MIN_V:g} V',
                      f'{sc.RELEASE_DELAY_S * 1e6:g} us', f'{sc.FLOOR_FLAT_V * 1e3:g} mV', f'{sc.FLOOR_FLAT_S * 1e3:g} ms',
                      f'{sc.SETTLED_S * 1e3:g} ms'):
            self.assertIn(value, text)
        self.assertIn(' '.join(f'v({v})' for v in sc.SERVO_VECTORS), text)
        for verdict in sc.UNRESOLVED_VERDICTS:
            self.assertIn(verdict[0].upper() + verdict[1:], text)


if __name__ == '__main__':
    unittest.main()
