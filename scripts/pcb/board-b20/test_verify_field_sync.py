"""Controls for verify-field-sync.py: a field-only change passes, anything else is refused."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PCB = HERE.parents[2] / 'boards/board-b20-draft/board-b20-draft.kicad_pcb'
SCRIPT = HERE / 'verify-field-sync.py'
_spec = importlib.util.spec_from_file_location('verify_field_sync', SCRIPT)
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)


def edit(text, ref, name, old, new):
    start = text.index(f'(property "Reference" "{ref}"')
    at = text.index(f'(property "{name}" "{old}"', start)
    return text[:at] + f'(property "{name}" "{new}"' + text[at + len(f'(property "{name}" "{old}"'):]


class VerifyFieldSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PCB.read_text()
        cls.fp_value = verify.footprint_fields(verify.parse(verify.tokenize(cls.text)))
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_check(self, text, refs):
        after = Path(self.tmp.name) / 'after.kicad_pcb'
        after.write_text(text)
        return subprocess.run([sys.executable, str(SCRIPT), str(PCB), str(after), refs, str(Path(self.tmp.name) / 'out.json')],
                              capture_output=True, text=True)

    def value(self, ref, name):
        return verify.atom(self.fp_value[ref][name][2])

    def test_field_only_change_passes(self):
        old_v, old_l = self.value('RRDY1', 'Value'), self.value('RRDY1', 'LCSC')
        text = edit(edit(self.text, 'RRDY1', 'Value', old_v, 'X1'), 'RRDY1', 'LCSC', old_l, 'C1')
        result = self.run_check(text, 'RRDY1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"X1"', result.stdout)

    def test_change_on_an_unexpected_footprint_is_refused(self):
        text = edit(self.text, 'RRDY2', 'Value', self.value('RRDY2', 'Value'), 'X2')
        result = self.run_check(text, 'RRDY1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('outside the expected', result.stdout + result.stderr)

    def test_moved_footprint_is_refused(self):
        start = self.text.index('(property "Reference" "RRDY1"')
        at = self.text.rindex('(at ', 0, start)
        end = self.text.index(')', at)
        text = self.text[:at] + '(at 1 1 0' + self.text[end:]
        result = self.run_check(text, 'RRDY1')
        self.assertNotEqual(result.returncode, 0)

    def test_changed_fill_is_refused(self):
        at = self.text.index('(filled_polygon')
        xy = self.text.index('(xy ', at)
        text = self.text[:xy] + '(xy 0.001 0.001) ' + self.text[xy:]
        result = self.run_check(text, 'RRDY1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('filled copper', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
