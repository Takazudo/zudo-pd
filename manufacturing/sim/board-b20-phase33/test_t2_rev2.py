import math
import re
import unittest
from unittest import mock

import rules_revision as rules
import t2_clamp as t1
import t2_rev2 as r2


def block_text(**kw):
    return '\n'.join(r2.t2_block(**kw))


class DiodeSlotTests(unittest.TestCase):
    def test_every_slot_is_bound_and_rated(self):
        self.assertEqual({k: d['mpn'] for k, d in r2.DIODES.items()},
                         {'DT2C': 'FJH1100', 'DT2K': 'BAS116LT1G', 'DL': 'FJH1100'})
        r2.require_diodes()

    def test_refuses_an_unsourced_slot(self):
        with mock.patch.dict(r2.DIODES, {'DT2K': None}), self.assertRaisesRegex(ValueError, 'not sourced'):
            r2.t2_block()

    def test_refuses_an_under_rated_part(self):
        # FJH1100's 15 V working rating does not cover DT2K's 27.5 V (owner decision 2026-11-12).
        with mock.patch.dict(r2.DIODES, {'DT2K': r2.FJH1100}), self.assertRaisesRegex(ValueError, '27.5'):
            r2.t2_block()

    def test_refuses_untraced_parameters(self):
        partial = {**r2.FJH1100, 'rows': {'IS': 'x'}}
        with mock.patch.dict(r2.DIODES, {'DT2C': partial}), self.assertRaisesRegex(ValueError, 'untraced'):
            r2.t2_block()

    def test_models_reproduce_their_rows(self):
        vt = r2.VT_SIM_V
        f = r2.FJH1100['model']
        self.assertAlmostEqual(f['N'] * vt * math.log(1e-6 / f['IS']), 0.530, places=6)
        self.assertAlmostEqual(f['N'] * vt * math.log(10e-6 / f['IS']), 0.605, places=6)
        k = r2.BAS116L['model']
        self.assertAlmostEqual(k['N'] * vt * math.log(1e-3 / k['IS']), 0.900, places=6)
        self.assertAlmostEqual(k['N'] * vt * math.log(10e-3 / k['IS']), 1.000, places=6)
        self.assertEqual((f['CJO'], f['M'], k['CJO'], k['M']), (2e-12, 0, 2e-12, 0))
        self.assertEqual((r2.FJH1100['ir_max_a'], r2.BAS116L['ir_max_a'], r2.BAS116L['ir_hot_max_a']),
                         (3e-12, 5e-9, 80e-9))


