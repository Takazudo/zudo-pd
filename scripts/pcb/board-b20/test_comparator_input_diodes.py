"""OV/UV comparator input-diode loading of REF25 and the disabled no-load back-feed (2026-11-12, D12).

U6/U7/U8 (and U5B) are OPA2187 sections with back-to-back differential input diodes (SBOS807E 7.3.7). While a rail is
absent, the diodes conduct from REF25 into the window dividers. The owner decision fits 100k in series with the four
U6/U7 divider-side inputs and leaves U8 unresistored. These assertions pin the CALCULATED result for the fitted design,
keep the pre-fix result as history, and check from the spec that no resistor path from U8's inputs reaches the +12 / +5
terminals or M12_PRE without passing through REF25 or GND (FET, diode and op-amp paths are out of scope). They do not prove
bench behaviour.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'scripts' / 'pcb' / 'calculate-board-b20-draft.py'
spec = importlib.util.spec_from_file_location('calculator_comparator_diodes', SOURCE)
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)
RESULT = calculator.comparator_input_diodes()
BEFORE = calculator.comparator_input_diodes(calculator.UNFIXED_SERIES_R, _options=False)
sys.path.insert(0, str(ROOT / 'scripts' / 'schgen'))
import board_b20_spec as b20  # noqa: E402


class FittedSeriesResistorTests(unittest.TestCase):
    def test_spec_fits_four_resistors_on_u6_u7_only(self):
        self.assertEqual(calculator.COMPARATOR_SERIES_R, {'U6': 100e3, 'U7': 100e3, 'U8': 0.0})
        for rail, u, plus, minus in (('12', 'U6', 'OV12_IN', 'UV12_IN'), ('5', 'U7', 'OV5_IN', 'UV5_IN')):
            self.assertIn(f'{u}.3', b20.NETS[plus])
            self.assertIn(f'{u}.6', b20.NETS[minus])
            for net, div in ((plus, f'OV{rail}_DIV'), (minus, f'UV{rail}_DIV')):
                (res,) = [p.split('.')[0] for p in b20.NETS[net] if not p.startswith(u)]
                self.assertEqual(b20.COMPONENTS[res][1:3], ('100k', 'C25741'))
                self.assertIn(f'{res}.1', b20.NETS[div])
        for net in ('OVN_DIV', 'UVN_DIV'):
            self.assertIn('U8.2' if net == 'OVN_DIV' else 'U8.5', b20.NETS[net])

    def test_u8_inputs_share_no_node_with_positive_terminals(self):
        # Walk resistors only (two-pin R parts), stopping only at REF25 and GND; M12_OUT is walked through.
        stiff = {'REF25', 'GND'}
        pins = {}
        for net, members in b20.NETS.items():
            for p in members:
                pins[p] = net
        resistors = {r for r in b20.COMPONENTS if r.startswith('R') and {f'{r}.1', f'{r}.2'} <= set(pins)}
        seen, todo = set(), ['OVN_DIV', 'UVN_DIV']
        while todo:
            net = todo.pop()
            if net in seen or net in stiff:
                continue
            seen.add(net)
            for p in b20.NETS[net]:
                ref, pin = p.rsplit('.', 1)
                if ref in resistors:
                    todo.append(pins[f'{ref}.{"2" if pin == "1" else "1"}'])
        self.assertIn('M12_OUT', seen)
        self.assertFalse(seen & {'P12_OUT', 'P5_OUT', 'M12_PRE', 'P5_SUP'}, sorted(seen))

    def test_fitted_channel_currents_and_ref_load(self):
        got = {k: v['diode_ma'] for k, v in RESULT['channels_at_vf_min'].items()}
        self.assertEqual(got, {'U6A OV+12': 0.0192, 'U6B UV+12': 0.0154, 'U7A OV+5': 0.0186, 'U7B UV+5': 0.0199,
                               'U8A OV-12': 0.0841, 'U8B UV-12': 0.0318, 'U5B VINUV': 0.0})
        self.assertEqual(RESULT['ref25_delta_ma_by_vf'], {'0.4': 0.1693, '0.7': 0.1416})
        self.assertEqual(RESULT['abs_max_status'], 'PASS')
        load = RESULT['ref25_load_ma']
        self.assertEqual((load['enabled_settled'], load['disabled_with_diodes'], load['step_on_enable']), (1.9232, 2.0766, 0.1534))
        self.assertEqual(RESULT['ref25_load_status'], 'PASS')
        self.assertEqual(RESULT['ref25_step_shift_ppm'], {'25c': 4.603, 'full_range': 7.672})

    def test_fitted_backfeed_is_below_the_absent_levels(self):
        now, levels = RESULT['disabled_terminal_v_no_load'], RESULT['absent_levels_v']
        self.assertEqual(now, {'+12': [0.124, 0.253], '+5': [0.158, 0.307], '-12': [0.204, 0.357]})
        for rail, (_, high) in now.items():
            self.assertLess(high, levels[rail], rail)
        self.assertEqual(RESULT['disabled_backfeed_status'], 'PASS')
        # The locked decision applies the contract absent / discharge levels to the disabled, unloaded terminal.
        self.assertEqual(levels, {'+12': 0.5, '+5': 0.6, '-12': 0.6})
        self.assertEqual(levels['+5'], min(calculator.DISCHARGE_LEVEL['+5'], calculator.P5_ORDER_LEVEL))

    def test_interpretation_is_bound_to_the_locked_decision(self):
        decisions = json.loads((ROOT / 'scripts' / 'schgen' / 'decisions.json').read_text())['decisions']
        (dec,) = [d for d in decisions if d['id'] == 'dec-b20-comparator-input-series-r']
        self.assertEqual(dec['status'], 'LOCKED')
        self.assertIn('#279', dec['applies_to'])
        self.assertIn('fact-c25741-resistance', dec['evidence'])
        self.assertIn(dec['id'], RESULT['disabled_backfeed_note'])

    def test_pre_fix_result_is_kept(self):
        self.assertEqual(RESULT['disabled_terminal_v_before_fix'], {'+12': [0.915, 1.162], '+5': [1.467, 1.78], '-12': [0.204, 0.357]})
        self.assertEqual(BEFORE['disabled_backfeed_status'], 'OPEN')
        self.assertEqual(BEFORE['diode_current_max_ma'], 0.3982)
        self.assertEqual(BEFORE['ref25_load_ma']['disabled_with_diodes'], 2.8423)
        self.assertEqual(BEFORE['series_resistor_options'], [])

    def test_fitted_windows_with_ib(self):
        screen = RESULT['fitted_window_ib_screen']
        margins = {k: v['margin_pct'] for k, v in screen.items()}
        self.assertEqual(margins, {'OV+12': [0.322, 0.224], 'UV+12': [1.59, 1.49], 'OV+5': [0.534, 0.501],
                                   'UV+5': [2.028, 1.936], 'OV-12': [0.309, 0.197], 'UV-12': [0.644, 0.645]})
        self.assertEqual(RESULT['fitted_window_ib_status'], 'PASS')
        self.assertEqual(screen['OV+12']['ib_max_a'], 5e-9)
        self.assertEqual(screen['OV-12']['ib_max_a'], 7.5e-9)

    def test_fitted_input_rc(self):
        self.assertEqual(RESULT['fitted_input_rc_us'], {'OV+12': 1.446, 'UV+12': 1.802, 'OV+5': 1.489, 'UV+5': 1.435,
                                                        'OV-12': 0.263, 'UV-12': 0.691})
        self.assertIn('NOT FOUND', RESULT['fitted_input_rc_note'])

    def test_paper_options_are_kept(self):
        opts = {o['series_r_ohm']: o for o in RESULT['series_resistor_options']}
        self.assertEqual({k: o['threshold_status'] for k, o in opts.items()}, {10e3: 'PASS', 100e3: 'PASS', 1e6: 'FAIL'})
        # Uniform 100k including U8 lifts -12 to the Q55 body-diode drop: the reason U8 stays unresistored.
        self.assertEqual(opts[100e3]['disabled_terminal_v']['-12'], [0.302, 0.601])
        self.assertGreater(opts[100e3]['disabled_terminal_v']['-12'][1], RESULT['absent_levels_v']['-12'])

    def test_setpoint_budget_uses_full_range_row(self):
        ppm = RESULT['setpoint_budget_ppm']
        self.assertEqual(ppm['budgeted_full_range_row_at_pa'], 150.0)
        self.assertEqual(ppm['full_range_row_at_enabled_load'], 96.16)
        self.assertEqual(RESULT['setpoint_budget_status'], 'PASS')
        self.assertAlmostEqual(calculator.REF_ACC, 0.001 + 50e-6 * 3.0, places=12)

    def test_inputs_are_not_relaxed(self):
        self.assertEqual(calculator.OPA_DIFF_DIODE_VF_PA, (0.4, 0.7))
        self.assertEqual(calculator.OPA_INPUT_CURRENT_ABS_MAX, 10e-3)
        self.assertEqual(calculator.OPA_IB_MAX, {'25c': 350e-12, 'full_range_lv': 5e-9, 'full_range_hv': 7.5e-9})
        self.assertEqual(calculator.REF_LOAD_REG_PPM_PER_MA, {'25c': 30.0, 'full_range': 50.0})
        self.assertEqual(calculator.REF_IOUT_MAX_A, 10e-3)
        self.assertEqual(calculator.REF_LOAD_MA_PA, 3.0)
        self.assertEqual(calculator.Q55_BODY_VF_PA, (0.3, 0.6))
        self.assertAlmostEqual(calculator.OPA_INPUT_C_TYP_F, 10.2e-12)
        self.assertEqual(calculator.INPUT_STRAY_C_PA_F, 3e-12)


if __name__ == '__main__':
    unittest.main()
