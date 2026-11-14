"""Tests for the D1 reference extraction; no vendor model bytes or solver are needed."""
import difflib
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock
import zipfile

import extract_reference as ex

HERE = Path(__file__).resolve().parent
WORKFLOW = HERE.parents[2] / '.github/workflows/phase33-d1-reference.yml'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ConversionTests(unittest.TestCase):
    FIXTURE = (b'* vendor header\r\n.SUBCKT X 1 2 3\r\n.PARAM Rs 0.5\r\n.param  Vth\t1.8 \r\n.PARAM a=1\r\n'
               b'.PARAM Cgs 1n\r\n.PARAM K_1 2\r\n.PARAM Lambda 0.01\r\n* .PARAM ignored 3\r\n.ENDS\r\n')

    def test_exactly_five_name_value_lines_change_and_other_bytes_are_preserved(self):
        converted = ex.convert_param(self.FIXTURE)
        expected = self.FIXTURE.replace(b'.PARAM Rs 0.5', b'.PARAM Rs=0.5').replace(
            b'.param  Vth\t1.8 ', b'.param  Vth=1.8 ').replace(b'.PARAM Cgs 1n', b'.PARAM Cgs=1n').replace(
            b'.PARAM K_1 2', b'.PARAM K_1=2').replace(b'.PARAM Lambda 0.01', b'.PARAM Lambda=0.01')
        self.assertEqual(converted, expected)
        self.assertEqual(converted.count(b'\r\n'), self.FIXTURE.count(b'\r\n'))
        self.assertEqual(len(converted), len(self.FIXTURE))  # each separator here is one blank or tab

    def test_a_different_count_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'found 4'):
            ex.convert_param(self.FIXTURE.replace(b'.PARAM K_1 2', b'.PARAM K_1=2'))
        with self.assertRaisesRegex(ValueError, 'found 6'):
            ex.convert_param(self.FIXTURE + b'.PARAM Extra 9\r\n')


class DeckTests(unittest.TestCase):
    def test_refined_decks_reproduce_recorded_hashes_from_git(self):
        _, refinement = ex.records()
        expected = refinement['preparation']['inputs']
        for name, deck in ex.derive_decks().items():
            with self.subTest(name=name):
                self.assertEqual(sha(deck['refined'].encode()), expected[f'tracking/{name}.cir'])

    def test_executed_deck_differs_by_two_output_only_lines(self):
        for name, deck in ex.derive_decks().items():
            with self.subTest(name=name):
                diff = [l for l in difflib.ndiff(deck['refined'].splitlines(), deck['executed'].splitlines())
                        if l[:1] in '+-']
                self.assertEqual(diff, ['+ ' + line for line in deck['added_lines']])
                self.assertTrue(deck['added_lines'][0].startswith(f'wrdata {name}-ref.txt '))
                self.assertEqual(deck['added_lines'][1], f'wrdata {name}-servo.txt v(p5_drv) v(trk5) v(p5_cs) '
                                                         'v(m12_drv) v(trk12n_fb) v(m12_cs) v(ctz)')
                lines = deck['executed'].splitlines()
                self.assertLess(lines.index('run'), lines.index(deck['added_lines'][0]))
                self.assertTrue(all(line.startswith('wrdata ') for line in deck['added_lines']))

    def test_spiceinit_and_gains_come_from_repository_sources(self):
        _, refinement = ex.records()
        self.assertEqual(sha(ex.INIT.encode()), refinement['preparation']['inputs']['tracking/.spiceinit'])
        decks = ex.derive_decks()
        self.assertAlmostEqual(ex.deck_gain(decks['nom']['executed'], '+5'), 1 + 23.2 / 10)
        self.assertAlmostEqual(ex.deck_gain(decks['adv']['executed'], '-12'), 750 / 93.1)