class BlockTests(unittest.TestCase):
    def test_no_switch_on_the_summing_node(self):
        block = r2.t2_block()
        on_fb = [x for x in block if 'trk12n_fb' in x.split()[1:3]]
        self.assertEqual(on_fb, ['VT2G t2g trk12n_fb 0'])
        self.assertFalse(any(x.startswith(('BT2G', 'BT2D', 'RT2D', 'CT2D')) for x in block))

    def test_limiter_and_feedback(self):
        block = r2.t2_block()
        for line in ('XT2B t2p t2m p5sup t2n t2a OPAx187', 'RT2M2 t2m t2a 4.99meg', 'RT2O t2a t2o 100k',
                     'DT2L t2o t2l DT2LX', 'VT2L t2l 0 0', 'DT2C t2c t2o DT2CX', 'RT2C t2c t2g 402k'):
            self.assertIn(line, block)
        self.assertAlmostEqual(r2.R_C_OHM + 100e3, 502e3)

    def test_window_pulls_the_inverting_input_toward_m12_pre(self):
        block = r2.t2_block()
        self.assertIn('RT2W t2m t2w 100k', block)
        self.assertIn(t1.switch('BT2W', 't2w', 'm12_pre', '0.5*(1-tanh((v(ennd)-1.0)*8))'), block)
        self.assertFalse(any(x.split()[0].startswith('R') and 't2p' in x.split()[1:3] and 'p5sup' in x for x in block))

    def test_inert_control_returns_r_c_to_gnd_and_keeps_the_rest(self):
        a, b = r2.t2_block(), r2.t2_block(inert=True)
        self.assertEqual({x.split()[0] for x in set(a) ^ set(b)}, {'*', 'VT2G'})
        self.assertIn('VT2G t2g 0 0', b)

    def test_leakage_flows_cathode_to_anode_at_each_rows_maximum(self):
        block = r2.t2_block()
        self.assertIn('BT2CL t2o t2c I=3e-12*tanh(max(v(t2o,t2c),0)/0.05)+7e-12*0.5*(1+tanh((v(t2o,t2c)-5)/0.05))',
                      block)
        self.assertIn('BT2KL t2k m12_drv I=5e-09*tanh(max(v(t2k,m12_drv),0)/0.05)', block)
        self.assertIn('BT2LL t2l t2o I=3e-12*tanh(max(v(t2l,t2o),0)/0.05)+7e-12*0.5*(1+tanh((v(t2l,t2o)-5)/0.05))',
                      block)

    def test_leakage_takes_the_next_row_above_a_rows_voltage(self):
        expr = r2.leak('B', 'c', 'a', ((5.0, 3e-12), (15.0, 10e-12))).split('I=', 1)[1]
        for vr, want in ((0.6, 3e-12), (4.5, 3e-12), (5.5, 10e-12), (12.0, 10e-12)):
            got = eval(expr.replace('v(c,a)', repr(vr)), {'tanh': math.tanh, 'max': max})
            self.assertAlmostEqual(got / want, 1.0, places=3, msg=vr)

    def test_diodes_use_their_own_models(self):
        text = block_text()
        self.assertEqual(dict(re.findall(r'^(D\S+) \S+ \S+ (\S+)$', text, re.M)),
                         {'DT2K': 'DT2KX', 'DT2L': 'DT2LX', 'DT2C': 'DT2CX'})
        self.assertNotIn('DBODY', text)

    def test_vf_spread_moves_only_is_of_one_role(self):
        for label, (role, vf) in r2.VF_SPREAD_V.items():
            block = r2.t2_block(vf=(role, vf))
            line = next(x for x in block if x.startswith(f'.model {r2.MODEL_NAME[role]}'))
            params = dict(re.findall(r'(\w+)=(\S+)', line.split(';')[0]))
            n, i = float(params['N']), r2.OPERATING_CURRENT_A[role]
            self.assertAlmostEqual(n * r2.VT_SIM_V * math.log(i / float(params['IS'])), vf, places=4)
            others = set(r2.t2_block()) ^ set(block)
            self.assertEqual({x.split()[1] for x in others}, {r2.MODEL_NAME[role]}, label)

    def test_ladder_overrides_one_role(self):
        block = r2.t2_block(ir={'DT2K': 80e-9})
        self.assertIn('BT2KL t2k m12_drv I=8e-08*tanh(max(v(t2k,m12_drv),0)/0.05)', block)
        self.assertIn('BT2CL t2o t2c I=3e-12*tanh(max(v(t2o,t2c),0)/0.05)+7e-12*0.5*(1+tanh((v(t2o,t2c)-5)/0.05))',
                      block)


class HotTests(unittest.TestCase):
    def test_hot_temperature_is_the_owner_decision(self):
        self.assertEqual(r2.HOT_T_C, 82.1)
        self.assertAlmostEqual(r2.hot_ir('DT2C'), 8.56e-10, delta=0.01e-9)     # below the ~1.95 nA prediction
        self.assertAlmostEqual(r2.hot_ir('DT2C', r2.LET_THROUGH_T_C), 4.75e-9, delta=0.01e-9)
        self.assertAlmostEqual(r2.temperature_for(1.95e-9) - r2.HOT_T_C, 8.3, places=1)

    @mock.patch.object(r2, 'HOT_T_C', None)
    def test_hot_case_waits_for_the_board_temperature(self):
        with self.assertRaisesRegex(ValueError, 'hot-case temperature'):
            r2.block_for('hot')
        with self.assertRaisesRegex(ValueError, 'hot-case temperature'):
            r2.derive_cases()

    def test_scaling(self):
        self.assertAlmostEqual(r2.temperature_for(1.95e-9), 90.41, places=2)
        self.assertAlmostEqual(r2.hot_factor(32.0), 2.0)
        self.assertAlmostEqual(r2.hot_ir('DT2C', 32.0), 6e-12)
        self.assertEqual(r2.hot_ir('DT2K', 60.0), 80e-9)       # the 150 C row held flat, not the chord
        with mock.patch.object(r2, 'HOT_T_C', None), self.assertRaisesRegex(ValueError, 'hot-case temperature'):
            r2.hot_ir('DT2K')

    def test_a_crossing_below_the_sourced_point_is_negative(self):
        crossing = r2.failure_ir([(3e-12, -1e-6), (1e-9, -2e-6), (2e-9, -3e-6)])
        self.assertLess(crossing, 0)

    def test_hot_block(self):
        with mock.patch.object(r2, 'HOT_T_C', 39.0):
            block = r2.block_for('hot')()
        self.assertIn('BT2CL t2o t2c I=1.2e-11*tanh(max(v(t2o,t2c),0)/0.05)+2.8e-11*0.5*(1+tanh((v(t2o,t2c)-5)/0.05))',
                      block)
        self.assertIn('BT2KL t2k m12_drv I=8e-08*tanh(max(v(t2k,m12_drv),0)/0.05)', block)


