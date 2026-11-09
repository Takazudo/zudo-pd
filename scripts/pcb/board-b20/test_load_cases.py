"""Regression checks: B20 desk load cases stay bound to the PD20 contract and the committed reports stay fresh.

usage: python3 -m unittest discover -s scripts/pcb/board-b20 -p 'test_*.py'
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import load_cases as lc  # noqa: E402

BOARD = ROOT / 'boards/board-b20-draft'
STATUS = ROOT / 'manufacturing/pd20-status.md'
CONTRACT_RE = re.compile(
    r'OSC current contract: \+12 / −12 / \+5 V continuous (?P<continuous>[\d. /]+) A; '
    r'20 ms transient (?P<transient_20ms>[\d. /]+) A; let-through maximum (?P<let_through_max>[\d. /]+) A')


def triple(text):
    return dict(zip(('+12', '-12', '+5'), (float(v) for v in text.split('/'))))


def keys(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from keys(v)
    elif isinstance(node, list):
        for v in node:
            yield from keys(v)


class ContractBinding(unittest.TestCase):
    def test_contract_cases_match_owner(self):
        m = CONTRACT_RE.search(STATUS.read_text())
        self.assertIsNotNone(m, 'contract sentence not found in manufacturing/pd20-status.md')
        for case in ('continuous', 'transient_20ms', 'let_through_max'):
            self.assertEqual(lc.CASES[case]['loads'], triple(m[case]), case)
            self.assertEqual(lc.CASES[case]['evidence'], 'CONTRACT')
        self.assertEqual(set(lc.CONTRACT_CASES), {'continuous', 'transient_20ms', 'let_through_max'})

    def test_legacy_case_is_not_contract_or_rated(self):
        legacy = lc.CASES['legacy_pd15_budget']
        self.assertEqual(legacy['evidence'], 'LEGACY_COMPARISON_ONLY')
        self.assertTrue(legacy['source'].startswith('LEGACY'))
        self.assertFalse(any('rated' in case for case in lc.CASES))

    def test_transient_case_states_model_limit(self):
        self.assertIn('not a transient model', lc.CASES['transient_20ms']['model_limit'])


class DerivedCurrents(unittest.TestCase):
    def test_coherent_derivation(self):
        for case in lc.CASES:
            c = lc.case_currents(case)
            self.assertEqual(c['rail_a'], lc.CASES[case]['loads'])
            for rail in ('+12', '+5'):
                self.assertEqual(c['inductor_a'][rail], c['rail_a'][rail])
            self.assertGreater(c['inductor_a']['-12'], c['rail_a']['-12'])
            for rail in lc.RAILS:
                self.assertGreater(c['inductor_rms_a'][rail], c['inductor_a'][rail])
            stage_sum = sum(c['stage_input_a'].values()) + lc.CONTROL_W / lc.VIN
            self.assertAlmostEqual(c['vin_total_a'], stage_sum, delta=0.003)

    def test_current_report_uses_derived_currents(self):
        report = json.loads((BOARD / 'current-check.json').read_text())
        self.assertEqual(report['vin_v'], lc.VIN)
        for case in lc.CASES:
            self.assertEqual(report['load_cases'][case]['derived_currents_a'], lc.case_currents(case))
            self.assertEqual(report['load_cases'][case]['loads_a'], lc.CASES[case]['loads'])
        for row in report['paths']:
            self.assertEqual(set(row['current_a']), set(lc.CASES))
            if row['net'] == 'M12_RAW':
                for case in lc.CASES:
                    self.assertEqual(row['current_a'][case], lc.case_currents(case)['inductor_a']['-12'])
        for row in report['stage_cells']:
            for case in lc.CASES:
                self.assertEqual(row['current_bound_a'][case], lc.case_currents(case)['inductor_rms_a'][row['stage']])


class ReportFreshness(unittest.TestCase):
    def test_thermal_report_reproduces(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'thermal-check.json'
            subprocess.run([sys.executable, str(HERE / 'thermal-check.py'), str(out)], check=True, cwd=ROOT)
            self.assertEqual(out.read_bytes(), (BOARD / 'thermal-check.json').read_bytes())

    def test_reports_carry_no_rated_case(self):
        for path in (BOARD / 'thermal-check.json', BOARD / 'current-check.json', BOARD / 'loop-check.json',
                     ROOT / 'manufacturing/power-budget-b20.json', ROOT / 'manufacturing/power-layout-b20.json'):
            found = [k for k in keys(json.loads(path.read_text())) if re.search(r'(^|_)rated(_|$)|limiter_max', k)]
            self.assertEqual(found, [], path.name)

    def test_budget_binds_current_thermal_report(self):
        budget = json.loads((ROOT / 'manufacturing/power-budget-b20.json').read_text())
        thermal = BOARD / 'thermal-check.json'
        self.assertEqual(budget['thermal_source_sha256'], hashlib.sha256(thermal.read_bytes()).hexdigest())
        self.assertEqual(budget['load_cases'], {case: lc.case_record(case) for case in lc.CASES})
        layout = json.loads((ROOT / 'manufacturing/power-layout-b20.json').read_text())
        for name, digest in layout['source_reports_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)

    def test_pickup_uses_largest_contract_case(self):
        loop = json.loads((BOARD / 'loop-check.json').read_text())['pickup_assumptions']
        self.assertEqual(loop['switched_current_case'], 'let_through_max')
        self.assertEqual(loop['switched_current_a']['A'], lc.CASES['let_through_max']['loads']['+12'])


if __name__ == '__main__':
    unittest.main()