class ExternalInputTests(unittest.TestCase):
    def test_fetch_is_one_attempt_and_failures_are_not_run(self):
        with mock.patch.object(ex.urllib.request, 'urlopen', side_effect=OSError('reset')) as opened:
            with self.assertRaisesRegex(ex.NotRun, 'https://example.invalid/a.zip: OSError: reset'):
                ex.fetch('https://example.invalid/a.zip', '0' * 64)
            self.assertEqual(opened.call_count, 1)
        response = mock.MagicMock()
        response.__enter__.return_value.read.side_effect = [b'revised', b'']
        with mock.patch.object(ex.urllib.request, 'urlopen', return_value=response):
            with self.assertRaisesRegex(ex.NotRun, 'differs from recorded'):
                ex.fetch('https://example.invalid/a.zip', '0' * 64)

    def test_revised_archives_fail_closed(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('OPAx187.LIB', b'not the vendor model')
        with self.assertRaisesRegex(ex.NotRun, 'sbomab6.zip differs'):
            ex.build_models({'sbomab6': buffer.getvalue(), 'slpm286': b''}, {})

    def test_prepare_records_not_run_without_writing_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / 'archives').mkdir()
            for name in ex.ARCHIVES:
                (tmp / 'archives' / f'{name}.zip').write_bytes(b'revised')
            manifest = tmp / 'manifest.json'
            code = ex.main(['prepare', str(tmp / 'work'), '--archives', str(tmp / 'archives'), '--manifest', str(manifest)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(manifest.read_text())['status'], ex.NOT_RUN)
            self.assertFalse((tmp / 'work').exists())


class RunTests(unittest.TestCase):
    def make_run(self, root, refinement):
        run = root / 'ladder-test'
        solver = '** ngspice-44.2 : Circuit level simulation program'
        inputs = {'lib/opax187.lib': sha(b'vendor'), '.spiceinit': sha(b'init')}
        receipt = {'status': 'COMPLETE', 'image': ex.IMAGE, 'platform': 'linux/amd64', 'variant_policy': 'original-only',
                   'solver_version_output': solver, 'input_sha256': inputs}
        refinement['preparation'] = {'inputs': {'lib/opax187.lib': sha(b'vendor'), 'tracking/.spiceinit': sha(b'init')}}
        run.mkdir(parents=True)
        (run / 'receipt.json').write_text(json.dumps(receipt))
        manifest = {'source_revision': 'abc', 'cases': {}}
        for name in ex.CASES:
            work = ex.attempt_dir(run, name)
            work.mkdir(parents=True)
            (run / name / '0' / 'lib').mkdir(exist_ok=True)
            (run / name / '0' / 'lib' / 'opax187.lib').write_bytes(b'vendor')
            (work / '.spiceinit').write_bytes(b'init')
            for suffix in ex.EVIDENCE_SUFFIXES:
                (work / f'{name}{suffix}').write_text(f'{name}{suffix}')
            refinement['cases'][name] = {'main_waveform_sha256': sha(f'{name}.dat'.encode()),
                                         'supplemental_waveform_sha256': sha(f'{name}-osc-cap.txt'.encode()),
                                         'solver_version_output': solver}
            manifest['cases'][name] = {'executed_deck_sha256': sha(f'{name}.cir'.encode())}
        return run, manifest

    def test_identity_requires_byte_identical_outputs_and_pinned_solver(self):
        with tempfile.TemporaryDirectory() as tmp:
            refinement = {'cases': {}}
            run, manifest = self.make_run(Path(tmp), refinement)
            with mock.patch.object(ex, 'records', return_value=({}, refinement)):
                self.assertEqual(ex.identity(run, manifest)['status'], 'REPRODUCED')
                (run / 'nom' / '0' / 'lib' / 'opax187.lib').write_bytes(b'other')
                result = ex.identity(run, manifest)
                self.assertFalse(result['cases']['nom']['matches']['executed_models_and_settings'])
                (run / 'nom' / '0' / 'lib' / 'opax187.lib').write_bytes(b'vendor')
                (ex.attempt_dir(run, 'adv') / 'adv.dat').write_text('drifted')
                result = ex.identity(run, manifest)
                self.assertEqual(result['status'], 'NOT REPRODUCED')
                self.assertFalse(result['cases']['adv']['matches']['main_waveform'])
                (ex.attempt_dir(run, 'adv') / 'adv.dat').write_text('adv.dat')
                receipt = json.loads((run / 'receipt.json').read_text())
                receipt['solver_version_output'] = '** ngspice-44.2 : other build'
                (run / 'receipt.json').write_text(json.dumps(receipt))
                self.assertEqual(ex.identity(run, manifest)['status'], 'NOT REPRODUCED')

    def test_collection_excludes_vendor_bytes_and_hashes_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            run, _ = self.make_run(tmp, {'cases': {}})
            (tmp / 'out').mkdir()
            (tmp / 'out' / 'manifest.json').write_text('{}')
            self.assertEqual(ex.main(['collect', str(tmp), '--evidence', str(tmp / 'evidence'), '--extra-dir', str(tmp / 'out')]), 0)
            hashes = json.loads((tmp / 'evidence' / 'hashes.json').read_text())
            self.assertIn('manifest.json', hashes)
            self.assertIn('ladder-test/receipt.json', hashes)
            self.assertIn('ladder-test/adv/adv-ref.txt', hashes)
            collected = [p for p in (tmp / 'evidence').rglob('*') if p.is_file()]
            self.assertFalse(any(p.suffix.lower() in ex.VENDOR_SUFFIXES or 'lib' in p.parts for p in collected))
            self.assertEqual(len(collected), len(hashes) + 1)
            (tmp / 'out' / 'model.lib').write_bytes(b'vendor')
            with self.assertRaisesRegex(ValueError, 'vendor model bytes'):
                ex.collect(tmp, tmp / 'again', tmp / 'out')

    def test_single_run_directory_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'found 0'):
                ex.single_run(tmp)


