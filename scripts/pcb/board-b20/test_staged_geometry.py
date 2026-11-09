import tempfile
import subprocess
import sys
import json
import unittest
from pathlib import Path
from verify_staged_geometry import compare, digest

BOARD = '''(kicad_pcb (version 20260101) (generator pcbnew)
 (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
 (footprint "part" (at 10 20 90) (uuid "fp")
  (property "Reference" "U1")
  (model "${KIPRJMOD}/model.step" (offset (xyz 0 0 1)))
  (pad "1" smd rect (at 1 2) (size 2 3) (layers "F.Cu" "F.Mask") (net "N")))
 (segment (start 1 2) (end 3 4) (width 0.25) (layer "F.Cu") (net "N") (uuid "t"))
 (via (at 3 4) (size 0.5) (drill 0.2) (layers "F.Cu" "B.Cu") (net "N"))
 (zone (net "N") (layer "F.Cu") (clearance 0.2)
  (polygon (pts (xy 0 0) (xy 10 0) (xy 10 10) (xy 0 10)))
  (filled_polygon (layer "F.Cu") (pts (xy 1 1) (xy 9 1) (xy 9 9) (xy 1 9)))))'''


class StagedGeometryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source.kicad_pcb'
        self.staged = self.root/'staged.kicad_pcb'
        self.source.write_text(BOARD)

    def result(self, data):
        self.staged.write_text(data)
        return compare(self.source, self.staged)['manufacturing_geometry_equal']

    def test_identical(self):
        self.assertTrue(self.result(BOARD))

    def test_only_known_nonphysical_spelling(self):
        text = BOARD.replace('(uuid "fp")','(uuid "another")').replace('(generator pcbnew)','(generator exporter)')
        text = text.replace('(width 0.25)','(width 0.2500)').replace('(xy 1 1) (xy 9 1) (xy 9 9) (xy 1 9)',
                    '(xy 9 9) (xy 9 1) (xy 1 1) (xy 1 9) (xy 9 9)')
        self.assertTrue(self.result(text))

    def test_declared_object_order(self):
        self.assertTrue(self.result(BOARD.replace('(at 10 20 90) (uuid "fp")', '(uuid "fp") (at 10 20 90)')))

    def test_resolved_model_path(self):
        self.assertTrue(self.result(BOARD.replace('${KIPRJMOD}/model.step',str(self.root/'model.step'))))
        self.assertFalse(self.result(BOARD.replace('model.step','different.step')))

    def test_each_manufacturing_change_rejected(self):
        changes = [('(size 2 3)','(size 2 3.001)'), ('(at 1 2)','(at 1.001 2)'),
                   ('(width 0.25)','(width 0.26)'), ('(end 3 4)','(end 3 4.001)'),
                   ('(drill 0.2)','(drill 0.21)'), ('(size 0.5)','(size 0.51)'),
                   ('(clearance 0.2)','(clearance 0.21)'), ('(xy 10 10)','(xy 10.001 10)'),
                   ('(xy 9 9)','(xy 9.000001 9)'), ('(xyz 0 0 1)','(xyz 0 0 1.1)'),
                   ('(layers "F.Cu" "F.Mask")','(layers "F.Cu" "F.Paste")'),
                   ('(net "N")','(net "OTHER")'), ('(at 10 20 90)','(at 20 10 90)')]
        for old,new in changes:
            with self.subTest(change=new):self.assertFalse(self.result(BOARD.replace(old,new,1)))

    def test_cli_blocks_changed_fill_with_failed_receipt(self):
        self.staged.write_text(BOARD.replace('(xy 9 9)','(xy 9.000001 9)'))
        output=self.root/'receipt.json'
        process=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_staged_geometry.py')),
            str(self.source),str(self.staged),'--expected-source-sha256',digest(self.source),
            '--output',str(output)],capture_output=True,text=True)
        self.assertNotEqual(process.returncode,0)
        self.assertFalse(json.loads(output.read_text())['manufacturing_geometry_equal'])
        self.assertIn('export blocked',process.stderr)

    def test_unknown_fields_not_discarded(self):
        self.assertFalse(self.result(BOARD.replace('(clearance 0.2)','(clearance 0.2) (future_geometry 1)')))

    def test_stale_approved_source_rejected(self):
        self.staged.write_text(BOARD)
        approved=digest(self.source)
        self.source.write_text(BOARD.replace('(drill 0.2)','(drill 0.3)'))
        with self.assertRaisesRegex(ValueError,'changed after export staging'):
            compare(self.source,self.staged,approved)

    def test_duplicate_or_missing_objects_rejected(self):
        self.assertFalse(self.result(BOARD.replace('(clearance 0.2)','(clearance 0.2) (clearance 0.2)')))
        self.assertFalse(self.result(BOARD.replace('(drill 0.2)','')))


if __name__ == '__main__':unittest.main()
