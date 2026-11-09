"""Synthetic stale-evidence controls, not CAD or circuit simulation."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import report_provenance as rp

spec = importlib.util.spec_from_file_location('exporter', Path(__file__).resolve().parents[1]/'export-jlcpcb.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class FreshnessTests(unittest.TestCase):
    def write(self, name, value):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) if isinstance(value, (dict, list)) else value)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in (*rp.OWNER_PATHS, f'{rp.OWNER}/power-report.py', 'scripts/schgen/board_p_spec.py'):
            self.write(name, 'synthetic source: '+name)
        self.write(rp.BOARD, 'synthetic B20 PCB')
        self.write('boards/board-p/board-p.kicad_pcb', 'synthetic P PCB')
        self.receipt = {'pcb_sha256': rp.digest(self.root/rp.BOARD), 'kicad_version': '10.0.6',
                        'owner_sha256': rp.owner_hashes(self.root), 'geom_sha256': 'a'*64,
                        'routes_sha256': 'b'*64, 'native_track_count': 2, 'native_via_count': 1}
        self.write(rp.RECEIPT, self.receipt)
        self.reports = {'routing-report': {'tracks': 2, 'vias': 1, 'unrouted': []}}
        for name in ('current-check', 'loop-check', 'thermal-check'):
            inputs = {'pcb': self.receipt['pcb_sha256']} if name == 'thermal-check' else {'geom': 'a'*64, 'routes': 'b'*64}
            self.reports[name] = {'input_binding': rp.calculation_binding(name+'.py', inputs, self.root, settings={'plane_height_mm': 0.2175} if name == 'loop-check' else {}), 'synthetic_result': 1}
        self.write_reports()
        binding = rp.verify_native_report_inputs(self.root)
        generator = f'{rp.OWNER}/power-report.py'
        common = {'source_generator': generator, 'source_generator_sha256': rp.digest(self.root/generator),
                  'native_input_binding': binding}
        self.layout = {**common, 'status': 'PASS', 'pcb_sha256': self.receipt['pcb_sha256'],
                       'negative_filled_zone_areas': [], 'ground_filled_zone_areas_mm2': {'In1.Cu': 1}}
        self.budget = {**common, 'board_p': 'board-p', 'board_b': 'board-b20-draft',
                       'board_p_spec_sha256': rp.digest(self.root/'scripts/schgen/board_p_spec.py'),
                       'board_b20_draft_spec_sha256': rp.digest(self.root/'scripts/schgen/board_b20_spec.py'),
                       'protection_pcb_source_sha256': {'board-p': rp.digest(self.root/'boards/board-p/board-p.kicad_pcb'),
                                                        'board-b20-draft': self.receipt['pcb_sha256']},
                       'actual_filled_copper': {'pcb_sha256': self.receipt['pcb_sha256'], 'negative_zones': [],
                                                'ground_zone_areas_mm2': {'In1.Cu': 1}},
                       'thermal_source': 'boards/board-b20-draft/thermal-check.json'}
        self.write_aggregates()

    def write_reports(self):
        for name, report in self.reports.items():
            self.write(f'boards/board-b20-draft/{name}.json', report)

    def write_aggregates(self):
        self.layout['source_reports_sha256'] = {f'boards/board-b20-draft/{n}.json': rp.digest(self.root/'boards/board-b20-draft'/f'{n}.json') for n in rp.REPORT_NAMES}
        self.budget['thermal_source_sha256'] = rp.digest(self.root/self.budget['thermal_source'])
        self.write('manufacturing/power-layout-b20.json', self.layout)
        self.write('manufacturing/power-budget-b20.json', self.budget)

    def check(self):
        exporter.verify_power_report_freshness(self.root, 'board-p', 'board-b20-draft')

    def test_complete_synthetic_binding_passes(self):
        self.check()

    def test_aggregate_rehash_cannot_hide_wrong_calculation_input(self):
        self.reports['current-check']['input_binding']['inputs_sha256']['geom'] = 'c'*64
        self.write_reports(); self.write_aggregates()
        with self.assertRaisesRegex(ValueError, 'current-check'):
            self.check()

    def test_aggregate_rebinding_cannot_hide_stale_native_receipt(self):
        self.write(rp.BOARD, 'changed PCB')
        changed = rp.digest(self.root/rp.BOARD)
        self.layout['pcb_sha256'] = changed
        self.budget['protection_pcb_source_sha256']['board-b20-draft'] = changed
        self.budget['actual_filled_copper']['pcb_sha256'] = changed
        self.write_aggregates()
        with self.assertRaisesRegex(ValueError, 'native report input PCB'):
            self.check()

    def test_calculator_or_shared_dependency_change_fails(self):
        self.write(f'{rp.OWNER}/load_cases.py', 'changed assumptions')
        with self.assertRaisesRegex(ValueError, 'owner/dependency'):
            self.check()

    def test_missing_or_unbound_native_evidence_fails(self):
        del self.reports['loop-check']['input_binding']
        self.write_reports(); self.write_aggregates()
        with self.assertRaisesRegex(ValueError, 'loop-check'):
            self.check()
        (self.root/rp.RECEIPT).unlink()
        with self.assertRaises(FileNotFoundError):
            self.check()

    def test_refreshed_report_hash_cannot_hide_wrong_native_count(self):
        self.reports['routing-report']['vias'] += 1
        self.write_reports(); self.write_aggregates()
        with self.assertRaisesRegex(ValueError, 'routing counts'):
            self.check()

    def test_aggregate_generator_and_report_tampering_fail(self):
        self.write(f'{rp.OWNER}/power-report.py', 'changed aggregator')
        with self.assertRaisesRegex(ValueError, 'generator changed'):
            self.check()

    def test_changed_result_without_regeneration_fails(self):
        self.reports['current-check']['synthetic_result'] = 2
        self.write_reports()
        with self.assertRaisesRegex(ValueError, 'calculation reports changed'):
            self.check()

    def test_noncanonical_plane_height_cannot_be_aggregated(self):
        self.reports['loop-check']['input_binding']['settings']['plane_height_mm'] = 0.0
        self.write_reports(); self.write_aggregates()
        with self.assertRaisesRegex(ValueError, 'loop-check'):
            self.check()

    def test_p15_pair_does_not_require_pd20_receipt(self):
        self.write('boards/board-p15/board-p15-draft.kicad_pcb', 'P15')
        self.write('boards/board-b/board-b.kicad_pcb', 'B')
        for name in ('board_p15_spec', 'board_b_spec'):
            self.write('scripts/schgen/'+name+'.py', name)
        hashes = {'board-p15': rp.digest(self.root/'boards/board-p15/board-p15-draft.kicad_pcb'),
                  'board-b': rp.digest(self.root/'boards/board-b/board-b.kicad_pcb')}
        pair = exporter.PAIRS[('board-p15', 'board-b')]
        self.write('manufacturing/'+pair['layout'], {'status': 'PASS', 'pcb_sha256': hashes['board-b'],
            'negative_filled_zone_areas': [], 'ground_filled_zone_areas_mm2': {}})
        self.write('manufacturing/'+pair['budget'], {'board_p': 'board-p15', 'board_b': 'board-b',
            'board_p15_spec_sha256': rp.digest(self.root/'scripts/schgen/board_p15_spec.py'),
            'board_b_spec_sha256': rp.digest(self.root/'scripts/schgen/board_b_spec.py'),
            'protection_pcb_source_sha256': hashes,
            'actual_filled_copper': {'pcb_sha256': hashes['board-b'], 'negative_zones': [], 'ground_zone_areas_mm2': {}}})
        (self.root/rp.RECEIPT).unlink()
        exporter.verify_power_report_freshness(self.root, 'board-p15', 'board-b')


if __name__ == '__main__':
    unittest.main()
