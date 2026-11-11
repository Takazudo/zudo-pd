"""Executed-copy provenance regressions with a fake solver; not circuit simulation or qualification."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from analyze_refinement import provenance
from run_ladder import verify_executed_inputs

HERE = Path(__file__).resolve().parent
FAKE_DOCKER = '''#!/usr/bin/env python3
import sys
from pathlib import Path
args=sys.argv
if args[1]=='rm': sys.exit(0)
if args[-1]=='--version':
 print('ngspice stub version'); sys.exit(0)
work=Path(args[args.index('-v')+1].split(':')[0])/'tracking'
name=Path(args[-1]).stem
(work/(name+'.dat')).write_text('\\n'.join(' '.join(str(v) for _ in range(11) for v in (t,0)) for t in (0,5e-6,1e-5)))
print('ngspice fake test solver')
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExecutedInputTests(unittest.TestCase):
    """Mutate the per-attempt copies the solver mounted while inputs/ snapshots stay unchanged."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.temp.name)
        for name in ('run_ladder.sh', 'run_ladder.py', 'analysis_inputs.py'):
            shutil.copyfile(HERE / name, root / name)
        (root / 'lib' / 'vendor').mkdir(parents=True)
        (root / 'lib' / 'opa.lib').write_text('* retained OPA model\n')
        (root / 'lib' / 'vendor' / 'csd.lib').write_text('* retained CSD model\n')
        tracking = root / 'tracking'
        tracking.mkdir()
        (tracking / '.spiceinit').write_text('set ngbehavior=psa\nset num_threads=1\n')
        cases = {}
        for name in ('nom', 'adv'):
            (tracking / (name + '.cir')).write_text(f'* {name}\n.tran 2u 10u 0 5u\n.options method=trap rshunt=1e10\n')
            cases[name] = {'derived_deck_sha256': sha(tracking / (name + '.cir'))}
        inputs = {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
                  if p.is_file() and p.parts[len(root.parts)] in ('lib', 'tracking')}
        self.preparation = {'cases': cases, 'inputs': inputs}
        binary = root / 'bin'
        binary.mkdir()
        (binary / 'docker').write_text(FAKE_DOCKER)
        (binary / 'docker').chmod(0o755)
        env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'])
        for name in ('nom', 'adv'):
            result = subprocess.run(['bash', str(root / 'run_ladder.sh'), 'tracking', name, '--original-only'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.snapshots = {p: p.read_bytes() for p in root.glob('ladder-*/inputs/**/*') if p.is_file()}

    def tearDown(self):
        self.temp.cleanup()

    def attempt(self, name='nom'):
        for receipt in self.root.glob('ladder-*/receipt.json'):
            if json.loads(receipt.read_text())['requested_cases'] == [name]:
                return receipt.parent / name / '0'
        raise AssertionError(name)

    def assert_rejected(self, reason):
        with self.assertRaises(ValueError) as caught:
            provenance(self.root, self.preparation, 'nom')
        self.assertIn(reason, str(caught.exception))
        self.assertEqual(self.snapshots, {p: p.read_bytes() for p in self.snapshots}, 'inputs/ snapshots must stay unchanged')
        provenance(self.root, self.preparation, 'adv')

    def test_untouched_attempts_pass_and_report_executed_digests(self):
        for name in ('nom', 'adv'):
            _, receipt, _, _, executed = provenance(self.root, self.preparation, name)
            self.assertEqual(set(executed), {'lib/opa.lib', 'lib/vendor/csd.lib', 'tracking/.spiceinit'})
            self.assertEqual(executed['tracking/.spiceinit'], receipt['input_sha256']['.spiceinit'])

    def test_executed_model_only_mutation_fails(self):
        (self.attempt() / 'lib' / 'vendor' / 'csd.lib').write_text('* altered CSD model\n')
        self.assert_rejected('executed input lib/vendor/csd.lib differs from runner input snapshot')

    def test_executed_settings_only_mutation_fails(self):
        (self.attempt() / 'tracking' / '.spiceinit').write_text('set ngbehavior=psa\nset num_threads=4\n')
        self.assert_rejected('executed settings tracking/.spiceinit differ from runner input snapshot')

    def test_missing_executed_model_fails(self):
        (self.attempt() / 'lib' / 'opa.lib').unlink()
        self.assert_rejected('executed input missing: lib/opa.lib')

    def test_missing_executed_settings_fails(self):
        (self.attempt() / 'tracking' / '.spiceinit').unlink()
        self.assert_rejected('executed settings missing: tracking/.spiceinit')

    def test_missing_executed_library_directory_fails(self):
        shutil.rmtree(self.attempt() / 'lib')
        self.assert_rejected('executed library directory missing')

    def test_unexpected_executed_model_fails(self):
        (self.attempt() / 'lib' / 'substitute.lib').write_text('* unreviewed model\n')
        self.assert_rejected('unexpected executed input: lib/substitute.lib')

    def test_symlinked_substitute_fails_even_with_identical_bytes(self):
        target = self.attempt() / 'lib' / 'opa.lib'
        outside = self.root / 'outside.lib'
        shutil.copyfile(target, outside)
        target.unlink()
        target.symlink_to(outside)
        self.assert_rejected('executed input lib/opa.lib is a symlink')

    def test_symlinked_tracking_directory_fails(self):
        attempt = self.attempt()
        moved = self.root / 'moved-tracking'
        shutil.move(str(attempt / 'tracking'), moved)
        (attempt / 'tracking').symlink_to(moved, target_is_directory=True)
        self.assert_rejected('tracking directory is a symlink')

    def test_snapshot_and_preparation_checks_are_preserved(self):
        snapshot = self.attempt().parent.parent / 'inputs' / '.spiceinit'
        snapshot.write_text('changed snapshot\n')
        with self.assertRaisesRegex(ValueError, 'runner input snapshot changed'):
            provenance(self.root, self.preparation, 'nom')

    def test_helper_rejects_receipts_without_settings_or_library(self):
        with self.assertRaisesRegex(ValueError, 'lacks .spiceinit or lib/'):
            verify_executed_inputs(self.attempt(), {'lib/opa.lib': '0'})
        with self.assertRaisesRegex(ValueError, 'lacks .spiceinit or lib/'):
            verify_executed_inputs(self.attempt(), {'.spiceinit': '0'})


if __name__ == '__main__':
    unittest.main()