class ClassificationTests(unittest.TestCase):
    def test_rule_is_fixed_before_the_run(self):
        self.assertEqual(ex.classify(0.95, 0.3137, 0.95), ex.SUPPORTED)
        self.assertEqual(ex.classify(0.3137 * 1.05, 0.3137, 0.95), ex.REFUTED)
        self.assertEqual(ex.classify(0.5, 0.3137, 0.95), ex.UNRESOLVED)
        self.assertEqual(ex.classify(-2.0, 0.3137, 0.95), ex.REFUTED)  # an opposite-direction edge never supports
        self.assertEqual(ex.classify(1.0, 0.3137, 0.95, competing=0.98), ex.UNRESOLVED)  # reference only follows RAMP
        self.assertEqual(ex.classify(1.2, 0.3137, 0.95, competing=0.3), ex.SUPPORTED)

    def test_slopes_are_signed_and_scaled_in_v_per_ms(self):
        self.assertEqual(ex.slopes([0.0, 1e-3], [0.0, -0.5], 2.0), [-1.0])


class AnalysisTests(unittest.TestCase):
    STEP = 50e-6
    DECK = ('* synthetic\nRT5A p5_out trk5 23.2k\nRT5B trk5 0 10k\nRT12NA ramp_m12 trk12n 93.1k\n'
            'RT12NB trk12n m12_out 750k\n.tran 2u 2m 0 50u\n.end\n')

    def write_case(self, run, name, main, ref, extra=()):
        work = Path(run) / name / '0' / 'tracking'
        work.mkdir(parents=True)
        (work / f'{name}.cir').write_text(self.DECK)
        times = sorted({i * self.STEP for i in range(41)} | set(extra))
        with (work / f'{name}.dat').open('w') as out:
            for t in times:
                values = main(t)
                out.write(' '.join(f'{t:.12e} {v:.12e}' for v in values) + '\n')
        with (work / f'{name}-ref.txt').open('w') as out:
            for t in times:
                out.write(' '.join(f'{t:.12e} {v:.12e}' for v in ref(t)) + '\n')
        return times

    def test_direction_gain_and_attribution_on_synthetic_waveforms(self):
        edge = (1.0e-3, 1.05e-3)

        def ramp(t, rate):  # rate in V/ms
            return rate * t * 1e3

        def step(t, base, extra):  # base slope plus an extra slope during the edge, both in V/ms
            return (base * t + extra * (min(max(t, edge[0]), edge[1]) - edge[0])) * 1e3

        nom_ref = lambda t: [ramp(t, 0.09), 0, step(t, 0.09, 0.30), 0, 0, 0, 0]  # rising RAMP_P5 edge, slow RAMP
        nom_main = lambda t: [0, step(t, 0.30, 0.65485), 0] + [0] * 8  # +5 output rises at the edge
        adv_ref = lambda t: [ramp(t, 0.09), 0, 0, ramp(t, 0.09), 0, 0, 0]  # smooth RAMP_M12
        adv_main = lambda t: [0, 0, -step(t, 0.7, 0.7748)] + [0] * 8  # -12 output falls at the edge
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'ladder-x'
            times = self.write_case(run, 'nom', nom_main, nom_ref)
            self.write_case(run, 'adv', adv_main, adv_ref)
            slope_p5 = ex.slopes(times, [nom_main(t)[1] for t in times], 1)[20]
            slope_m12 = ex.slopes(times, [adv_main(t)[2] for t in times], -1)[20]
            refinement = {'cases': {
                'nom': {'rails': {'+5': {'worst_recorded_bound_exceedance': {'start_ms': 1.0, 'end_ms': 1.05, 'slope_v_per_ms': slope_p5},
                                         'exception': {'slope_ceiling_v_per_ms': 0.95}}}},
                'adv': {'rails': {'-12': {'worst_recorded_bound_exceedance': {'start_ms': 1.0, 'end_ms': 1.05, 'slope_v_per_ms': slope_m12},
                                          'exception': {'slope_ceiling_v_per_ms': 1.47}}}}}}
            with mock.patch.object(ex, 'records', return_value=({}, refinement)):
                result = ex.analyze(run)
        p5, m12 = result['rails']['+5'], result['rails']['-12']
        self.assertAlmostEqual(p5['tracking_gain_from_deck'], 3.32)
        self.assertAlmostEqual(p5['scaled_reference_peak_near_segment_v_per_ms'], 3.32 * 0.39, places=6)
        self.assertEqual(p5['hypotheses']['D1-H6 reference-side edge'], ex.SUPPORTED)
        self.assertEqual(p5['hypotheses']['D1-H1 recorded common RAMP too steep'], ex.REFUTED)
        self.assertEqual(m12['hypotheses']['D1-H6 reference-side edge'], ex.REFUTED)
        self.assertEqual(p5['hypotheses']['D1-H6 clamp-diode release'], ex.UNRESOLVED)  # diode at 0 V is not reverse-biased
        self.assertEqual(m12['hypotheses']['D1-H1 recorded common RAMP too steep'], ex.REFUTED)
        self.assertGreater(m12['output_slope_at_segment_v_per_ms'], 1.47)
        self.assertTrue(all('UNRESOLVED' in r['hypotheses']['D1-H4 pre-bias overshoot'] for r in result['rails'].values()))


    def test_nanosecond_timestep_ring_cannot_fire_the_rule(self):
        # Regression for run 43087070975: a +/-1 mV alternating ring over 2 ns steps on RAMP_M12,
        # straddling a bin edge, made the adjacent-sample rule report a 3730 V/ms reference edge.
        ring_at = 0.96e-3
        ring = {ring_at + k * 2e-9: (0.0 if abs(k) == 7 else 1e-3 if k % 2 else -1e-3) for k in range(-7, 8) if k}
        base = lambda t: 0.09 * t * 1e3
        adv_ref = lambda t: [base(t), 0, 0, base(t) + ring.get(t, 0.0), 0, 0, 5.0]  # clamp output far above: reverse-biased
        adv_main = lambda t: [0, 0, -(0.7 * t + 0.7748 * (min(max(t, 1.0e-3), 1.05e-3) - 1.0e-3)) * 1e3] + [0] * 8
        nom_ref = lambda t: [base(t), 0, base(t), 0, 0, 5.0, 0]
        nom_main = lambda t: [0, (0.30 * t + 0.65485 * (min(max(t, 1.0e-3), 1.05e-3) - 1.0e-3)) * 1e3, 0] + [0] * 8
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'ladder-x'
            times = self.write_case(run, 'nom', nom_main, nom_ref)
            adv_times = self.write_case(run, 'adv', adv_main, adv_ref, extra=ring)
            refinement = {'cases': {
                'nom': {'rails': {'+5': {'worst_recorded_bound_exceedance': {
                    'start_ms': 1.0, 'end_ms': 1.05, 'slope_v_per_ms': ex.slopes(times, [nom_main(t)[1] for t in times], 1)[20]},
                    'exception': {'slope_ceiling_v_per_ms': 0.95}}}},
                'adv': {'rails': {'-12': {'worst_recorded_bound_exceedance': {
                    'start_ms': 1.0, 'end_ms': 1.05,
                    'slope_v_per_ms': ex.slopes(adv_times, [adv_main(t)[2] for t in adv_times], -1)[adv_times.index(1.0e-3)]},
                    'exception': {'slope_ceiling_v_per_ms': 1.47}}}}}}
            with mock.patch.object(ex, 'records', return_value=({}, refinement)):
                result = ex.analyze(run)
                ring_record = ex.timestep_ring(run)
        m12 = result['rails']['-12']
        self.assertGreater(m12['adjacent_sample_scaled_reference_peak_v_per_ms'], 1000)  # the old rule would fire
        self.assertAlmostEqual(m12['scaled_reference_peak_near_segment_v_per_ms'], 8.055854 * 0.09, delta=0.05)
        self.assertEqual(m12['hypotheses']['D1-H6 reference-side edge'], ex.REFUTED)
        self.assertEqual(m12['hypotheses']['D1-H6 clamp-diode release'], ex.REFUTED)
        self.assertEqual(m12['hypotheses']['D1-H7 adjacent-sample trigger is a solver-timestep artefact'], ex.SUPPORTED)
        self.assertTrue(result['rails']['+5']['hypotheses']['D1-H7 adjacent-sample trigger is a solver-timestep artefact']
                        .startswith('NOT APPLICABLE'))
        self.assertEqual(ring_record['cluster_samples'], 14)
        self.assertGreaterEqual(ring_record['node_sign_reversals_in_cluster'], 10)
        self.assertAlmostEqual(ring_record['node_peak_to_peak_in_cluster_v'], 2e-3, delta=1e-5)

    def test_bins_outside_the_record_are_dropped(self):
        times = [i * 1e-6 for i in range(400)]
        values = [1.0 + 0.1 * t * 1e3 for t in times]  # 0.1 V/ms riding on 1 V, excursion near both record ends
        for start in (50e-6, 330e-6):
            out = ex.grid_slopes(times, values, 1.0, start, start + 2e-6)
            self.assertTrue(out)
            self.assertTrue(all(abs(slope - 0.1) < 1e-9 for _, slope in out), start)

    def test_a_long_step_is_not_called_a_timestep_artefact(self):
        times = [0.0, 1e-6, 3e-6, 4e-6]  # the peak interval is 2 us, not a sub-grid cluster
        self.assertIsNone(ex.cluster(times, [0, 0, 1, 1], 1))
        self.assertEqual(ex.timestep_artefact(5.0, 0.5, 1.47, None), ex.UNRESOLVED)
        self.assertEqual(ex.timestep_artefact(5.0, 0.5, 1.47, (0, 3, 1)), ex.UNRESOLVED)  # no alternating ring
        self.assertEqual(ex.timestep_artefact(5.0, 0.5, 1.47, (0, 3, 2)), ex.SUPPORTED)
        self.assertEqual(ex.timestep_artefact(5.0, 2.0, 1.47, (0, 3, 9)), ex.REFUTED)
        self.assertTrue(ex.timestep_artefact(1.0, 0.5, 1.47, None).startswith('NOT APPLICABLE'))

    def test_bin_slopes_are_exact_for_a_linear_waveform(self):
        times = [i * 1e-6 for i in range(400)]
        values = [0.5 * t * 1e3 for t in times]  # 0.5 V/ms
        out = ex.grid_slopes(times, values, 2.0, 200e-6, 202e-6)
        self.assertTrue(all(abs(slope - 1.0) < 1e-9 for _, slope in out))


