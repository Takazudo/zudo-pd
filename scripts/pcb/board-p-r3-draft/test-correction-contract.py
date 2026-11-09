"""Host-only negative controls for native evidence coverage and freshness."""
import copy
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from correction_contract import validate_coverage
from native_receipt import read_native_receipt, sha

ROOT = Path(__file__).resolve().parents[3]


class Coverage(unittest.TestCase):
    def setUp(self):
        self.pours = json.loads((ROOT/'boards/board-p/r3-draft/pours.json').read_text())
        self.constraints = json.loads((ROOT/'boards/board-p/r3-draft/search-two-sided.json').read_text())['local_decoupling_constraints']

    def test_current(self):
        validate_coverage(self.pours, self.constraints)

    def test_missing_owner(self):
        for via in self.pours['vias']:
            if via.get('thermal_owner') == 'Q1.9':
                del via['thermal_owner']
        with self.assertRaises(ValueError):
            validate_coverage(self.pours, self.constraints)

    def test_missing_capacitor(self):
        del self.constraints['C34']
        with self.assertRaises(ValueError):
            validate_coverage(self.pours, self.constraints)

    def test_weakened_pin_contract(self):
        self.constraints['C30']['ic_pad'] = 'U1.21'
        with self.assertRaises(ValueError):
            validate_coverage(self.pours, self.constraints)


class Receipt(unittest.TestCase):
    def test_missing_stale_and_tampered(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            paths = [directory/name for name in ['pcb', 'schematic', 'project']]
            for path in paths:
                path.write_text(path.name)
            self.assertEqual(read_native_receipt(directory, *paths)['status'], 'NOT RUN')
            report = directory/'native.json'
            report.write_text(json.dumps({'kicad_version':'10.0.6', 'violations':[], 'unconnected_items':[], 'schematic_parity':[], 'ignored_checks':[], 'date':'fixture'}))
            receipt = {path.name+'_sha256':sha(path) for path in paths}
            receipt.update(report_file=report.name, report_sha256=sha(report), command=['pcb','drc','--schematic-parity','--severity-all'])
            (directory/'native-drc-receipt.json').write_text(json.dumps(receipt))
            self.assertEqual(read_native_receipt(directory, *paths)['errors'], 0)
            paths[0].write_text('changed PCB')
            self.assertEqual(read_native_receipt(directory, *paths)['status'], 'NOT RUN')
            paths[0].write_text('pcb')
            report.write_text('{}')
            with self.assertRaises(ValueError):
                read_native_receipt(directory, *paths)


class Replay(unittest.TestCase):
    def test_uuid_only_and_copper_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first, second, report = [directory/name for name in ['a.pcb', 'b.pcb', 'report.json']]
            first.write_text('(kicad_pcb (segment (width 0.2) (uuid "00000000-0000-0000-0000-000000000001")))')
            second.write_text('(kicad_pcb (segment (width 0.2) (uuid "00000000-0000-0000-0000-000000000002")))')
            command = [sys.executable, str(Path(__file__).with_name('verify-replay.py')), str(first), str(second), str(report)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            second.write_text(second.read_text().replace('(width 0.2)', '(width 0.1)'))
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(report.read_text())['equal_ignoring_generated_uuids'])
            duplicate = '(kicad_pcb (uuid "00000000-0000-0000-0000-000000000001") (uuid "00000000-0000-0000-0000-000000000001"))'
            first.write_text(duplicate); second.write_text(duplicate)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Duplicate native object UUIDs', result.stderr)


if __name__ == '__main__':
    unittest.main()
