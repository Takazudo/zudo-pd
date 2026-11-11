import json
import math
from pathlib import Path
import re
import tempfile
import unittest

import extract_reference as ex
import gap_sensitivity as gap
import t2_clamp as t2

HERE = Path(__file__).resolve().parent
CRITERIA = (HERE / 'd1-t2-criteria.md').read_text()


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = t2.derive_cases()
        cls.executed = {k: v['executed'] for k, v in ex.derive_decks().items()}

    def test_labels_and_names_agree(self):
        self.assertEqual(tuple(self.cases), t2.LABEL_ORDER)
        names = t2.derive_case_names()
        for label in t2.LABEL_ORDER:
            self.assertEqual(sorted(self.cases[label]), sorted(names[label]), label)

    def test_loaded_baselines_are_the_accepted_decks(self):
        for name in t2.LOADED:
            self.assertEqual(t2.sha(self.cases['base'][name].encode()), t2.executed_attempt(name)['deck_sha256'])

    def diff(self, base, text):
        return set(base.splitlines()) - set(text.splitlines()), set(text.splitlines()) - set(base.splitlines())

    def test_t2_changes_only_the_registered_lines(self):
        base = t2.no_load(self.executed['nom'], 'nom')
        removed, added = self.diff(base, self.cases['t2']['nom'])
        self.assertEqual(removed, {t2.Q6_LINE[0]})
        expected = set(t2.t2_block()) | set(t2.Q6_LINE[1].splitlines()) | {t2.t2_line('nom')}
        self.assertEqual(added, expected)
        self.assertNotIn('.include ../lib/new', self.cases['t2']['nom'])

    def test_the_block_uses_only_existing_models(self):
        block = '\n'.join(t2.t2_block())
        self.assertEqual(set(re.findall(r'^X\S+ .* (\S+)$', block, re.M)), {'OPAx187'})
        self.assertEqual(set(re.findall(r'^D\S+ \S+ \S+ (\S+)$', block, re.M)), {'DBODY'})
        for model in ('OPAx187', 'DBODY'):
            self.assertIn(model, self.executed['nom'])

    def test_inert_control_differs_only_in_the_clamp_return(self):
        removed, added = self.diff(self.cases['t2']['adv'], self.cases['ctrl']['adv'])
        self.assertEqual(len(removed), 2)  # the clamp switch and the comment line
        self.assertTrue(any(x.startswith('BT2G t2g 0 ') for x in added))
        self.assertTrue(any(x.startswith('BT2G t2g trk12n_fb ') for x in removed))

    def test_corners_move_only_their_offset(self):
        nom = t2.no_load(self.executed['nom'], 'nom')
        for label, (rail, which) in t2.CORNER_CASES.items():
            removed, added = self.diff(nom, self.cases[label]['nom'])
            self.assertEqual(removed, {t2.OFFSET_LINES[rail]})
            self.assertEqual(len(added), 1)
            self.assertTrue(next(iter(added)).endswith(f' {t2.CORNER_VO_V[which]:g}'))
        removed, added = self.diff(self.cases['t2']['nom'], self.cases['t2hi']['nom'])
        self.assertEqual(removed, {'VO3 m12_g m12_gi 0'})
        self.assertEqual(added, {'VO3 m12_g m12_gi 0.54'})

    def test_loaded_t2_decks_keep_their_solver_variant(self):
        for name, swap in t2.LOADED.items():
            removed, added = self.diff(self.cases['base'][name], self.cases['t2load'][name])
            self.assertEqual(removed, {t2.Q6_LINE[0]})
            if swap:
                self.assertIn(swap[1], self.cases['t2load'][name])

    def test_no_solver_option_changes(self):
        for label, decks in self.cases.items():
            for name, text in decks.items():
                options = [x for x in text.splitlines() if x.startswith(('.options', '.tran'))]
                source = self.cases['base'][name] if name in t2.LOADED else self.executed[name]
                self.assertEqual(options, [x for x in source.splitlines() if x.startswith(('.options', '.tran'))],
                                 f'{label}/{name}')


class CriteriaTests(unittest.TestCase):
    def test_numbers_in_step(self):
        for text in ('**0.5 ×**', '**10 mV**', '**50 mV**', '**0.1 µA**', '95–115 ms', '110–115 ms', '1e-3·',
                     '30–40 ms and 245–250 ms', 'tanh × 30', '1.47 V/ms', '0.265 A'):
            self.assertIn(text, CRITERIA)
        self.assertEqual(t2.CHANNEL_FRACTION_MAX, 0.5)
        self.assertEqual(t2.LIMIT_CYCLE_PP_MAX_V, 10e-3)
        self.assertEqual(t2.RELEASE_STEP_MAX_V, 50e-3)
        self.assertEqual(t2.ENGAGED_MIN_A, 0.1e-6)
        self.assertEqual(t2.HOLD_RESET_MAX_V, 10e-3)
        self.assertEqual(t2.IDLE_WINDOW_S, (95e-3, 115e-3))
        self.assertEqual(t2.RELTOL, 1e-3)
        self.assertEqual(t2.CORNER_VO_V, {'lo': -0.66, 'hi': 0.54})
        self.assertIn('(v(ennd)-1.2)*30', t2.CAPTURE_GATE)
        for key, (value, _) in t2.VALUES.items():
            self.assertIn(value, '\n'.join(t2.t2_block()), key)

    def test_held_d1_and_plus5_rejection_are_stated(self):
        self.assertIn('D1 stays held until +5 V has an answer', CRITERIA)
        self.assertIn('T2 on +5 V is REJECTED by construction', CRITERIA)
        self.assertIn('recorded limitation, not a pass', CRITERIA)

    def test_recorded_failure_matches_the_reference_record(self):
        record = json.loads((HERE / 'd1-gap-attempt2-20261111.json').read_text())
        text = json.dumps(record)
        self.assertIn(repr(t2.RECORDED_D1['slope_v_per_ms']), text)
        self.assertIn(repr(t2.RECORDED_D1['current_a']), text)


