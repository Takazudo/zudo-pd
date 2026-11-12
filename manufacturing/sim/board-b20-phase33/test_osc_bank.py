import tempfile
from pathlib import Path
import unittest
from unittest import mock

import gap_sensitivity as gap
import osc_bank as ob
import t2_rev2


class DeckTests(unittest.TestCase):
    def test_eighteen_single_deck_labels(self):
        cases = ob.derive_cases()
        self.assertEqual(len(cases), 18)
        self.assertEqual(cases['nom-adv'][0], 'adv')
        self.assertEqual(cases['lo-e12hi'][0], 'nom')

    def test_only_the_bank_differs_from_the_ceiling_deck(self):
        rev2 = t2_rev2.derive_cases()
        for case in ('e12lo', 'e12hi', 'e5lo', 'e5hi'):
            name, text = ob.base_deck(case)
            self.assertEqual(text, rev2[case]['nom'], case)
        for lbl, (name, text) in ob.derive_cases().items():
            scale, case = lbl.split('-', 1)
            base = ob.base_deck(case)[1]
            changed = [(a, b) for a, b in zip(base.splitlines(), text.splitlines()) if a != b]
            self.assertEqual(len(base.splitlines()), len(text.splitlines()))
            self.assertEqual(sorted(a.split()[0] for a, _ in changed), ['CL12', 'CL5', 'CLN'], lbl)

    def test_bank_values(self):
        text = ob.derive_cases()['lo-nom'][1]
        for line in ('CL12 p12_out cl12 39.92u', 'CL5 p5_out cl5 19.6u', 'CLN 0 cln 33.76u'):
            self.assertIn(line + '\n', text)
        text = ob.derive_cases()['hi-adv'][1]
        for line in ('CL12 p12_out cl12 59.88u', 'CL5 p5_out cl5 29.4u', 'CLN 0 cln 50.64u'):
            self.assertIn(line + '\n', text)

    def test_variants_change_one_option(self):
        name, text = ob.derive_cases()['nom-nom']
        self.assertEqual(ob.apply_variant(text, 'abstol'), text.replace('abstol=1e-9', 'abstol=1e-8'))
        self.assertIsNone(ob.apply_variant(ob.derive_cases()['nom-adv'][1], 'rshunt'))   # adv already rshunt=1e9


class VariantPlanTests(unittest.TestCase):
    def test_only_pinned_aborts_enter_and_resolved_ones_leave(self):
        states = {('nom-nom', 'nom'): 'ABORTED', ('nom-adv', 'adv'): 'COMPLETE', ('v-abstol-nom-nom', 'nom'): 'NOT RUN'}

        def status(work, lbl, name):
            return {'status': states.get((lbl, name), 'COMPLETE' if not lbl.startswith('v-') else 'NOT RUN')}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(ob, 'status', side_effect=status), \
                mock.patch.object(ob, 'write', return_value='x'):
            self.assertEqual(ob.variant_plan(tmp, 1), {'v-abstol-nom-nom': 'nom'})
            states[('v-abstol-nom-nom', 'nom')] = 'COMPLETE'
            self.assertEqual(ob.variant_plan(tmp, 2), {})


class MetricTests(unittest.TestCase):
    def record(self):
        # +5 V rises 0 -> 0.6 V; -12 V falls 0 -> -1.0 V; 1 ms samples inside the screen window.
        times = [0.050 + k * 1e-3 for k in range(11)]
        rows = [[t, 0.0, min(0.06 * k, 0.6), -0.1 * k] for k, t in enumerate(times)]
        side = [[t, 0.0, 0.1 * (k % 3), -0.1 * k + 0.01 * k] for k, t in enumerate(times)]
        return {'rows': rows, 'side': side}

    def test_minus12_current_sign_and_region_split(self):
        m = ob.rail_metrics(self.record(), '-12')
        self.assertAlmostEqual(m['peak_slope_in_region_v_per_ms'], 0.1)
        self.assertAlmostEqual(m['peak_slope_above_region_v_per_ms'], 0.1)
        self.assertAlmostEqual(m['peak_current_in_region_a'], 0.01 * 7 / 0.05)
        self.assertGreater(m['charge_in_region_c'], 0)

    def test_plus5_region(self):
        m = ob.rail_metrics(self.record(), '+5')
        self.assertAlmostEqual(m['peak_slope_in_region_v_per_ms'], 0.06)
        self.assertAlmostEqual(m['peak_current_in_region_a'], 0.2 / 0.05)

    def test_half_width(self):
        self.assertAlmostEqual(ob.half_width([0, 1, 2, 3, 4], [0, 1, 2, 1, 0], 2), 2)


class AnalyzeTests(unittest.TestCase):
    def test_unknown_when_nothing_completes(self):
        with mock.patch.object(ob, 'status', return_value={'status': 'ABORTED', 'abort': {'cause': 'x'}}):
            out = ob.analyze('/w')
        self.assertEqual(len(out['unknown']), 18)
        self.assertEqual(out['worst_measured'], {})


class CriteriaTests(unittest.TestCase):
    def test_criteria_states_the_scope(self):
        text = (ob.HERE / ob.CRITERIA).read_text()
        for phrase in ('not a verdict run', '49.9 / 24.5 / 42.2', '× 0.8', 'matched-variant', 'not folded'):
            self.assertIn(phrase, text)

    def test_status_reads_the_bank_tree(self):
        with mock.patch.object(gap, 'case_status', return_value={'status': 'NOT RUN'}) as cs:
            ob.status('/w', 'lo-nom', 'nom')
        cs.assert_called_once_with(Path('/w/bank/lo-nom'), 'nom')


if __name__ == '__main__':
    unittest.main()