class AnalysisTests(unittest.TestCase):
    def test_failure_ir_is_the_zero_of_a_straight_line(self):
        pts = [(3e-12, 80e-6), (1e-9, 40e-6), (2e-9, -0.1e-6)]
        crossing = r2.failure_ir(pts)
        self.assertGreater(crossing, 1.9e-9)
        self.assertLess(crossing, 2.1e-9)
        self.assertIsNone(r2.failure_ir([(1e-9, 1e-6)]))
        self.assertIsNone(r2.failure_ir([(1e-9, 1e-6), (2e-9, 2e-6)]))

    def test_sourced_point_uses_the_row_the_deck_applied(self):
        self.assertEqual(r2.sourced_dt2c_ir({'dt2c_reverse_max_v': 0.5}), 3e-12)
        self.assertEqual(r2.sourced_dt2c_ir({'dt2c_reverse_max_v': 6.0}), 10e-12)
        self.assertEqual(r2.sourced_dt2c_ir('NOT EVALUATED: x'), 10e-12)

    def test_rule6b_margin(self):
        detail = {'enable_edge_tolerance_v': {'minimum': 107e-6, 'maximum': 17e-6},
                  'below_baseline_minimum_v': 20e-6, 'above_baseline_maximum_v': -3e-6}
        self.assertAlmostEqual(r2.rule6b_margin(detail), 20e-6)

    def test_rule6b_margin_matches_the_revised_rule(self):
        base = (-0.09715653351, -0.00766395804)
        for low in (-0.0972, -0.09727, -0.09726):
            detail = {'enable_edge_tolerance_v': {'minimum': rules.tolerance(base[0]), 'maximum': rules.tolerance(base[1])},
                      'below_baseline_minimum_v': base[0] - low, 'above_baseline_maximum_v': 0.0}
            self.assertEqual(r2.rule6b_margin(detail) >= 0, rules.within_tolerance((low, base[1]), base), low)

    def test_a2_metrics_on_a_synthetic_record(self):
        times = [k * 1e-4 for k in range(2400)]
        s = {'t2a': [2.76] * 2400, 't2o': [0.5] * 2400, 't2p': [-9.6] * 2400, 't2m': [-12.0] * 2400,
             't2k': [-9.4] * 2400, 'm12_drv': [-10.1] * 2400, 'p5sup': [4.98] * 2400, 'm12_pre': [-12.1] * 2400,
             'i_VT2L': [43e-6] * 2400, 'i_VT2G': [0.0] * 2400}
        t2 = {'t2o': s['t2o'], 't2c': [0.19] * 2400}
        m = r2.a2_metrics(times, s, t2)
        self.assertAlmostEqual(m['limiter_current_disabled_a'], 43e-6)
        self.assertAlmostEqual(m['limiter_current_running_a'], 43e-6)
        self.assertTrue(m['xt2b_inputs_within_retained_vcm'])
        self.assertAlmostEqual(m['dt2k_reverse_max_v'], 0.7)
        self.assertAlmostEqual(m['dt2c_reverse_max_v'], 0.31)
        self.assertEqual(m['reverse_within_rating'], {'DT2C': True, 'DT2K': True, 'DL': True})
        self.assertEqual(m['reverse_within_leakage_rows'], {'DT2C': True, 'DT2K': True, 'DL': True})
        loaded = r2.a2_metrics(times, s, t2, input_window=(0.02, 0.15), running=None)
        self.assertNotIn('limiter_current_running_a', loaded)
        s['t2p'][5] = 6.0                             # power-up (0.5 ms) is outside the assessed window
        self.assertTrue(r2.a2_metrics(times, s, t2)['xt2b_inputs_within_absmax'])
        s['t2p'] = [3.4] * 2400                       # the original (a2) window placement
        self.assertFalse(r2.a2_metrics(times, s, t2)['xt2b_inputs_within_retained_vcm'])

    def test_combine(self):
        self.assertEqual(r2.combine([{'passes': True}, {'passes': True}]), 'PASS')
        self.assertEqual(r2.combine([{'passes': True}, {'passes': False}]), 'FAIL')
        self.assertEqual(r2.combine([{'passes': True}, {'passes': None}]), 'NOT EVALUATED')

    def test_informational_cases_never_decide_the_candidate(self):
        self.assertEqual(set(r2.INFORMATIONAL), {'ir1n', 'ir2n', 'k1u'})
        self.assertNotIn('hot', r2.REQUIRED)
        self.assertEqual(set(r2.REQUIRED), {'vflo', 'vfhi', 'cvflo', 'cvfhi', 'kvflo', 'kvfhi', 'k80n'})


