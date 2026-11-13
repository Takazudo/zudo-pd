"""OV/UV comparator input-diode loading of REF25 and the disabled no-load back-feed (2026-11-12, D12).

U6/U7/U8 (and U5B) are OPA2187 sections with back-to-back differential input diodes (SBOS807E 7.3). While a rail is
absent, the diodes conduct from REF25 into the window dividers. These assertions pin the CALCULATED result: abs max
and the REF25 load hold, setpoints() budgets the full-range load-regulation row, the disabled back-feed stays OPEN, and the series-resistor
paper options keep their threshold verdicts. They do not prove bench behaviour.
"""
import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'calculate-board-b20-draft.py'
spec = importlib.util.spec_from_file_location('calculator_comparator_diodes', SOURCE)
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)
RESULT = calculator.comparator_input_diodes()


class ComparatorInputDiodeTests(unittest.TestCase):
    def test_channel_currents_at_vf_min(self):
        expected = {'U6A OV+12': 0.2192, 'U6B UV+12': 0.0575, 'U7A OV+5': 0.1639, 'U7B UV+5': 0.3982,
                    'U8A OV-12': 0.0841, 'U8B UV-12': 0.0318, 'U5B VINUV': 0.0}
        got = {k: v['diode_ma'] for k, v in RESULT['channels_at_vf_min'].items()}
        self.assertEqual(got, expected)
        self.assertEqual(RESULT['ref25_delta_ma_by_vf'], {'0.4': 0.9349, '0.7': 0.7979})

    def test_abs_max_and_ref_load_hold(self):
        self.assertEqual(RESULT['abs_max_status'], 'PASS')
        self.assertLess(RESULT['diode_current_max_ma'], 10.0)
        load = RESULT['ref25_load_ma']
        self.assertEqual(load['enabled_settled'], 1.9232)
        self.assertEqual(load['disabled_with_diodes'], 2.8423)
        self.assertEqual(load['step_on_enable'], 0.9191)
        self.assertEqual(RESULT['ref25_load_status'], 'PASS')
        self.assertEqual(RESULT['ref25_step_shift_ppm'], {'25c': 27.572, 'full_range': 45.954})
        self.assertEqual(RESULT['setpoint_step_mv_full_range'], {'+12': 0.5584, '+5': 0.2336, '-12': 0.5575})

    def test_setpoint_budget_uses_full_range_row(self):
        ppm = RESULT['setpoint_budget_ppm']
        self.assertEqual(ppm['budgeted_full_range_row_at_pa'], 150.0)
        self.assertEqual(ppm['full_range_row_at_enabled_load'], 96.16)
        self.assertLessEqual(ppm['full_range_row_at_enabled_load'], ppm['budgeted_full_range_row_at_pa'])
        self.assertEqual(RESULT['setpoint_budget_status'], 'PASS')
        self.assertAlmostEqual(calculator.REF_ACC, 0.001 + 50e-6 * 3.0, places=12)

    def test_disabled_backfeed_stays_open(self):
        self.assertEqual(RESULT['disabled_terminal_v_no_load'],
                         {'+12': [0.915, 1.162], '+5': [1.467, 1.78], '-12': [0.204, 0.357]})
        self.assertEqual(RESULT['disabled_terminal_v_without_diode_conduction']['-12'], [0.303, 0.602])
        levels = RESULT['absent_levels_v']
        for rail in ('+12', '+5'):
            self.assertGreater(RESULT['disabled_terminal_v_no_load'][rail][0], levels[rail], rail)
        # -12: the comparator diodes clamp the REF-referenced dividers today; without them the Q55 body diode bounds
        # the terminal at one unsourced drop, which reaches the 0.6 V level only at the top of its PA.
        self.assertLess(RESULT['disabled_terminal_v_no_load']['-12'][1], levels['-12'])
        self.assertLess(RESULT['disabled_terminal_v_without_diode_conduction']['-12'][0], levels['-12'])
        self.assertGreater(RESULT['disabled_terminal_v_without_diode_conduction']['-12'][1], levels['-12'])
        self.assertIn('Q55 body diode', RESULT['disabled_backfeed_note'])
        self.assertEqual(RESULT['disabled_backfeed_status'], 'OPEN')
        self.assertIn('unresolved', RESULT['disabled_backfeed_note'])

    def test_series_resistor_options(self):
        opts = {o['series_r_ohm']: o for o in RESULT['series_resistor_options']}
        self.assertEqual({k: o['threshold_status'] for k, o in opts.items()}, {10e3: 'PASS', 100e3: 'PASS', 1e6: 'FAIL'})
        self.assertEqual(opts[100e3]['ref25_delta_max_ma'], 0.0938)
        self.assertEqual(opts[100e3]['ib_threshold_error_pct'], {'+12': 0.03, '+5': 0.03, '-12': 0.0361})
        self.assertEqual(opts[100e3]['window_margin_pct'], {'+12': 0.246, '+5': 0.5231, '-12': 0.2045})
        self.assertEqual(opts[100e3]['disabled_terminal_v']['-12'], [0.302, 0.601])

    def test_inputs_are_not_relaxed(self):
        self.assertEqual(calculator.OPA_DIFF_DIODE_VF_PA, (0.4, 0.7))
        self.assertEqual(calculator.OPA_INPUT_CURRENT_ABS_MAX, 10e-3)
        self.assertEqual(calculator.OPA_IB_MAX, {'25c': 350e-12, 'full_range_lv': 5e-9, 'full_range_hv': 7.5e-9})
        self.assertEqual(calculator.REF_LOAD_REG_PPM_PER_MA, {'25c': 30.0, 'full_range': 50.0})
        self.assertEqual(calculator.REF_IOUT_MAX_A, 10e-3)
        self.assertEqual(calculator.REF_LOAD_MA_PA, 3.0)
        self.assertEqual(calculator.Q55_BODY_VF_PA, (0.3, 0.6))


if __name__ == '__main__':
    unittest.main()