class ServoRecordTests(unittest.TestCase):
    RECORD = json.loads(ex.SERVO_RECORD.read_text())

    def test_prose_is_generated_from_the_record(self):
        self.assertEqual(ex.SERVO_RECORD_MD.read_text(), ex.render_servo_markdown(self.RECORD))
        altered = json.loads(json.dumps(self.RECORD))
        altered['servo']['-12']['verdicts']['dead zone set by'] = ex.UNRESOLVED
        altered['predictions_met']['-12']['dead zone set by'] = False
        text = ex.render_servo_markdown(altered)
        self.assertIn('UNRESOLVED (not as predicted)', text)
        self.assertNotIn('set by the conduction threshold', text)

    def test_record_keeps_acceptance_open_and_failures_recorded(self):
        record = self.RECORD
        self.assertEqual(record['electrical_acceptance'], 'NOT ESTABLISHED')
        self.assertEqual(record['identity']['status'], 'REPRODUCED')
        self.assertEqual(record['run']['run_id'], 43099431981)
        self.assertEqual(record['in_job_analysis_sha256'], record['run']['artifact_files_sha256']['analysis.json'])
        _, refinement = ex.records()
        for rail, (name, *_rest) in ex.FAILED.items():
            recorded = refinement['cases'][name]['rails'][rail]['worst_recorded_bound_exceedance']['slope_v_per_ms']
            self.assertEqual(record['recorded_failures_preserved'][rail], recorded)

    def test_predictions_met_follow_the_verdicts(self):
        for rail, row in self.RECORD['servo'].items():
            for question, verdict in row['verdicts'].items():
                self.assertEqual(self.RECORD['predictions_met'][rail][question], ex.prediction_met(question, verdict))
        self.assertTrue(ex.prediction_met('windup released when the reference passes the pre-bias floor', ex.UNRESOLVED))
        self.assertFalse(ex.prediction_met('windup released when the reference passes the pre-bias floor', ex.SUPPORTED))


