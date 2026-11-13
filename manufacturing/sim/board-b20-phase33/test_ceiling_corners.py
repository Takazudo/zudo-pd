import tempfile
from pathlib import Path
import unittest
from unittest import mock

import ceiling_corners as cc
import gap_sensitivity as gap
import osc_bank as ob


class DeckTests(unittest.TestCase):
    def test_labels_and_entries(self):
        cases = cc.derive_cases()
        self.assertEqual(list(cases), ['nom', 'adv', 'e5lo', 'e5hi', 'e12hi', 'hot-nom', 'hot-adv', 'hot-e12hi', 'hot-e5hi'])
        self.assertEqual({k for k, v in cases.items() if v[2] == 'variant'}, {'e5lo', 'e5hi', 'e12hi'})

    def test_cold_decks_are_the_ceiling_bank_baseline(self):
        for case in ('nom', 'adv', 'e5lo', 'e5hi', 'e12hi'):
            self.assertEqual(cc.derive_cases()[case][:2], ob.base_deck(case))
            self.assertIn('CL5 p5_out cl5 120u\n', cc.derive_cases()[case][1])

    def test_hot_adds_only_one_temp_line(self):
        for case in cc.HOT:
            cold = cc.derive_cases()[case][1].splitlines()
            hot = cc.derive_cases()[cc.hot_label(case)][1].splitlines()
            self.assertEqual(len(hot), len(cold) + 1)
            k = hot.index('.temp 82.1')
            self.assertEqual(hot[:k] + hot[k + 1:], cold)
            self.assertTrue(hot[k + 1].startswith('.options method=trap'))

    def test_temperature_refuses_a_second_temp_line(self):
        with self.assertRaises(ValueError):
            cc.with_temperature('x\n.temp 27\n.options a\n', 'x')


class PlanTests(unittest.TestCase):
    def run_plan(self, states, step):
        def status(work, lbl, name):
            return {'status': states.get(lbl, 'NOT RUN' if lbl.startswith('v-') or lbl in cc.VARIANT_ONLY else 'COMPLETE')}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cc, 'status', side_effect=status), \
                mock.patch.object(cc, 'write', return_value='x'):
            return cc.variant_plan(tmp, step)

    def test_pending_runs_only_pinned_entries(self):
        with mock.patch.object(cc, 'status', return_value={'status': 'NOT RUN'}):
            self.assertEqual(cc.pending('/w', 'e5lo'), [])
            self.assertEqual(cc.pending('/w', 'hot-e5hi'), ['nom'])

    def test_step1_takes_variant_entries_aborted_hot_rows_their_anchors_and_the_cross_check(self):
        plan = self.run_plan({'hot-adv': 'ABORTED'}, 1)
        self.assertEqual(set(plan), {'v-abstol-e5lo', 'v-abstol-e5hi', 'v-abstol-e12hi', 'v-abstol-hot-adv',
                                     'v-abstol-adv', 'v-abstol-nom'})

    def test_step2_keeps_only_unresolved_and_adds_their_anchor(self):
        states = {'hot-e12hi': 'ABORTED', 'v-abstol-e5lo': 'COMPLETE', 'v-abstol-e5hi': 'COMPLETE',
                  'v-abstol-e12hi': 'COMPLETE', 'v-abstol-hot-e12hi': 'ABORTED'}
        self.assertEqual(set(self.run_plan(states, 2)), {'v-rshunt-hot-e12hi', 'v-rshunt-e12hi', 'v-rshunt-nom'})

    def test_adv_has_no_rshunt_variant(self):
        states = {'hot-adv': 'ABORTED', 'v-abstol-hot-adv': 'ABORTED', 'v-abstol-e5lo': 'COMPLETE',
                  'v-abstol-e5hi': 'COMPLETE', 'v-abstol-e12hi': 'COMPLETE'}
        self.assertEqual(self.run_plan(states, 2), {})

    def test_check_run_resolves_variant_labels(self):
        with mock.patch.object(cc, 'status', return_value={'status': 'FAILED'}) as st:
            self.assertEqual(cc.check_run('/w', 'v-abstol-hot-e5hi'), {'nom': 'FAILED'})
        st.assert_called_once_with('/w', 'v-abstol-hot-e5hi', 'nom')


class AnalyzeTests(unittest.TestCase):
    def test_flags_use_the_owner_thresholds(self):
        rows = {'a': {'measured_under': 'pinned', 'rails': {'-12': {'peak_current_in_region_a': 0.301},
                                                            '+5': {'peak_current_in_region_a': 0.139}}}}
        self.assertEqual([f['rail'] for f in cc.flags(rows)], ['-12'])

    def test_hot_rows_compare_only_under_the_same_setting(self):
        def status(work, lbl, name):
            return {'status': {'hot-nom': 'COMPLETE', 'hot-adv': 'ABORTED', 'v-abstol-hot-adv': 'COMPLETE'}.get(
                lbl, 'NOT RUN' if lbl.startswith(('v-', 'hot-')) else 'COMPLETE'), 'run': lbl}
        fake = {'+12': {'x': 1.0}, '+5': {'x': 1.0}, '-12': {'x': 1.0}}
        with mock.patch.object(cc, 'status', side_effect=status), mock.patch.object(cc, 'metrics', return_value=fake):
            out = cc.hot_minus_cold('/w')
        self.assertTrue(out['hot-nom']['comparable'])
        self.assertEqual(out['hot-adv'], {'comparable': False, 'setting': 'abstol',
                                          'why': 'cold anchor NOT RUN under abstol'})
        self.assertFalse(out['hot-e5hi']['comparable'])

    def test_unknown_when_nothing_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(cc, 'status', return_value={'status': 'ABORTED', 'abort': {'cause': 'x'}}):
                out = cc.analyze(tmp)
        self.assertEqual(len(out['unknown']), 9)
        self.assertEqual(out['flags'], [])
        self.assertEqual(out['model_temperature_terms'], {})

    def test_temperature_terms_counts_words_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'lib').mkdir()
            (Path(tmp) / 'lib' / 'm.lib').write_text('.model q nmos (TNOM=27 KT1=-0.1 xtitle=1)\n* temp note\n')
            out = cc.temperature_terms(tmp)['m.lib']
        self.assertEqual((out['tnom'], out['kt1'], out['xti'], out['temp']), (1, 1, 0, 1))


class CriteriaTests(unittest.TestCase):
    def test_criteria_states_the_scope(self):
        text = (ob.HERE / cc.CRITERIA).read_text()
        for phrase in ('not a verdict run', '.temp 82.1', '300 mA on −12 V', '140 mA on +5 V', '43187732133',
                       'not a hot-start verdict', 'same solver'):
            self.assertIn(phrase, text)

    def test_status_reads_the_ceiling_tree(self):
        with mock.patch.object(gap, 'case_status', return_value={'status': 'NOT RUN'}) as cs:
            cc.status('/w', 'hot-nom', 'nom')
        cs.assert_called_once_with(Path('/w/ceiling/hot-nom'), 'nom')


if __name__ == '__main__':
    unittest.main()
