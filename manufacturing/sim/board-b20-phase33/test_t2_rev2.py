import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

import gap_sensitivity as gap
import rules_revision as rules
import t2_clamp as t1
import t2_rev2 as r2

# Placeholder values for structural tests only; they are not a part and never reach a prepared deck.
FAKE = {'owner': 'test-only', 'mpn': 'TEST-ONLY', 'ir_max_a': 1e-10,
        'model': {'IS': 1e-14, 'N': 1.8, 'RS': 10, 'CJO': 3e-13, 'VJ': 0.7, 'M': 0, 'BV': 50, 'IBV': 1e-9},
        'rows': {p: 'test' for p in r2.MODEL_PARAMETERS + ('ir_max_a',)}}


class DiodeSlotTests(unittest.TestCase):
    def test_refuses_without_a_sourced_diode(self):
        self.assertIsNone(r2.DIODE)
        with self.assertRaisesRegex(ValueError, 'not sourced'):
            r2.t2_block()

    def test_refuses_untraced_parameters(self):
        partial = {**FAKE, 'rows': {'IS': 'x'}}
        with mock.patch.object(r2, 'DIODE', partial), self.assertRaisesRegex(ValueError, 'untraced'):
            r2.t2_block()


@mock.patch.object(r2, 'DIODE', FAKE)
class BlockTests(unittest.TestCase):
    def test_rev2_changes_only_the_registered_elements(self):
        old, new = set(t1.t2_block()), set(r2.t2_block())
        removed = {x.split()[0] for x in old - new}
        added = {x.split()[0] for x in new - old}
        self.assertEqual(removed, {'*', 'DT2K', 'DT2C', 'BT2G'})
        self.assertEqual(added, {'*', 'DT2K', 'DT2C', 'BT2G', '.model', 'BT2KL', 'BT2CL', 'RT2D', 'CT2D', 'BT2D'})

    def test_diodes_use_the_traced_model(self):
        block = '\n'.join(r2.t2_block())
        self.assertEqual(set(re.findall(r'^D\S+ \S+ \S+ (\S+)$', block, re.M)), {'DT2X'})
        self.assertIn('M=0', r2.model_line())
        self.assertNotIn('DBODY', block)

    def test_leakage_flows_cathode_to_anode(self):
        block = r2.t2_block()
        self.assertIn('BT2CL t2o t2c I=1e-10*tanh(max(v(t2o,t2c),0)/0.05)', block)
        self.assertIn('BT2KL t2k m12_drv I=1e-10*tanh(max(v(t2k,m12_drv),0)/0.05)', block)

    def test_connection_is_delayed_and_break_before_make(self):
        block = '\n'.join(r2.t2_block())
        self.assertIn('(1-tanh((v(t2d)-0.4)*30))', block)
        self.assertIn('BT2D t2g 0 I=v(t2g,0)*(1/3.5)*0.5*(1+tanh((v(t2d)-0.6)*30))', block)
        self.assertLess(r2.CONNECT_BELOW_V, r2.PARK_ABOVE_V)

    def test_inert_control_returns_the_clamp_to_gnd_and_keeps_the_rest(self):
        a, b = r2.t2_block(), r2.t2_block(inert=True)
        diff = {x.split()[0] for x in set(a) ^ set(b)}
        self.assertEqual(diff, {'*', 'BT2G'})
        self.assertTrue(any(x.startswith('BT2G t2g 0 ') for x in b))

    def test_delay_numbers(self):
        import math
        tau = 100e3 * 47e-9
        self.assertAlmostEqual(tau * math.log(5 / 0.4) * 1e3, 11.87, places=2)


class RulesTests(unittest.TestCase):
    def test_tolerance_is_the_convergence_tolerance(self):
        self.assertAlmostEqual(rules.tolerance(-0.09715653), 107.157e-6, places=9)
        self.assertAlmostEqual(rules.tolerance(-12.14195474), 12.15195e-3, places=7)

    def test_attempt1_numbers_under_the_revision(self):
        # Rule 6(b): 135.4 uV beyond a -97.157 mV minimum still fails; 12.2 / 55.6 uV (C1 g20 / g16) pass.
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
        with mock.patch.object(r2, 'pinned_status', lambda w, l, n: {'status': states.get((l, n), 'COMPLETE')}):
            self.assertEqual(r2.aborted_pinned('w'), [('t2', 'nom')])

    def test_no_plan_without_aborts(self):
        with mock.patch.object(r2, 'aborted_pinned', lambda w: []):
            self.assertEqual(r2.variant_plan('w', 1), {})

    def test_variant_verdict_is_never_pass_or_fail(self):
        self.assertNotIn(r2.VARIANT_VERDICT, ('PASS', 'FAIL'))


if __name__ == '__main__':
    unittest.main()