class RecordTests(unittest.TestCase):
    RECORD = json.loads(ex.RECORD.read_text())

    def test_prose_is_generated_from_the_record(self):
        self.assertEqual(ex.RECORD_MD.read_text(), ex.render_markdown(self.RECORD))
        self.assertEqual(ex.main(['check-record']), 0)
        altered = json.loads(json.dumps(self.RECORD))
        altered['superseded_in_job_analysis']['hypotheses']['-12']['D1-H6 clamp-release reference edge'] = ex.REFUTED
        altered['analysis']['rails']['-12']['hypotheses']['D1-H6 reference-side edge'] = ex.UNRESOLVED
        text = ex.render_markdown(altered)
        self.assertIn('REFUTED (+5 V), REFUTED (−12 V)', text)
        self.assertNotIn('lie downstream of the reference', text)

    def test_record_keeps_acceptance_open_and_failures_recorded(self):
        record = self.RECORD
        self.assertEqual(record['electrical_acceptance'], 'NOT ESTABLISHED')
        self.assertEqual(record['identity']['status'], 'REPRODUCED')
        self.assertEqual(record['run']['run_id'], 43087070975)
        _, refinement = ex.records()
        for rail, (name, *_rest) in ex.FAILED.items():
            recorded = refinement['cases'][name]['rails'][rail]['worst_recorded_bound_exceedance']['slope_v_per_ms']
            self.assertEqual(record['recorded_failures_preserved'][rail], recorded)
            self.assertEqual(record['analysis']['rails'][rail]['output_slope_at_segment_v_per_ms'], recorded)
            self.assertGreater(recorded, refinement['cases'][name]['rails'][rail]['exception']['slope_ceiling_v_per_ms'])
        self.assertEqual(record['superseded_in_job_analysis']['sha256'], record['run']['artifact_files_sha256']['analysis.json'])
        self.assertEqual(record['superseded_in_job_analysis']['hypotheses']['-12']['D1-H6 clamp-release reference edge'],
                         ex.SUPPORTED)

    def test_recorded_conclusions_follow_the_rule_from_recorded_numbers(self):
        for rail, row in self.RECORD['analysis']['rails'].items():
            with self.subTest(rail=rail):
                ideal, ceiling = row['ideal_tracking_max_slope_v_per_ms'], row['exception_slope_ceiling_v_per_ms']
                peak, common = row['scaled_reference_peak_near_segment_v_per_ms'], row['scaled_common_ramp_peak_near_segment_v_per_ms']
                h = row['hypotheses']
                self.assertEqual(h['D1-H6 reference-side edge'], ex.classify(peak, ideal, ceiling, common))
                self.assertEqual(h['D1-H1 recorded common RAMP too steep'], ex.classify(common, ideal, ceiling))
                self.assertEqual(h['D1-H6 clamp-diode release'],
                                 ex.REFUTED if row['clamp_diode_voltage_v']['window_max'] < 0 else ex.UNRESOLVED)
                reversals = row['adjacent_sample_peak_cluster_sign_reversals']
                self.assertEqual(h['D1-H7 adjacent-sample trigger is a solver-timestep artefact'],
                                 ex.timestep_artefact(row['adjacent_sample_scaled_reference_peak_v_per_ms'], peak, ceiling,
                                                      None if reversals is None else (0, 0, reversals)))

    def test_tampered_artifact_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp)
            (evidence / 'ladder-x').mkdir()
            (evidence / 'ladder-x' / 'a.txt').write_text('a')
            (evidence / 'hashes.json').write_text(json.dumps({'ladder-x/a.txt': sha(b'b')}))
            with self.assertRaisesRegex(ValueError, 'hash differs'):
                ex.verified_artifact(evidence)
            (evidence / 'extra.txt').write_text('x')
            with self.assertRaisesRegex(ValueError, 'differ from hashes.json'):
                ex.verified_artifact(evidence)


