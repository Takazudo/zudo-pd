"""Synthetic analyzer regressions; these do not replay or qualify the circuit."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from analysis_inputs import load, START_CASES, REENTRY_CASES
from analyze_reentry import forms

HERE = Path(__file__).resolve().parent


def row(t, p12=0, p5=0, m12=0, enn=0):
    values = (p12, p5, m12, 0, -1, -.3, 1, 0, 0, 0, enn)
    return ' '.join(f'{x:.12g}' for value in values for x in (t, value)) + '\n'


class AnalysisInputsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'nom.dat'
        self.path.with_suffix('.cir').write_text('.tran 1u 4u 0 1u\n')
        self.good = ''.join(row(i * 1e-6) for i in range(5))
        self.path.write_text(self.good)

    def test_complete_wrdata(self):
        self.assertEqual(len(load(self.path)), 5)

    def test_empty_truncated_and_bad_rows(self):
        for content in ('', row(0), self.good[:self.good.index('\n') + 1], 'not numbers\n',
                        '0 0\n', self.good.replace('0 0', '0 nan', 1)):
            with self.subTest(content=content[:30]):
                self.path.write_text(content)
                with self.assertRaises(ValueError):
                    load(self.path)

    def test_nonmonotonic_and_missing_interior_samples(self):
        for times in ((0, 1e-6, 1e-6, 4e-6), (0, 3e-6, 4e-6)):
            self.path.write_text(''.join(row(t) for t in times))
            with self.assertRaises(ValueError):
                load(self.path)

    def test_inconsistent_wrdata_clocks(self):
        self.path.write_text(self.good.replace('0 0 0 0', '0 0 1 0', 1))
        with self.assertRaisesRegex(ValueError, 'time columns'):
            load(self.path)

    def test_missing_and_bad_deck(self):
        self.path.with_suffix('.cir').unlink()
        with self.assertRaises(OSError):
            load(self.path)
        self.path.with_suffix('.cir').write_text('.tran bad\n')
        with self.assertRaisesRegex(ValueError, '.tran'):
            load(self.path)

    def test_coarse_sampling_rejected(self):
        self.path.with_suffix('.cir').write_text('.tran 1m 4m 0 1m\n')
        with self.assertRaisesRegex(ValueError, 'resolution'):
            load(self.path)

    def test_definition_one_includes_1v45_to_1v5_interval(self):
        # A historical 1.45 V predicate misses the 0.9 V hold violation at 1.47 V.
        r = [(0, 1.44, .7, -1.44), (1, 1.47, .9, -1.47), (2, 1.5, 1.1, -1.5)]
        self.assertEqual(forms(r)['p5_max_while_min_analog_lt_1v5'], .9)

    def run_analyzer(self, name, directory=None):
        return subprocess.run([sys.executable, str(HERE / name), str(directory or self.root)],
                              capture_output=True, text=True)

    def test_missing_directory_and_incomplete_case_set_fail_without_json(self):
        empty = self.root / 'empty'
        empty.mkdir()
        for script in ('analyze_tracking.py', 'analyze_reentry.py'):
            for directory in (self.root / 'absent', empty, self.root):
                with self.subTest(script=script, directory=str(directory)):
                    result = self.run_analyzer(script, directory)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, '')
                    self.assertIn('FAIL:', result.stderr)

    def make_batch(self, cases):
        for case in cases:
            reentry = case.startswith('reR') or case.startswith('reB')
            stop = .42 if case.startswith('reB') else .32 if reentry else .25
            td = .2 if case.startswith('reB') else .15
            tr = td + (int(case[3:]) * .001 if reentry else .006)
            deck = f'.tran 50u {stop} 0 50u\n'
            if reentry:
                deck += f'VDIS dis 0 PWL(0 0 {td} 0 {td+.001} 5 {tr} 5 {tr+.001} 0)\n'
            (self.root / f'{case}.cir').write_text(deck)
            with (self.root / f'{case}.dat').open('w') as stream:
                for i in range(round(stop / 50e-6) + 1):
                    t = i * 50e-6
                    v = max(0, min(12.2, (t - .11) * 400))
                    if reentry and td <= t < tr:
                        v = 0
                    p5 = min(5.1, v * .42)
                    # Inject a distinct hold violation above the old 1.45 V boundary.
                    if 1.45 < v < 1.5:
                        p5 = .9
                    stream.write(row(t, v, p5, -v, 5 if reentry and td <= t < tr else 0))

    def test_complete_start_batch_and_exact_metric(self):
        self.make_batch(START_CASES)
        result = self.run_analyzer('analyze_tracking.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(set(report), set(START_CASES))
        self.assertEqual(report['nom']['p5_max_while_min_analog_lt_1v5'], .9)
        self.assertNotIn('p5_max_while_min_analog_lt_1v45', report['nom'])

    def test_complete_reentry_batch(self):
        self.make_batch(REENTRY_CASES)
        result = self.run_analyzer('analyze_reentry.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(json.loads(result.stdout)), set(REENTRY_CASES))

    def test_missing_reentry_pwl_fails(self):
        self.make_batch(REENTRY_CASES)
        (self.root / 'reB6.cir').write_text('.tran 50u .42 0 50u\n')
        result = self.run_analyzer('analyze_reentry.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing reentry VDIS PWL', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_reentry_without_enable_observation_fails(self):
        self.make_batch(REENTRY_CASES)
        p = self.root / 'reB6.dat'
        p.write_text(''.join(row(i*50e-6, enn=5) for i in range(8401)))
        result = self.run_analyzer('analyze_reentry.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('re-enable never observed', result.stderr)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
