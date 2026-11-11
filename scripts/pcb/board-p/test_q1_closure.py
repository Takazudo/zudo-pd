"""Regression and tamper controls for the Board P r3 Q1 closure screen (q1-closure.py)."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('q1_closure', HERE / 'q1-closure.py')
q1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q1)

INPUTS = json.loads((HERE / 'q1-closure-inputs.json').read_text())
RESULT = q1.evaluate(INPUTS)


def case(cap_id, vbus, vpl, ctol):
    cap = next(c for c in RESULT['capacitors'] if c['id'] == cap_id)
    return next(k for k in cap['cases'] if (k['vbus_p_v'], k['v_plateau_v'], k['c_tolerance_factor']) == (vbus, vpl, ctol))


class ReproducesRecordedScreen(unittest.TestCase):
    """Fitted C36 must reproduce the 2026-11-11 screen in manufacturing/pd20-evidence-research.md (PR #252)."""

    ROWS = [  # vbus, plateau, tolerance, C36 at start uF, peak V/ms, Ipk 186/250 A, Ppk 186/250 W, ramp ms, avg V/ms
        (20.0, 3.5, 1.0, 0.183, 19.2, 3.57, 4.79, 71, 96, 3.21, 6.2),
        (20.0, 1.5, 1.0, 0.161, 24.5, 4.56, 6.13, 91, 123, 2.47, 8.1),
        (21.0, 1.5, 1.0, 0.151, 27.4, 5.10, 6.86, 107, 144, 2.38, 8.8),
        (21.0, 1.5, 0.9, 0.136, 30.5, 5.67, 7.62, 119, 160, 2.15, 9.8),
    ]

    def test_rows(self):
        for vbus, vpl, tol, c0, pk, i186, i250, p186, p250, ramp, avg in self.ROWS:
            k = case('current', vbus, vpl, tol)
            with self.subTest(vbus=vbus, vpl=vpl, tol=tol):
                self.assertAlmostEqual(k['c36_at_start_uf'], c0, delta=0.0015)
                self.assertAlmostEqual(k['peak_slew_v_per_ms'], pk, delta=0.06)
                self.assertAlmostEqual(k['banks']['186uF']['peak_inrush_a'], i186, delta=0.01)
                self.assertAlmostEqual(k['banks']['250uF']['peak_inrush_a'], i250, delta=0.01)
                self.assertAlmostEqual(k['banks']['186uF']['q1_peak_power_w'], p186, delta=0.6)
                self.assertAlmostEqual(k['banks']['250uF']['q1_peak_power_w'], p250, delta=0.6)
                self.assertAlmostEqual(k['ramp_to_vbus_ms'], ramp, delta=0.02)
                self.assertAlmostEqual(k['average_slew_v_per_ms'], avg, delta=0.06)
                self.assertEqual(k['peak_slew_vs_adopted'], 'EXCEEDS')

    def test_energy_is_half_cv_squared(self):
        k = case('current', 21.0, 1.5, 1.0)
        self.assertAlmostEqual(k['banks']['186uF']['q1_energy_mj'], 0.5 * 186e-6 * 21 ** 2 * 1e3, delta=0.05)
        self.assertAlmostEqual(k['banks']['250uF']['q1_energy_mj'], 0.5 * 250e-6 * 21 ** 2 * 1e3, delta=0.05)

    def test_most_fitted_cases_exceed_u2_iol_min(self):
        cap = next(c for c in RESULT['capacitors'] if c['id'] == 'current')
        flags = [b['inrush_vs_u2_iol_min'] for k in cap['cases'] for b in k['banks'].values()]
        self.assertGreater(flags.count('EXCEEDS'), len(flags) // 2)


class NeverAnAcceptance(unittest.TestCase):
    def test_verdict_and_soa_stay_screen_only(self):
        self.assertEqual(RESULT['verdict'], 'SCREEN ONLY - NOT AN ACCEPTANCE')
        self.assertEqual(RESULT['data_class'], 'TYPICAL')
        text = json.dumps(RESULT)
        for word in ('"PASS', 'ACCEPTED', '"QUALIFIED'):
            self.assertNotIn(word, text)
        for cap in RESULT['capacitors']:
            for k in cap['cases']:
                for b in k['banks'].values():
                    self.assertTrue(b['soa_status'].startswith('OPEN'))

    def test_candidates_are_labelled_proposed(self):
        status = {c['id']: c['status'] for c in RESULT['capacitors']}
        self.assertEqual(status, {'current': 'FITTED', 'option-a': 'PROPOSED', 'option-b': 'PROPOSED'})
        for cap in RESULT['capacitors']:
            if cap['status'] == 'PROPOSED':
                self.assertIn('not adopted', cap['label'])

    def test_open_items_name_missing_guaranteed_data(self):
        joined = ' '.join(RESULT['open_items'])
        for needle in ('typical', 'UNSOURCED', 'NOT RUN', 'temperature'):
            self.assertIn(needle, joined)


class TamperControls(unittest.TestCase):
    def test_changed_curve_point_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        x, y = bad['capacitors'][0]['series']['points'][40]
        bad['capacitors'][0]['series']['points'][40] = [x, str(float(y) + 5.0)]
        with self.assertRaisesRegex(q1.InputError, 'canonical series hash'):
            q1.evaluate(bad)

    def test_removed_owner_source_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['capacitors'][0]['source_id'] = 'src-c15849-dcbias-removed'
        with self.assertRaisesRegex(q1.InputError, 'missing or unavailable'):
            q1.evaluate(bad)

    def test_candidate_without_manufacturer_url_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['capacitors'][1].pop('url')
        with self.assertRaisesRegex(q1.InputError, 'URL or page hash'):
            q1.evaluate(bad)

    def test_soa_source_hash_mismatch_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['q1_soa']['sha256'] = '0' * 64
        with self.assertRaisesRegex(q1.InputError, 'SOA source'):
            q1.evaluate(bad)

    def test_missing_iol_fact_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['u2_iol_min_a']['fact_id'] = 'fact-c1849461-iol-removed'
        with self.assertRaisesRegex(q1.InputError, 'missing from'):
            q1.evaluate(bad)

    def test_unknown_status_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['capacitors'][1]['status'] = 'ADOPTED'
        with self.assertRaisesRegex(q1.InputError, 'FITTED or PROPOSED'):
            q1.evaluate(bad)


if __name__ == '__main__':
    unittest.main()
