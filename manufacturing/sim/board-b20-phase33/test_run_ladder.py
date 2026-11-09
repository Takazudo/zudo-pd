"""Runner regression tests use a fake Docker solver; these are not circuit simulation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class RunnerTests(unittest.TestCase):
    def run_case(self, mode, cases=('nom',)):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('run_ladder.sh', 'run_ladder.py', 'analysis_inputs.py'):
                shutil.copyfile(HERE / name, root / name)
            source = root / 'tracking'
            source.mkdir()
            (root / 'lib').mkdir()
            (root / 'lib' / 'model.lib').write_text('retained model')
            (source / '.spiceinit').write_text('set ngbehavior=psa\nset num_threads=1\n')
            for name in cases:
                (source / (name + '.cir')).write_text('.tran 2u 10u 0 5u\n.options method=trap rshunt=1e10\n')
                (source / (name + '.dat')).write_text('STALE')
            original = {p.name: p.read_bytes() for p in source.iterdir()}
            binary = root / 'bin'
            binary.mkdir()
            docker = binary / 'docker'
            docker.write_text('''#!/usr/bin/env python3
import os,sys,signal,time
from pathlib import Path
args=sys.argv
if args[1]=='rm': sys.exit(7 if os.environ['FAKE_MODE']=='cleanup-fail' and 'version' not in args[-1] else 0)
if args[-1]=='--version':
 print('ngspice stub version'); sys.exit(0)
work=Path(args[args.index('-v')+1].split(':')[0])/'tracking'
name=Path(args[-1]).stem
mode=os.environ['FAKE_MODE']
if mode=='interrupt':
 os.kill(os.getppid(), signal.SIGTERM); time.sleep(1); sys.exit(1)
if mode=='fail' or (mode=='mixed' and name=='adv'): sys.exit(3)
if mode=='missing': sys.exit(0)
if mode=='fallback' and work.parent.name=='0': sys.exit(4)
times=[0, 0.000005, 0.00001] if mode!='truncated' else [0,0.000005]
(work/(name+'.dat')).write_text('\\n'.join(' '.join(str(v) for _ in range(11) for v in (t,0)) for t in times))
print('ngspice fake test solver')
if mode=='aborted': print('Simulation ABORTED')
''')
            docker.chmod(0o755)
            env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'], FAKE_MODE=mode)
            result = subprocess.run(['bash', str(root / 'run_ladder.sh'), 'tracking', *cases], env=env, capture_output=True, text=True)
            receipts = list(root.glob('ladder-*/receipt.json'))
            self.assertEqual(len(receipts), 1, result.stderr)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(original, {p.name: p.read_bytes() for p in source.iterdir()})
            return result, receipt, sorted(p.name for p in (receipts[0].parent / 'accepted').iterdir())

    def test_complete_preserves_provenance(self):
        result, receipt, files = self.run_case('ok')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt['status'], 'COMPLETE')
        self.assertIn('nom.dat', files)
        self.assertIn('waveform_sha256', receipt['cases']['nom']['attempts'][0])

    def test_missing_truncated_aborted_and_failed_are_failures(self):
        for mode in ('missing', 'truncated', 'aborted', 'fail'):
            with self.subTest(mode=mode):
                result, receipt, files = self.run_case(mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(receipt['status'], 'FAILED')
                self.assertEqual(len(receipt['cases']['nom']['attempts']), 7)
                self.assertEqual(files, [])

    def test_aggregate_failure_even_when_last_case_succeeds(self):
        result, receipt, files = self.run_case('mixed', ('adv', 'nom'))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt['cases']['nom']['status'], 'COMPLETE')
        self.assertNotIn('adv.dat', files)

    def test_cleanup_failure_stops_attempts(self):
        result, receipt, files = self.run_case('cleanup-fail')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt['status'], 'FAILED')
        self.assertEqual(len(receipt['cases']['nom']['attempts']), 1)
        self.assertEqual(files, [])

    def test_interruption_keeps_sources_and_fails(self):
        result, receipt, files = self.run_case('interrupt')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt['status'], 'INTERRUPTED')
        self.assertEqual(files, [])

    def test_fallback_retains_failed_attempt(self):
        result, receipt, _ = self.run_case('fallback')
        self.assertEqual(result.returncode, 0, result.stderr)
        attempts = receipt['cases']['nom']['attempts']
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(attempts[0]['deck_sha256'], attempts[1]['deck_sha256'])


if __name__ == '__main__':
    unittest.main()
