"""Product-specific export report selection; no CAD/export or package writes."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('report_selection_exporter',
    Path(__file__).resolve().parents[1]/'export-jlcpcb.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ReportSelectionTests(unittest.TestCase):
    def test_pd20_contains_only_pd20_reports(self):
        self.assertEqual(exporter.power_report_files(('board-p','board-b20-draft')),
                         ('power-budget-b20.json','power-layout-b20.json'))

    def test_p15_preserves_existing_report_list(self):
        self.assertEqual(exporter.power_report_files(('board-p15','board-b')),
                         ('power-budget-p15.json','power-budget.md','power-layout.json'))

    def test_unreviewed_pairs_refused(self):
        for pair in [('board-p','board-b'),('board-p15','board-b20-draft'),
                     ('board-b20-draft','board-p'),('unknown','board-b')]:
            with self.subTest(pair=pair), self.assertRaisesRegex(ValueError,'No reviewed stack pairing'):
                exporter.power_report_files(pair)


if __name__ == '__main__':unittest.main()