class WorkflowTests(unittest.TestCase):
    def test_workflow_is_single_purpose_and_pinned(self):
        text = WORKFLOW.read_text()
        on = text.split('\non:', 1)[1].split('\npermissions:', 1)[0]
        self.assertEqual([l.strip() for l in on.splitlines() if l.strip()],
                         ['workflow_dispatch:', 'inputs:', 'gap_sensitivity:',
                          'description: Also run the eight pre-registered C1 gap-sensitivity variant cases (d1-gap-criteria.md)',
                          'type: boolean', 'default: false', 't2_evaluation:',
                          'description: Also run the pre-registered T2 -12 V clamp evaluation and enable-edge corners '
                          '(d1-t2-criteria.md)', 'type: boolean', 'default: false', 't2_rev2_evaluation:',
                          'description: Also run the T2 rev 2 (a2) -12 V evaluation and variant ladder '
                          '(d1-t2-rev2-criteria.md; only once pre-registered)', 'type: boolean', 'default: false',
                          'itl4_inertness:',
                          'description: Also run the itl4 inertness diagnostic on the recorded T2 rev 2 pinned decks '
                          '(itl4-inertness-criteria.md)', 'type: boolean', 'default: false', 'osc_bank:',
                          'description: Also run the OSC-bank baseline diagnostic at the fitted bank and +/-20 % '
                          '(osc-bank-criteria.md)', 'type: boolean', 'default: false', 'ceiling_corners:',
                          'description: Also run the ceiling-bank e5 corners and hot case diagnostic '
                          '(ceiling-corners-criteria.md)', 'type: boolean', 'default: false', 'variant_cross_check:',
                          'description: Also rerun the identity pair under each matched variant and compare with pinned '
                          '(variant-cross-check-criteria.md)', 'type: boolean', 'default: false', 'adv_rshunt_free:',
                          'description: Also run the identity adv deck at rshunt=1e10, pinned and under abstol '
                          '(adv-rshunt-free-criteria.md)', 'type: boolean', 'default: false', 'd2_fast_discharge:',
                          'description: Also run the D2 fast matched discharge candidate over banks and load corners '
                          '(d2-fast-discharge-criteria.md)', 'type: boolean', 'default: false', 'd2_sequenced:',
                          'description: Also run the D2 sequenced -12 V discharge candidate over banks and load corners '
                          '(d2-sequenced-criteria.md)', 'type: boolean', 'default: false'])
        self.assertRegex(text, r'\npermissions:\n  contents: read\n')
        self.assertIn('timeout-minutes: 300', text)
        self.assertRegex(text, r'\nconcurrency:\n  group: phase33-d1-reference\n')
        self.assertNotIn('secrets.', text)
        self.assertEqual(re.findall(r'inputs\.\w+', text), [
            'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.osc_bank', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness',
            'inputs.ceiling_corners', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness', 'inputs.osc_bank',
            'inputs.variant_cross_check', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness', 'inputs.osc_bank', 'inputs.ceiling_corners',
            'inputs.adv_rshunt_free', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness', 'inputs.osc_bank', 'inputs.ceiling_corners', 'inputs.variant_cross_check',
            'inputs.d2_fast_discharge', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness', 'inputs.osc_bank', 'inputs.ceiling_corners', 'inputs.variant_cross_check',
            'inputs.adv_rshunt_free',
            'inputs.d2_sequenced', 'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation',
            'inputs.itl4_inertness', 'inputs.osc_bank', 'inputs.ceiling_corners', 'inputs.variant_cross_check',
            'inputs.adv_rshunt_free', 'inputs.d2_fast_discharge',
            'inputs.gap_sensitivity', 'inputs.t2_evaluation', 'inputs.t2_rev2_evaluation', 'inputs.itl4_inertness',
            'inputs.osc_bank', 'inputs.ceiling_corners', 'inputs.variant_cross_check', 'inputs.adv_rshunt_free',
            'inputs.d2_fast_discharge', 'inputs.d2_sequenced'])
        self.assertIn("if: inputs.gap_sensitivity && steps.identity.outcome == 'success'", text)
        self.assertNotIn('${{ inputs', text)
        uses = re.findall(r'uses: (\S+)', text)
        self.assertTrue(uses)
        for use in uses:
            self.assertRegex(use, r'^[\w.-]+/[\w.-]+@[0-9a-f]{40}$')
        self.assertIn(ex.IMAGE, text)
        self.assertIn('--original-only', text)
        self.assertIn('nom adv', text)
        self.assertIn('${{ runner.temp }}/evidence', text)


if __name__ == '__main__':
    unittest.main()