class CaseTests(unittest.TestCase):
    @mock.patch.object(r2, 'HOT_T_C', 85.0)
    def test_cases(self):
        cases = r2.derive_cases()
        self.assertEqual(r2.LABEL_ORDER[:len(t1.LABEL_ORDER)], t1.LABEL_ORDER)
        self.assertEqual({k: sorted(v) for k, v in cases.items() if k in r2.EXTRA},
                         {k: sorted(names) for k, (_, names) in r2.EXTRA.items()})
        for label, decks in cases.items():
            for name, text in decks.items():
                if label in r2.EXTRA or label in t1.T2_LABELS or label == 'ctrl':
                    self.assertEqual(text.count(f'wrdata {name}-a2.txt'), 1, (label, name))

    def test_every_extra_case_compares_with_the_pinned_pair(self):
        for label, (_, names) in r2.EXTRA.items():
            for n in names:
                self.assertEqual(r2.unit((label, n)), [(label, n), ('run', n)])


class VariantTests(unittest.TestCase):
    def test_ladder_is_fixed(self):
        self.assertEqual(r2.VARIANTS, (('abstol', ('abstol=1e-9', 'abstol=1e-8')),
                                       ('rshunt', ('rshunt=1e10', 'rshunt=1e9'))))

    def test_chains_end_at_a_pinned_reference(self):
        for case in r2.BASELINE:
            self.assertIn(r2.unit(case)[-1][0], ('run', 'base'), case)
        self.assertEqual(r2.unit(('t2lo', 'nom')), [('t2lo', 'nom'), ('e12lo', 'nom'), ('run', 'nom')])

    def test_variant_applies_only_once_or_not_at_all(self):
        self.assertEqual(r2.apply_variant('x abstol=1e-9 y', 'abstol'), 'x abstol=1e-8 y')
        self.assertIsNone(r2.apply_variant('x abstol=1e-8 y', 'abstol'))

    def test_only_pinned_aborts_enter_the_ladder(self):
        states = {('t2', 'nom'): 'ABORTED', ('e12lo', 'nom'): 'COMPLETE'}
        with mock.patch.object(r2, 'pinned_status', lambda w, l, n: {'status': states.get((l, n), 'COMPLETE')}), \
                mock.patch.object(r2.t1, 'control_gate', lambda w: {'verdict': 'REPRODUCED'}):
            self.assertEqual(r2.aborted_pinned('w'), [('t2', 'nom')])
        with mock.patch.object(r2, 'pinned_status', lambda w, l, n: {'status': states.get((l, n), 'COMPLETE')}), \
                mock.patch.object(r2.t1, 'control_gate', lambda w: {'verdict': 'NOT REPRODUCED'}):
            self.assertEqual(r2.aborted_pinned('w'), [])

    def test_a_baseline_abort_brings_its_dependent_case(self):
        states = {('e12lo', 'nom'): 'ABORTED', ('base', 'reR20'): 'ABORTED', ('t2hi', 'nom'): 'NOT RUN',
                  ('e12hi', 'nom'): 'ABORTED'}
        with mock.patch.object(r2, 'pinned_status', lambda w, l, n: {'status': states.get((l, n), 'COMPLETE')}), \
                mock.patch.object(r2.t1, 'control_gate', lambda w: {'verdict': 'REPRODUCED'}):
            # t2lo enters through its aborted corner baseline; corners never enter as cases; t2hi never ran;
            # reR20 has no anchor
            self.assertEqual(r2.aborted_pinned('w'), [('t2lo', 'nom')])
            self.assertEqual(r2.unanchored('w'), [('t2load', 'reR20')])

    def test_a_step_applies_only_to_a_chain_that_carries_its_option(self):
        decks = {('t2', 'adv'): 'x rshunt=1e9', ('run', 'adv'): 'x rshunt=1e9',
                 ('t2', 'nom'): 'x rshunt=1e10', ('run', 'nom'): 'x rshunt=1e10'}
        self.assertFalse(r2.applicable(decks, ('t2', 'adv'), 'rshunt'))
        self.assertTrue(r2.applicable(decks, ('t2', 'nom'), 'rshunt'))

    def test_variant_no_load_reuses_the_pinned_judging_without_a_verdict(self):
        calls = []

        def judged(work, base_run, label, name, judge, baseline, r_c_ohm, detail):
            calls.append((label, name, baseline, r_c_ohm))
            return {'status': 'COMPLETE', 'passes': False, 'rules': {'6 x': False}}
        with mock.patch.object(r2, 'reference_match', lambda *a: {'matches': True}), \
                mock.patch.object(r2, 'pinned_status', lambda w, l, n: {'status': 'COMPLETE'}), \
                mock.patch.object(r2.t1, 'status', lambda w, l, n: {'run': None}), \
                mock.patch.object(r2.t1, 'no_load_case', judged):
            row = r2.variant_case('w', ('t2', 'adv'), 1)
        self.assertEqual(calls, [('v-abstol-t2', 'adv', ('v-abstol-run', 'adv'), r2.R_C_OHM)])
        self.assertEqual(row['verdict'], r2.VARIANT_VERDICT)
        self.assertNotIn('passes', row)
        self.assertIs(row['all_rules_hold'], False)

    def test_a_step_that_does_not_apply_writes_nothing(self):
        decks = {('t2', 'adv'): 'x rshunt=1e9', ('run', 'adv'): 'x rshunt=1e9'}
        with mock.patch.object(r2, 'aborted_pinned', lambda w: [('t2', 'adv')]), \
                mock.patch.object(r2, 'resolved', lambda w, c, k: None), \
                mock.patch.object(r2, 'pinned_decks', lambda: decks):
            self.assertEqual(r2.variant_plan('w', 2), {})

    def test_no_plan_without_aborts(self):
        with mock.patch.object(r2, 'aborted_pinned', lambda w: []):
            self.assertEqual(r2.variant_plan('w', 1), {})

    def test_variant_verdict_is_never_pass_or_fail(self):
        self.assertNotIn(r2.VARIANT_VERDICT, ('PASS', 'FAIL'))


