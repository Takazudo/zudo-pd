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

    def test_executed_deck_differs_by_one_output_only_line(self):
        for name, deck in ex.derive_decks().items():
            with self.subTest(name=name):
                diff = [l for l in difflib.ndiff(deck['refined'].splitlines(), deck['executed'].splitlines())
                        if l[:1] in '+-']
                self.assertEqual(diff, ['+ ' + deck['added_line']])
                self.assertTrue(deck['added_line'].startswith(f'wrdata {name}-ref.txt '))
                lines = deck['executed'].splitlines()
                self.assertLess(lines.index('run'), lines.index(deck['added_line']))

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
        response.__enter__.return_value.read.return_value = b'revised'
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
        receipt = {'status': 'COMPLETE', 'image': ex.IMAGE, 'platform': 'linux/amd64', 'variant_policy': 'original-only',
                   'solver_version_output': '** ngspice-44.2 : Circuit level simulation program'}
        run.mkdir(parents=True)
        (run / 'receipt.json').write_text(json.dumps(receipt))
        manifest = {'cases': {}}
        for name in ex.CASES:
            work = ex.attempt_dir(run, name)
            work.mkdir(parents=True)
            (root / 'lib').mkdir(exist_ok=True)
            (run / name / '0' / 'lib').mkdir(exist_ok=True)
            (run / name / '0' / 'lib' / 'opax187.lib').write_bytes(b'vendor')
            for suffix in ex.EVIDENCE_SUFFIXES:
                (work / f'{name}{suffix}').write_text(f'{name}{suffix}')
            refinement['cases'][name] = {'main_waveform_sha256': sha(f'{name}.dat'.encode()),
                                         'supplemental_waveform_sha256': sha(f'{name}-osc-cap.txt'.encode())}
            manifest['cases'][name] = {'executed_deck_sha256': sha(f'{name}.cir'.encode())}
        return run, manifest

    def test_identity_requires_byte_identical_outputs_and_pinned_solver(self):
        with tempfile.TemporaryDirectory() as tmp:
            refinement = {'cases': {}}
            run, manifest = self.make_run(Path(tmp), refinement)
            with mock.patch.object(ex, 'records', return_value=({}, refinement)):
                self.assertEqual(ex.identity(run, manifest)['status'], 'REPRODUCED')
                (ex.attempt_dir(run, 'adv') / 'adv.dat').write_text('drifted')
                result = ex.identity(run, manifest)
                self.assertEqual(result['status'], 'NOT REPRODUCED')
                self.assertFalse(result['cases']['adv']['matches']['main_waveform'])
                (ex.attempt_dir(run, 'adv') / 'adv.dat').write_text('adv.dat')
                receipt = json.loads((run / 'receipt.json').read_text())
                receipt['solver_version_output'] = 'ngspice-45'
                (run / 'receipt.json').write_text(json.dumps(receipt))
                self.assertEqual(ex.identity(run, manifest)['status'], 'NOT REPRODUCED')

    def test_collection_excludes_vendor_bytes_and_hashes_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            run, _ = self.make_run(tmp, {'cases': {}})
            hashes = ex.collect(tmp, tmp / 'evidence')
            self.assertIn('ladder-test/receipt.json', hashes)
            self.assertIn('ladder-test/adv/adv-ref.txt', hashes)
            collected = [p for p in (tmp / 'evidence').rglob('*') if p.is_file()]
            self.assertFalse(any(p.suffix.lower() in ex.VENDOR_SUFFIXES or 'lib' in p.parts for p in collected))
            self.assertEqual(len(collected), len(hashes) + 1)
            with self.assertRaisesRegex(ValueError, 'vendor model bytes'):
                ex.collect(tmp, tmp / 'again', [run / 'nom' / '0' / 'lib' / 'opax187.lib'])

    def test_single_run_directory_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'found 0'):
                ex.single_run(tmp)


class ClassificationTests(unittest.TestCase):
    def test_rule_is_fixed_before_the_run(self):
        self.assertEqual(ex.classify(0.95, 0.3137, 0.95), ex.SUPPORTED)
        self.assertEqual(ex.classify(0.3137 * 1.05, 0.3137, 0.95), ex.REFUTED)
        self.assertEqual(ex.classify(0.5, 0.3137, 0.95), ex.UNRESOLVED)

    def test_slopes_scale_by_gain_in_v_per_ms(self):
        self.assertEqual(ex.slopes([0.0, 1e-3], [0.0, -0.5], 2.0), [1.0])


class WorkflowTests(unittest.TestCase):
    def test_workflow_is_single_purpose_and_pinned(self):
        text = WORKFLOW.read_text()
        on = text.split('\non:', 1)[1].split('\npermissions:', 1)[0]
        self.assertEqual([l.strip() for l in on.splitlines() if l.strip()], ['workflow_dispatch:'])
        self.assertRegex(text, r'\npermissions:\n  contents: read\n')
        self.assertIn('timeout-minutes: 45', text)
        self.assertRegex(text, r'\nconcurrency:\n  group: phase33-d1-reference\n')
        self.assertNotIn('secrets.', text)
        self.assertNotIn('inputs:', text)
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
