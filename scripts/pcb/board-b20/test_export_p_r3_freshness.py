"""Negative controls for stale P correction evidence in a development export."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('exporter_p_freshness', Path(__file__).resolve().parents[1]/'export-jlcpcb.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class CorrectionFreshness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.names = ['scripts/pcb/board-p-r3-draft/build-draft.py',
                      'scripts/pcb/board-p-r3-draft/run.sh',
                      'boards/board-p/r3-draft/pours.json',
                      'boards/board-p/r3-draft/search-two-sided.json',
                      'boards/board-p/r3-draft/routes.json',
                      'scripts/schgen/board_p_spec.py']
        self.pcb = 'boards/board-p/board-p.kicad_pcb'
        for name in [*self.names, self.pcb]:
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic '+name)
        self.report = {'pcb_sha256': exporter.digest(self.root/self.pcb), 'kicad_version': '10.0.6',
                       'source_hashes': {name: exporter.digest(self.root/name) for name in self.names}}
        self.save()

    def save(self):
        (self.root/'boards/board-p/r3-draft/layout-correction-check.json').write_text(json.dumps(self.report))

    def check(self):
        exporter.verify_p_r3_report_freshness(self.root)

    def test_current_binding_passes(self):
        self.check()

    def test_changed_pcb_fails(self):
        (self.root/self.pcb).write_text('changed PCB')
        with self.assertRaisesRegex(ValueError, 'PCB proof is stale'):
            self.check()

    def test_changed_owner_fails(self):
        (self.root/self.names[0]).write_text('changed builder')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.check()

    def test_omitted_or_added_owner_input_fails(self):
        del self.report['source_hashes'][self.names[0]]
        self.save()
        with self.assertRaisesRegex(ValueError, 'omits current owner'):
            self.check()
        self.report['source_hashes'][self.names[0]] = exporter.digest(self.root/self.names[0])
        self.save()
        (self.root/'scripts/pcb/board-p-r3-draft/new-owner.py').write_text('new dependency')
        with self.assertRaisesRegex(ValueError, 'omits current owner'):
            self.check()

    def test_unpinned_tool_fails(self):
        self.report['kicad_version'] = '10.0.0'
        self.save()
        with self.assertRaisesRegex(ValueError, 'tool pin'):
            self.check()


if __name__ == '__main__':
    unittest.main()