class RulesTests(unittest.TestCase):
    def test_tolerance_is_the_convergence_tolerance(self):
        self.assertAlmostEqual(rules.tolerance(-0.09715653), 107.157e-6, places=9)
        self.assertAlmostEqual(rules.tolerance(-12.14195474), 12.15195e-3, places=7)

    def test_attempt1_numbers_under_the_revision(self):
        base = (-0.09715653351, -0.00766395804)
        self.assertFalse(rules.within_tolerance((-0.09729197807, -0.0076614218), base))
        self.assertTrue(rules.within_tolerance((-0.0971687655, -0.0076682505), base))
        self.assertTrue(rules.within_tolerance((-0.0972121684, -0.0076703575), base))

    def test_contract_screens(self):
        rows = [(t * 1e-4, 0.2, 0.79, -1.49, 0, 0, 0, 0) for t in range(399, 1112)]
        record = {'times': [r[0] for r in rows], 'rows': rows}
        self.assertTrue(all(s['passes'] for s in rules.contract_screens(record).values()))
        rows = [(t, a, 0.81, c, *rest) for t, a, _, c, *rest in rows]
        record = {'times': [r[0] for r in rows], 'rows': rows}
        self.assertFalse(rules.contract_screens(record)['+5']['passes'])


if __name__ == '__main__':
    unittest.main()
