"""Regression tests for the PD20 interface diagnostics; arithmetic only, not circuit qualification."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import interface_diagnostics as diag

HERE = Path(__file__).resolve().parent
RETAINED = HERE / 'interface-diagnostics.json'


class DiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calc = diag.calculator()

    def test_zero_load_rc_matches_closed_form(self):
        r, c, v0 = self.calc.DISCHARGE_R['+12'], self.calc.C_LOAD_MAX['+12'], 12.48
        tau = r * c
        self.assertAlmostEqual(diag.rc_voltage(v0, r, c, tau), v0 / math.e, places=12)
        self.assertAlmostEqual(diag.rc_voltage(v0, r, c, 0.0), v0, places=12)
        result = diag.evaluate_discharge(self.calc, {}, 0.5)
        expected = tau * math.log(v0 / self.calc.DISCHARGE_LEVEL['+12'])
        self.assertLessEqual(abs(result['time_to_discharge_level_s']['+12'] - expected), 10e-6)
        self.assertTrue(result['all_within_100ms'])
        self.assertIsNone(result['first_rvee_violation'])
        self.assertIsNone(result['first_direct_hazard'])

    def test_resistive_load_parallels_the_discharge_resistor(self):
        self.assertAlmostEqual(diag.rc_voltage(10.0, 100.0, 1e-4, 1e-3, r_load=100.0), 10.0 * math.exp(-1e-3 / 5e-3))

    def test_assumed_asymmetric_load_reverses_decay_order_and_is_flagged(self):
        result = diag.evaluate_discharge(self.calc, {'+12': 6.0}, 0.5)
        times = result['time_to_discharge_level_s']
        self.assertLess(times['+12'], times['-12'])
        zero = diag.evaluate_discharge(self.calc, {}, 0.5)['time_to_discharge_level_s']
        self.assertLess(times['+12'], zero['+12'] / 10)
        self.assertGreater(result['first_rvee_violation']['-12'], diag.M12_WHILE_P12_ABSENT_MAX)
        reverse = diag.evaluate_discharge(self.calc, {'-12': 6.3158}, 0.5)
        self.assertLess(reverse['time_to_discharge_level_s']['-12'], reverse['time_to_discharge_level_s']['+12'])
        self.assertGreater(reverse['first_rvee_violation']['+12'], diag.P12_WHILE_M12_ABSENT_MAX)

    def test_direct_hazard_is_distinct_from_the_sufficient_screen(self):
        # screen violated (+5 above 0.8 V with an analog rail below 1.5 V) but no direct hazard: other rail below 8 V
        self.assertTrue(diag.sufficient_screen_violation(1.67, -0.3, 1.0))
        self.assertFalse(diag.direct_hazard(1.67, -0.3, 1.0, 0.5))
        # direct hazard: -12 absent, +12 at 8 V or more, +5 above 0.8 V
        self.assertTrue(diag.direct_hazard(8.0, -0.2, 0.81, 0.5))
        self.assertFalse(diag.direct_hazard(8.0, -0.2, 0.8, 0.5))
        self.assertFalse(diag.direct_hazard(7.99, -0.2, 2.0, 0.5))
        # a screen pass while both analog rails are above 1.5 V says nothing about absence
        self.assertFalse(diag.sufficient_screen_violation(1.6, -1.6, 4.0))

    def test_undefined_absence_or_timing_stays_open(self):
        self.assertIsNone(diag.direct_hazard(12.0, 0.0, 5.0, None))
        self.assertIsNone(diag.rvee_violation(12.0, 0.0, None))
        result = diag.evaluate_discharge(self.calc, {}, None)
        self.assertEqual(result['first_rvee_violation'], diag.OPEN)
        self.assertEqual(result['first_direct_hazard'], diag.OPEN)
        report = diag.discharge(self.calc)
        self.assertEqual(report['disconnect_order']['status'], diag.OPEN)
        chain = diag.maximum_current(self.calc)['response_chain']
        self.assertTrue(any(stage['class'] == diag.UNSOURCED for stage in chain))

    def test_trip_threshold_is_never_a_delivered_maximum(self):
        for rail, row in diag.maximum_current(self.calc)['rails'].items():
            with self.subTest(rail=rail):
                self.assertEqual(row['bound_without_timing']['status'], diag.OPEN)
                self.assertIsNone(row['bound_without_timing']['bound_a'])
                self.assertLess(row['trip_max_a'], row['contract_max_a'])
        self.assertEqual(diag.delivered_current_bound(2.08, response_s=1e-6)['status'], diag.OPEN)
        self.assertEqual(diag.delivered_current_bound(2.08, di_dt_a_per_s=1e6)['status'], diag.OPEN)
        bound = diag.delivered_current_bound(2.08485, response_s=1e-6, di_dt_a_per_s=1e5)
        self.assertAlmostEqual(bound['bound_a'], 2.18485)
        h1 = next(h for h in diag.maximum_current(self.calc)['hypotheses'] if h['id'] == 'D3-H1')
        self.assertEqual(h1['conclusion'], diag.REFUTED)

    def test_startup_failures_are_preserved_and_current_equals_slope(self):
        report = diag.startup(self.calc)
        for rail, row in report['rails'].items():
            with self.subTest(rail=rail):
                self.assertTrue(row['exceeds_recorded_ceilings'])
                self.assertLess(abs(row['capacitive_current_at_peak_a'] - row['recorded_esr_branch_current_a']), 0.001)
                self.assertGreater(row['recorded_peak_over_ideal'], 1.5)
        peaks = diag.recorded_peaks()
        self.assertEqual(round(peaks['+5']['2us_v_per_ms'], 9), 0.954850860)
        self.assertEqual(round(peaks['+5']['2us_current_a'], 9), 0.114510041)
        self.assertEqual(round(peaks['-12']['2us_v_per_ms'], 9), 1.474778000)
        self.assertEqual(round(peaks['-12']['2us_current_a'], 9), 0.265259332)
        h1 = next(h for h in report['hypotheses'] if h['id'] == 'D1-H1')
        self.assertIn('designed common RAMP', h1['conclusion'])
        self.assertEqual(next(h for h in report['hypotheses'] if h['id'] == 'D1-H6')['conclusion'], diag.UNRESOLVED)

    def test_discharge_resistors_are_bound_to_the_schematic(self):
        values = diag.schematic_values()
        self.assertEqual(diag.discharge_resistors(self.calc, values), {'+12': 100.0, '+5': 33.0, '-12': 150.0})
        with self.assertRaisesRegex(ValueError, 'R76 is 120.0 ohm'):
            diag.discharge_resistors(self.calc, {**values, 'R76': '120 1% 1206'})
        with self.assertRaisesRegex(ValueError, 'RX5 not found'):
            diag.discharge_resistors(self.calc, {k: v for k, v in values.items() if k != 'RX5'})

    def test_rvee_boundaries_are_inclusive_limits(self):
        self.assertFalse(diag.rvee_violation(0.5, -0.4, 0.5))
        self.assertTrue(diag.rvee_violation(0.5001, -0.4, 0.5))
        self.assertFalse(diag.rvee_violation(0.4, -6.0, 0.5))
        self.assertTrue(diag.rvee_violation(0.4, -6.0001, 0.5))

    def test_zero_load_support_depends_on_the_absent_threshold(self):
        report = diag.discharge(self.calc)
        self.assertEqual(report['zero_load_rvee_absent_threshold_limit_v'], 1.45)
        self.assertIsNone(report['cases']['zero_load']['first_rvee_violation'])
        self.assertIsNotNone(report['cases']['zero_load_absent_1_5v']['first_rvee_violation'])
        h1 = next(h for h in report['hypotheses'] if h['id'] == 'D2-H1')
        self.assertIn('absent <= 1.44 V', h1['conclusion'])
        self.assertIn('Q54 -> R61 470k / R62 1M divider -> Q55', report['disconnect_order']['reason'])

    def test_scope_matrix_is_bound_to_schematic_and_deck(self):
        rows = diag.scope_matrix()
        omitted = {row['subsystem'] for row in rows if row['status'] == 'OMITTED'}
        self.assertIn('Active discharge with hold-up', omitted)
        self.assertIn('Current limiters and fault latch', omitted)
        refs, deck = diag.schematic_refs(), diag.deck_elements()
        with self.assertRaisesRegex(ValueError, 'not found'):
            diag.scope_matrix(refs - {'RX12'}, deck)
        with self.assertRaisesRegex(ValueError, 'not found'):
            diag.scope_matrix(refs, deck - {'XU13A'})
        with self.assertRaisesRegex(ValueError, 'now appear in the deck'):
            diag.scope_matrix(refs, deck | {'RX12'})
        for name in ('XQ51', 'XU11', 'XU6A'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'now appear in the deck'):
                diag.scope_matrix(refs, deck | {name})
        diag.scope_matrix(refs, deck | {'XU60'})

    @staticmethod
    def hypothesis(report, ident):
        return next(h for h in report['hypotheses'] if h['id'] == ident)

    def test_hypothesis_prose_is_bound_to_computed_fields(self):
        report = diag.startup(self.calc)
        h2 = self.hypothesis(report, 'D1-H2')['evidence']
        for rail in ('+5', '-12'):
            self.assertIn(f"{report['rails'][rail]['step_change_5us_to_2us_pct']:+.5f} %", h2)
        h3 = self.hypothesis(report, 'D1-H3')['evidence']
        self.assertIn('= 0.95 V/ms against 0.95 V/ms (equal)', h3)
        self.assertIn('= 1.4722 V/ms against 1.47 V/ms (slope ceiling tighter)', h3)
        current = diag.maximum_current(self.calc)
        d3 = self.hypothesis(current, 'D3-H2')['evidence']
        self.assertIn('15.15 / 4.56 / 39.16 mA (+12 / -12 / +5)', d3)
        self.assertIn('at most 4.56 mA/us of growth on -12', d3)

    def test_drifted_inputs_change_prose_and_fail_the_check(self):
        retained = json.loads(RETAINED.read_text())
        real = diag.recorded_peaks()
        drifted = copy.deepcopy(real)
        drifted['+5']['5us_v_per_ms'] *= 0.999
        with mock.patch.object(diag, 'recorded_peaks', return_value=drifted):
            h2 = self.hypothesis(diag.startup(self.calc), 'D1-H2')['evidence']
            self.assertNotEqual(h2, self.hypothesis(retained['d1_startup'], 'D1-H2')['evidence'])
            self.assertNotEqual(diag.findings(), retained)
            self.assertEqual(diag.main(['--check', str(RETAINED)]), 1)
        calc = diag.calculator()
        calc.I_MAX = {**calc.I_MAX, '-12': calc.I_MAX['-12'] + 0.02}
        d3 = self.hypothesis(diag.maximum_current(calc), 'D3-H2')['evidence']
        self.assertNotEqual(d3, self.hypothesis(retained['d3_maximum_current'], 'D3-H2')['evidence'])
        self.assertIn('on +12', d3)

    def test_hand_edited_prose_fails_the_check(self):
        retained = json.loads(RETAINED.read_text())
        self.hypothesis(retained['d1_startup'], 'D1-H2')['evidence'] = 'about +0.01 %'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'tampered.json'
            path.write_text(json.dumps(retained, indent=2) + '\n')
            self.assertEqual(diag.main(['--check', str(path)]), 1)

    def test_record_mirrors_computed_values(self):
        record = (HERE / 'interface-diagnostics.md').read_text()
        rails = diag.startup(self.calc)['rails']
        self.assertIn(f"changes the peak by {rails['+5']['step_change_5us_to_2us_pct']:+.5f} % (+5)", record)
        self.assertIn(f"{rails['-12']['step_change_5us_to_2us_pct']:+.5f} % (−12)", record)
        margins = diag.maximum_current(self.calc)['rails']
        self.assertIn(' / '.join(f"{margins[r]['margin_a'] * 1e3:.2f}" for r in ('+12', '-12', '+5')) + ' mA', record)
        self.assertIn(f"{margins['-12']['margin_a'] * 1e3:.2f} mA/µs", record)

    def test_retained_findings_are_fresh(self):
        self.assertEqual(json.loads(RETAINED.read_text()), diag.findings())
        self.assertEqual(diag.main(['--check', str(RETAINED)]), 0)


if __name__ == '__main__':
    unittest.main()
