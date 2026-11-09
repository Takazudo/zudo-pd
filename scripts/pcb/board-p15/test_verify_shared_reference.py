"""Negative and positive checks for verify-shared-reference.py.

run: python3 -m unittest discover -s scripts/pcb/board-p15 -p 'test_*.py'
"""
import copy, hashlib, importlib.util, json, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('vsr', HERE / 'verify-shared-reference.py')
vsr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vsr)


class OverlaySource(vsr.Source):
    """The real worktree with selected files replaced in memory."""

    def __init__(self, overrides=None, commits_ok=True):
        super().__init__(ROOT, None)
        self.overrides, self.commits_ok = overrides or {}, commits_ok

    def read(self, path):
        if path in self.overrides:
            return self.overrides[path]
        return super().read(path)

    def has_commit(self, sha):
        return self.commits_ok and super().has_commit(sha)

    def is_ancestor(self, sha):
        return self.commits_ok and super().is_ancestor(sha)


def load_record():
    return json.loads((ROOT / vsr.RECORD).read_text())


PCB = 'boards/board-p15/board-p15-draft.kicad_pcb'


class SharedReferenceTest(unittest.TestCase):
    def assertFailsWith(self, errors, needle):
        self.assertTrue(any(needle in e for e in errors), f'{needle!r} not in {errors}')

    def test_committed_record_matches_worktree(self):
        errors, report = vsr.verify(OverlaySource(), load_record())
        self.assertEqual(errors, [])
        self.assertTrue(all(r['result'] == 'MATCH' for r in report['artifacts']))

    def test_changed_pcb_bytes_rejected(self):
        data = (ROOT / PCB).read_bytes() + b'\n'
        errors, _ = vsr.verify(OverlaySource({PCB: data}), load_record())
        self.assertFailsWith(errors, f'{PCB}: sha256')
        self.assertFailsWith(errors, 'no longer matches the frozen source lock')

    def test_each_artifact_is_required(self):
        for artifact in load_record()['artifacts']:
            with self.subTest(role=artifact['role']):
                rec = load_record()
                rec['artifacts'] = [a for a in rec['artifacts'] if a['role'] != artifact['role']]
                errors, _ = vsr.verify(OverlaySource(), rec)
                self.assertFailsWith(errors, f'no {artifact["role"]} artifact')

    def test_duplicate_role_rejected(self):
        rec = load_record()
        rec['artifacts'].append(copy.deepcopy(rec['artifacts'][0]))
        errors, _ = vsr.verify(OverlaySource(), rec)
        self.assertFailsWith(errors, 'duplicate pcb artifact')

    def test_swapped_roles_rejected_with_matching_hashes(self):
        rec = load_record()
        bom, cpl = rec['artifacts'][-2:]
        bom['role'], cpl['role'] = cpl['role'], bom['role']
        errors, _ = vsr.verify(OverlaySource(), rec)
        self.assertFailsWith(errors, 'unexpected role/path assignment')

    def test_changed_population_files_rejected(self):
        for role in ('population-bom', 'population-cpl'):
            artifact = next(a for a in load_record()['artifacts'] if a['role'] == role)
            path = artifact['path']
            with self.subTest(role=role):
                errors, _ = vsr.verify(OverlaySource({path: (ROOT / path).read_bytes() + b'\n'}), load_record())
                self.assertFailsWith(errors, f'{path}: sha256')

    def test_changed_nvm_bytes_rejected(self):
        path = 'boards/board-p15/nvm/stusb4500-15v.bin'
        data = bytearray((ROOT / path).read_bytes())
        data[0] ^= 0x01
        errors, _ = vsr.verify(OverlaySource({path: bytes(data)}), load_record())
        self.assertFailsWith(errors, f'{path}: sha256')

    def test_wrong_board_path_rejected_even_with_its_true_hash(self):
        rec = load_record()
        wrong = 'boards/board-p/board-p.kicad_pcb'
        for art in rec['artifacts']:
            if art['role'] == 'pcb':
                art['path'] = wrong
                art['sha256'] = hashlib.sha256((ROOT / wrong).read_bytes()).hexdigest()
        errors, _ = vsr.verify(OverlaySource(), rec)
        self.assertFailsWith(errors, 'forbidden board path')

    def test_path_outside_canonical_rejected(self):
        rec = load_record()
        rec['artifacts'][0]['path'] = 'boards/board-b/board-b.kicad_pcb'
        errors, _ = vsr.verify(OverlaySource(), rec)
        self.assertFailsWith(errors, 'outside the P15 canonical paths')

    def test_record_hash_updated_to_drifted_pcb_still_rejected(self):
        data = (ROOT / PCB).read_bytes() + b'\n'
        rec = load_record()
        rec['artifacts'][0]['sha256'] = hashlib.sha256(data).hexdigest()
        errors, _ = vsr.verify(OverlaySource({PCB: data}), rec)
        self.assertFailsWith(errors, 'record sha256 differs from the frozen source lock')

    def test_frozen_manifest_change_rejected(self):
        path = 'manufacturing/releases/corner-support-review/manifest.json'
        data = (ROOT / path).read_bytes().replace(b'3b9821b48cf4c77e8512ce653cada3db962d2c88',
                                                  b'0000000000000000000000000000000000000000')
        errors, _ = vsr.verify(OverlaySource({path: data}), load_record())
        self.assertFailsWith(errors, 'frozen package must not change')
        self.assertFailsWith(errors, 'git_base')

    def test_missing_frozen_package_rejected(self):
        path = 'manufacturing/releases/corner-support-review/SHA256SUMS'
        errors, _ = vsr.verify(OverlaySource({path: None}), load_record())
        self.assertFailsWith(errors, 'missing at the selected revision')

    def test_physical_claim_without_evidence_rejected(self):
        rec = load_record()
        rec['status']['programmed'] = 'PASS'
        errors, _ = vsr.verify(OverlaySource(), rec)
        self.assertFailsWith(errors, 'claims physical state')

    def test_status_fields_must_stay_separate(self):
        rec = load_record()
        del rec['status']['measured']
        errors, _ = vsr.verify(OverlaySource(), rec)
        self.assertFailsWith(errors, 'status.measured missing')

    def test_unknown_commit_rejected(self):
        errors, _ = vsr.verify(OverlaySource(commits_ok=False), load_record())
        self.assertFailsWith(errors, 'reviewed_commit')
        self.assertFailsWith(errors, 'adoption_revision')

    def test_unknown_revision_is_a_failure(self):
        self.assertEqual(vsr.main(['--rev', 'no-such-revision-xyz', '--repo', str(ROOT)]), 1)

    def test_old_revision_reports_schematic_drift(self):
        rec = copy.deepcopy(load_record())
        src = vsr.Source(ROOT, rec['frozen_package']['manifest_git_base'])
        errors, report = vsr.verify(src, rec)
        rows = {r['role']: r['result'] for r in report['artifacts']}
        self.assertEqual(rows['pcb'], 'MATCH')
        self.assertEqual(rows['nvm-image'], 'MATCH')
        self.assertEqual(rows['schematic-generated'], 'MISMATCH')
        self.assertFailsWith(errors, 'not an ancestor')


if __name__ == '__main__':
    unittest.main()
