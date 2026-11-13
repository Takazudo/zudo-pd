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
# Pinned here so an edit to the inputs cannot silently re-hash a curve or the SOA read: the PROPOSED page bytes
# are not reproducible (render timestamp), and the SOA points are a 2026-11-11 graph read of DS37038 Fig. 12.
PINNED_CURVES = {
    'previous': '329b040aac94fd3e353874f2ec1d8f50368ab8cd50bc7f2f8a42717ed0da0985',
    'option-a': 'e4fc1166bb2a3297d070cdc5b1791fc5a51b5091b3756cbf876066de25bad42c',
    'option-b': '57951ee5f48a8acb80ccf57cba70db066308977f45172faab1a795fc53f01aca',
}
PINNED_SOA_POINTS = [(1e-4, 17.9), (1e-3, 8.29), (1e-2, 1.17), (1e-1, 0.184), (1.0, 0.083), (10.0, 0.055)]
RESULT = q1.evaluate(INPUTS)


def case(cap_id, vbus, vpl, ctol):
    cap = next(c for c in RESULT['capacitors'] if c['id'] == cap_id)
    return next(k for k in cap['cases'] if (k['vbus_p_v'], k['v_plateau_v'], k['c_tolerance_factor']) == (vbus, vpl, ctol))


class ReproducesRecordedScreen(unittest.TestCase):
    """The superseded 0603 C36 must still reproduce the 2026-11-11 screen in manufacturing/pd20-evidence-research.md (PR #252)."""

    ROWS = [  # vbus, plateau, tolerance, C36 at start uF, peak V/ms, Ipk 186/250 A, Ppk 186/250 W, ramp ms, avg V/ms
        (20.0, 3.5, 1.0, 0.183, 19.2, 3.57, 4.79, 71, 96, 3.21, 6.2),
        (20.0, 1.5, 1.0, 0.161, 24.5, 4.56, 6.13, 91, 123, 2.47, 8.1),
        (21.0, 1.5, 1.0, 0.151, 27.4, 5.10, 6.86, 107, 144, 2.38, 8.8),
        (21.0, 1.5, 0.9, 0.136, 30.5, 5.67, 7.62, 119, 160, 2.15, 9.8),
    ]

    def test_rows(self):
        for vbus, vpl, tol, c0, pk, i186, i250, p186, p250, ramp, avg in self.ROWS:
            k = case('previous', vbus, vpl, tol)
            with self.subTest(vbus=vbus, vpl=vpl, tol=tol):
                self.assertAlmostEqual(k['c36_at_start_uf'], c0, delta=0.0015)
                self.assertAlmostEqual(k['peak_slew_v_per_ms'], pk, delta=0.06)
                self.assertAlmostEqual(k['banks']['186uF']['peak_inrush_a'], i186, delta=0.01)
                self.assertAlmostEqual(k['banks']['250uF']['peak_inrush_a'], i250, delta=0.01)
                self.assertAlmostEqual(k['banks']['186uF']['q1_peak_power_w'], p186, delta=0.6)
                self.assertAlmostEqual(k['banks']['250uF']['q1_peak_power_w'], p250, delta=0.6)
                self.assertAlmostEqual(k['ramp_to_vbus_ms'], ramp, delta=0.02)
                self.assertAlmostEqual(k['average_slew_v_per_ms'], avg, delta=0.06)
                self.assertEqual(k['peak_slew_vs_adopted'], 'TYPICAL_EXCEEDS')

    def test_energy_is_half_cv_squared(self):
        k = case('previous', 21.0, 1.5, 1.0)
        self.assertAlmostEqual(k['banks']['186uF']['q1_energy_mj'], 0.5 * 186e-6 * 21 ** 2 * 1e3, delta=0.05)
        self.assertAlmostEqual(k['banks']['250uF']['q1_energy_mj'], 0.5 * 250e-6 * 21 ** 2 * 1e3, delta=0.05)

    def test_most_superseded_cases_exceed_u2_iol_min(self):
        cap = next(c for c in RESULT['capacitors'] if c['id'] == 'previous')
        flags = [b['inrush_vs_u2_iol_min'] for k in cap['cases'] for b in k['banks'].values()]
        self.assertGreater(flags.count('TYPICAL_EXCEEDS'), len(flags) // 2)

    def ratios(self, cap_id):
        cap = next(c for c in RESULT['capacitors'] if c['id'] == cap_id)
        return [b['soa_ratio_peak_rectangular'] for k in cap['cases'] for b in k['banks'].values()]

    def test_soa_screen_ranges_match_the_record(self):
        previous = self.ratios('previous')
        self.assertAlmostEqual(min(previous), 0.54, delta=0.005)
        self.assertAlmostEqual(max(previous), 0.86, delta=0.005)
        options = self.ratios('option-a') + self.ratios('option-b')
        self.assertAlmostEqual(min(options), 1.66, delta=0.005)
        self.assertAlmostEqual(max(options), 2.64, delta=0.005)

    def test_option_rows(self):
        for cap_id, pk, i250, ramp in (('option-a', 4.49, 1.122, 4.962), ('option-b', 4.64, 1.159, 4.805)):
            k = case(cap_id, 20.0, 1.5, 1.0)
            with self.subTest(cap_id=cap_id):
                self.assertAlmostEqual(k['peak_slew_v_per_ms'], pk, delta=0.02)
                self.assertAlmostEqual(k['banks']['250uF']['peak_inrush_a'], i250, delta=0.005)
                self.assertAlmostEqual(k['ramp_to_vbus_ms'], ramp, delta=0.01)


class AdoptedOptionAScreen(unittest.TestCase):
    """D10 (2026-11-12) adoption limits for the fitted C36: SOA ratio >= 1.2 and peak inrush below U2 I(OL) min at every corner."""

    def test_fitted_is_option_a_and_clears_the_adoption_limits(self):
        fitted = [c for c in RESULT['capacitors'] if c['status'] == 'FITTED']
        self.assertEqual([c['id'] for c in fitted], ['option-a'])
        self.assertEqual(len(fitted[0]['cases']), 8)
        for k in fitted[0]['cases']:
            self.assertNotEqual(k['peak_slew_vs_adopted'], 'TYPICAL_EXCEEDS')
            for b in k['banks'].values():
                self.assertGreaterEqual(b['soa_ratio_peak_rectangular'], 1.2)
                self.assertLess(b['peak_inrush_a'], RESULT['u2_iol_min_a'])
                self.assertEqual(b['inrush_vs_u2_iol_min'], 'TYPICAL_BELOW')
                self.assertEqual(b['inrush_vs_adopted_max'], 'TYPICAL_WITHIN')

    def test_tolerance_corner_cites_the_fitted_part(self):
        self.assertEqual(INPUTS['circuit']['c_nominal_tolerance']['fact_id'], 'fact-c1848-tolerance')


class PinnedInputs(unittest.TestCase):
    def test_curve_hashes_are_pinned(self):
        self.assertEqual({c['id']: c['canonical_sha256'] for c in INPUTS['capacitors']}, PINNED_CURVES)
        for cap in INPUTS['capacitors']:
            self.assertEqual(q1.canonical_sha256(cap['series']), PINNED_CURVES[cap['id']])

    def test_soa_points_are_pinned(self):
        self.assertEqual([(p['pw_s'], p['id_a']) for p in INPUTS['q1_soa']['points']], PINNED_SOA_POINTS)
        self.assertEqual(INPUTS['q1_soa']['vds_v'], 20.0)


class NeverAnAcceptance(unittest.TestCase):
    def test_verdict_and_soa_stay_screen_only(self):
        self.assertEqual(RESULT['verdict'], 'SCREEN ONLY - NOT AN ACCEPTANCE')
        self.assertEqual(RESULT['data_class'], 'TYPICAL')
        text = json.dumps(RESULT)
        for word in ('"PASS', 'ACCEPTED', '"QUALIFIED', '"WITHIN', '"BELOW', '"EXCEEDS'):
            self.assertNotIn(word, text)
        for cap in RESULT['capacitors']:
            for k in cap['cases']:
                for b in k['banks'].values():
                    self.assertTrue(b['soa_status'].startswith('OPEN'))

    def test_candidates_are_labelled_proposed(self):
        status = {c['id']: c['status'] for c in RESULT['capacitors']}
        self.assertEqual(status, {'previous': 'SUPERSEDED', 'option-a': 'FITTED', 'option-b': 'PROPOSED'})
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
        bad['capacitors'][2].pop('url')
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

    def test_value_drift_from_facts_is_refused(self):
        for path, value, msg in ((('circuit', 'r12_ohm', 'value'), 1000, 'resistance fact'),
                                 (('u2_iol_min_a', 'value'), 40.0, 'I\\(OL\\) minimum'),
                                 (('circuit', 'c_nominal_tolerance', 'values'), [1.0, 0.95], 'tolerance fact')):
            bad = copy.deepcopy(INPUTS)
            node = bad
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value
            with self.subTest(path=path), self.assertRaisesRegex(q1.InputError, msg):
                q1.evaluate(bad)

    def test_adopted_value_not_in_decision_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['adopted']['rationale_phrases'][0] = '0.1-1.1 uF'
        with self.assertRaisesRegex(q1.InputError, 'rationale'):
            q1.evaluate(bad)

    def test_missing_soa_input_is_unsourced(self):
        bad = copy.deepcopy(INPUTS)
        bad.pop('q1_soa')
        with self.assertRaisesRegex(q1.InputError, 'UNSOURCED'):
            q1.evaluate(bad)

    def test_unknown_status_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['capacitors'][1]['status'] = 'ADOPTED'
        with self.assertRaisesRegex(q1.InputError, 'FITTED, SUPERSEDED or PROPOSED'):
            q1.evaluate(bad)

    def test_two_fitted_capacitors_are_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['capacitors'][0]['status'] = 'FITTED'
        with self.assertRaisesRegex(q1.InputError, 'exactly one'):
            q1.evaluate(bad)

    def test_fitted_option_without_owner_source_is_refused(self):
        bad = copy.deepcopy(INPUTS)
        bad['capacitors'][1]['source_id'] = 'src-c1848-dcbias-removed'
        with self.assertRaisesRegex(q1.InputError, 'missing or unavailable'):
            q1.evaluate(bad)


if __name__ == '__main__':
    unittest.main()
