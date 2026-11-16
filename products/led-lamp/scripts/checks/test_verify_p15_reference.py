"""Tests for verify-p15-reference.py using a throwaway zudo-pd stand-in repository.

run: python3 -m unittest discover -s scripts/checks -p 'test_*.py'
"""
import copy, hashlib, importlib.util, json, subprocess, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('vpr', HERE / 'verify-p15-reference.py')
vpr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vpr)

PCB, NVM = b'(kicad_pcb p15 stand-in)\n', bytes(range(40))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True).stdout.decode().strip()


class P15ReferenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.pd = base / 'pd'
        (self.pd / 'boards/board-p15/nvm').mkdir(parents=True)
        git(self.pd, 'init', '-q')
        git(self.pd, 'config', 'user.email', 't@example.invalid')
        git(self.pd, 'config', 'user.name', 'test')
        (self.pd / 'README').write_text('adoption\n')
        git(self.pd, 'add', '-A')
        git(self.pd, 'commit', '-qm', 'adoption')
        self.adoption = git(self.pd, 'rev-parse', 'HEAD')
        (self.pd / 'boards/board-p15/board-p15-draft.kicad_pcb').write_bytes(PCB)
        (self.pd / 'boards/board-p15/nvm/stusb4500-15v.bin').write_bytes(NVM)
        self.pd_record = {'adoption_revision': {'sha': self.adoption}, 'artifacts': [
            {'role': 'pcb', 'path': 'boards/board-p15/board-p15-draft.kicad_pcb', 'sha256': sha(PCB)},
            {'role': 'nvm-image', 'path': 'boards/board-p15/nvm/stusb4500-15v.bin', 'sha256': sha(NVM)}]}
        (self.pd / 'boards/board-p15/shared-reference.json').write_text(json.dumps(self.pd_record))
        git(self.pd, 'add', '-A')
        git(self.pd, 'commit', '-qm', 'record')
        self.commit = git(self.pd, 'rev-parse', 'HEAD')

        self.led = base / 'led'
        (self.led / 'boards/board-p').mkdir(parents=True)
        self.hist = b'(kicad_pcb historical LED board p)\n'
        (self.led / 'boards/board-p/board-p.kicad_pcb').write_bytes(self.hist)
        real = json.loads(vpr.RECORD.read_text())
        self.record = copy.deepcopy(real)
        self.record['owner']['record_commit'] = self.commit
        self.record['adoption']['zudo_pd_commit'] = self.adoption
        self.record['pinned_artifacts'] = copy.deepcopy(self.pd_record['artifacts'])
        self.record['historical_board_p']['sha256'] = sha(self.hist)

    def tearDown(self):
        self.tmp.cleanup()

    def run_all(self, record=None, rev=None):
        record = record or self.record
        errors = vpr.check_local(record, self.led)
        if not errors:
            errors += vpr.check_owner(record, self.pd, rev or record['owner']['record_commit'])[0]
        return errors

    def assertFailsWith(self, errors, needle):
        self.assertTrue(any(needle in e for e in errors), f'{needle!r} not in {errors}')

    def test_committed_record_shape_and_local_side(self):
        self.assertEqual(vpr.check_local(json.loads(vpr.RECORD.read_text())), [])

    def test_match(self):
        self.assertEqual(self.run_all(), [])

    def test_changed_owner_bytes_rejected(self):
        (self.pd / 'boards/board-p15/board-p15-draft.kicad_pcb').write_bytes(PCB + b'x')
        git(self.pd, 'commit', '-qam', 'drift')
        self.assertFailsWith(self.run_all(rev='HEAD'), 'have sha256')

    def test_changed_led_pin_rejected(self):
        self.record['pinned_artifacts'][1]['sha256'] = '0' * 64
        self.assertFailsWith(self.run_all(), '!= zudo-pd record')

    def test_wrong_board_path_rejected(self):
        self.record['pinned_artifacts'][0]['path'] = 'boards/board-p/board-p.kicad_pcb'
        self.assertFailsWith(self.run_all(), 'wrong board')

    def test_historical_board_p_change_rejected(self):
        (self.led / 'boards/board-p/board-p.kicad_pcb').write_bytes(self.hist + b'edit')
        self.assertFailsWith(self.run_all(), 'historical bytes changed')

    def test_historical_board_p_as_p15_rejected(self):
        (self.led / 'boards/board-p/board-p.kicad_pcb').write_bytes(PCB)
        self.record['historical_board_p']['sha256'] = sha(PCB)
        self.assertFailsWith(self.run_all(), 'equal a P15 artifact')

    def test_missing_owner_revision_is_failure(self):
        self.assertFailsWith(self.run_all(rev='0' * 40), 'not found')

    def test_missing_owner_record_is_failure(self):
        self.assertFailsWith(self.run_all(rev=self.adoption), 'missing at')

    def test_physical_claim_rejected(self):
        self.record['status']['measured'] = 'PASS'
        self.assertFailsWith(self.run_all(), 'claims physical state')


if __name__ == '__main__':
    unittest.main()
