"""Refusal and pass checks for verify-upload-files.py on synthetic packages and the committed package.

run: python3 -m unittest discover -s scripts/pcb/pd20-order -p 'test_*.py'
"""
import hashlib, importlib.util, io, json, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('vuf', HERE / 'verify-upload-files.py')
vuf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vuf)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Package:
    """A minimal release folder: six upload files, manifest.json and SHA256SUMS."""

    def __init__(self, root):
        self.root = Path(root)
        self.files = {relative: f'content of {relative}\n'.encode() for relative in vuf.UPLOAD_FILES}
        self.files['board-p/excluded.csv'] = b'Designator,Reason\n'
        self.manifest = {'boards': [{'board': b} for b in vuf.BOARDS],
                         'artifact_hashes': {r: sha(d) for r, d in self.files.items()}}
        self.extra_sum_lines = []

    def write(self, manifest_sum=None):
        for relative, data in self.files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        manifest_bytes = json.dumps(self.manifest).encode()
        (self.root / 'manifest.json').write_bytes(manifest_bytes)
        lines = [f'{sha(d)}  {r}' for r, d in self.files.items()]
        lines.append(f'{manifest_sum or sha(manifest_bytes)}  manifest.json')
        lines += self.extra_sum_lines
        (self.root / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')
        return self.root


class VerifyUploadFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pkg = Package(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def refuse(self, pattern):
        with self.assertRaisesRegex(vuf.Refusal, pattern):
            vuf.check(self.pkg.root)

    def test_clean_package_passes_with_exactly_six_files(self):
        results = vuf.check(self.pkg.write())
        self.assertEqual([r for r, _ in results], list(vuf.UPLOAD_FILES))
        self.assertEqual(len(results), 6)

    def test_missing_upload_file_is_refused(self):
        self.pkg.write()
        (self.pkg.root / 'board-b20-draft/cpl.csv').unlink()
        self.refuse('missing file: board-b20-draft/cpl.csv')

    def test_tampered_upload_file_is_refused(self):
        self.pkg.write()
        (self.pkg.root / 'board-p/bom.csv').write_bytes(b'tampered\n')
        self.refuse('bytes differ from the package lock: board-p/bom.csv')

    def test_duplicate_checksum_entry_is_refused(self):
        self.pkg.extra_sum_lines = [f'{"0" * 64}  board-p/cpl.csv']
        self.pkg.write()
        self.refuse('lists board-p/cpl.csv more than once')

    def test_manifest_and_checksum_disagreement_is_refused(self):
        self.pkg.manifest['artifact_hashes']['board-b20-draft/board-b20-draft-gerbers.zip'] = '1' * 64
        self.pkg.write()
        self.refuse('manifest and SHA256SUMS disagree for board-b20-draft/board-b20-draft-gerbers.zip')

    def test_manifest_not_matching_its_checksum_is_refused_first(self):
        self.pkg.write(manifest_sum='2' * 64)
        (self.pkg.root / 'board-p/bom.csv').write_bytes(b'also tampered\n')
        self.refuse('manifest.json does not match its SHA256SUMS entry')

    def test_missing_checksum_entry_is_refused(self):
        self.pkg.write()
        sums = self.pkg.root / 'SHA256SUMS'
        sums.write_text(''.join(l + '\n' for l in sums.read_text().splitlines() if not l.endswith('  board-p/cpl.csv')))
        self.refuse('no entry for board-p/cpl.csv')

    def test_missing_manifest_lock_is_refused(self):
        del self.pkg.manifest['artifact_hashes']['board-p/board-p-gerbers.zip']
        self.pkg.write()
        self.refuse('manifest artifact_hashes has no entry for board-p/board-p-gerbers.zip')

    def test_invalid_checksum_paths_are_refused(self):
        for bad in ('../outside.csv', '/abs/bom.csv', 'board-p/./bom.csv', 'board-p\\bom.csv'):
            with self.subTest(bad=bad):
                self.pkg.extra_sum_lines = [f'{"3" * 64}  {bad}']
                self.pkg.write()
                self.refuse('invalid path')

    def test_malformed_checksum_line_is_refused(self):
        self.pkg.extra_sum_lines = ['not a checksum line']
        self.pkg.write()
        self.refuse('is not')

    def test_malformed_manifest_types_fail_cleanly(self):
        for manifest in ([], {'boards': [{}], 'artifact_hashes': {}}, {'boards': [], 'artifact_hashes': []}):
            with self.subTest(manifest=manifest):
                self.pkg.manifest = manifest
                self.pkg.write()
                self.refuse('expected boards / artifact_hashes structure')

    def test_unexpected_manifest_is_refused_when_pinned(self):
        self.pkg.write()
        with self.assertRaisesRegex(vuf.Refusal, 'not the expected export'):
            vuf.check(self.pkg.root, expected_manifest='4' * 64)

    def test_symlinked_checksum_file_is_refused(self):
        self.pkg.write()
        sums = self.pkg.root / 'SHA256SUMS'
        real = self.pkg.root / 'real-sums'
        sums.rename(real)
        sums.symlink_to(real)
        self.refuse('symlink')

    def test_wrong_board_set_is_refused(self):
        self.pkg.manifest['boards'] = [{'board': 'board-p15'}, {'board': 'board-b'}]
        self.pkg.write()
        self.refuse('expected exactly')

    def test_symlink_escaping_release_is_refused(self):
        self.pkg.write()
        outside = Path(self.tmp.name).parent / f'{Path(self.tmp.name).name}-outside.csv'
        outside.write_bytes(self.pkg.files['board-p/cpl.csv'])
        self.addCleanup(outside.unlink)
        target = self.pkg.root / 'board-p/cpl.csv'
        target.unlink()
        target.symlink_to(outside)
        self.refuse('outside the release folder')

    def test_cli_failure_states_scope_and_exit_code(self):
        self.pkg.write()
        (self.pkg.root / 'board-p/bom.csv').write_bytes(b'tampered\n')
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(vuf.main(['--release', str(self.pkg.root)]), 1)
        self.assertIn('UPLOAD FILE INTEGRITY: FAIL', err.getvalue())
        self.assertIn('NOT a complete engineering replay', err.getvalue())

    def test_committed_package_passes(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(vuf.main([]), 0)
        self.assertIn('UPLOAD FILE INTEGRITY: PASS (6/6', out.getvalue())
        self.assertIn('pinned manifest f430a76a… matched', out.getvalue())
        self.assertNotIn('populated-stack.step', out.getvalue())


if __name__ == '__main__':
    unittest.main()