class MeasurementTests(unittest.TestCase):
    def test_detrended_peak_to_peak(self):
        times = [k * 10e-6 for k in range(25001)]
        line = [0.5 * t for t in times]
        self.assertLess(t2.detrended_pp(times, line, 0.095, 0.115), 1e-9)
        for amplitude, over in ((0.003, False), (0.006, True)):
            wobble = [v + amplitude * math.sin(2 * math.pi * 300 * t) for t, v in zip(times, line)]
            pp = t2.detrended_pp(times, wobble, 0.095, 0.115)
            self.assertAlmostEqual(pp, 2 * amplitude, delta=0.25 * amplitude)  # the fit absorbs part of a sine
            self.assertEqual(pp > t2.LIMIT_CYCLE_PP_MAX_V, over)

    def test_rules_follow_the_bounds(self):
        m = {'idle_channel_current_max_a': 0.4e-6, 'idle_output_drain_min_a': 1.0e-6, 'limit_cycle_driver_pp_v': 9e-3,
             'release_step_v': -0.011, 'clamp_engaged': True, 'hold_while_disabled_max_v': 1e-3,
             'hold_after_disable_max_v': 1e-3}
        self.assertTrue(all(t2.t2_rules(m).values()))
        for key, value in (('idle_channel_current_max_a', 0.51e-6), ('limit_cycle_driver_pp_v', 11e-3),
                           ('release_step_v', 0.06), ('release_step_v', None), ('clamp_engaged', False),
                           ('hold_after_disable_max_v', 0.02)):
            bad = dict(m, **{key: value})
            self.assertFalse(all(t2.t2_rules(bad).values()), key)

    def test_t2_metrics_on_a_synthetic_record(self):
        times = [k * 10e-6 for k in range(25001)]
        drv = [-12.14 + (2.66 if 0.06 <= t < 0.07 else (1.66 if 0.07 <= t < 0.117 else 0.0)) for t in times]
        series = {c: [0.0] * len(times) for c in t2.T2_COLUMNS}
        series['m12_drv'] = drv
        series['m12_pre'] = [-12.14] * len(times)
        series['t2h'] = [-12.14 + (2.34 if 0.065 <= t < 0.24 else 0.0) for t in times]
        series['mabs_n'] = [0.0] * len(times)
        series['trk12n'] = [-0.0107] * len(times)
        series['t2c'] = [-1.0 if 0.08 <= t < 0.118 else 0.5 for t in times]
        series['t2g'] = [-1.0 + 1.07e-6 * 499e3 if 0.08 <= t < 0.118 else 0.5 for t in times]
        series['i_VIQ6'] = [0.03e-6] * len(times)
        rows = [[t, 0, 0, -0.097] + [0] * 8 for t in times]
        m = t2.t2_metrics({'t2': (times, series), 'rows': rows, 'gap': None})
        self.assertAlmostEqual(m['engaged_clamp_current_a'], 1.07e-6, delta=1e-9)
        self.assertAlmostEqual(m['release_ms'], 118.0, delta=0.01)
        self.assertAlmostEqual(m['idle_output_drain_min_a'], 0.097 / 100e3 + (0.097 - 0.0107) / 750e3, delta=1e-12)
        self.assertAlmostEqual(m['idle_driver_below_peak_v'], 1.0, delta=1e-6)
        self.assertGreater(m['hold_while_disabled_max_v'], -1e-9)
        rules = t2.t2_rules(m)
        self.assertTrue(rules['10 idle channel current at most half the output drain'])
        self.assertTrue(rules['13 clamp engaged while idle'])


class WorkflowTests(unittest.TestCase):
    def test_workflow_runs_the_labels_in_order_and_opt_in(self):
        text = (HERE.parents[2] / '.github/workflows/phase33-d1-reference.yml').read_text()
        self.assertIn('for label in ' + ' '.join(t2.LABEL_ORDER) + '; do', text)
        self.assertIn("if: inputs.t2_evaluation && steps.identity.outcome == 'success'", text)
        self.assertIn('t2_clamp.py" check-run', text)
        self.assertIn('--original-only', text)


class StatusTests(unittest.TestCase):
    def test_t2_labels_wait_for_a_reproduced_control(self):
        with tempfile.TemporaryDirectory() as work:
            for label in t2.T2_LABELS:
                self.assertEqual(t2.pending(work, label), [])
            self.assertEqual(t2.pending(work, 'ctrl'), ['adv'])
            self.assertEqual(t2.pending(work, 'base'), list(t2.LOADED))
            self.assertEqual(t2.control(work)['verdict'], 'NOT EVALUATED')


if __name__ == '__main__':
    unittest.main()
