import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('capability', ROOT/'scripts/pcb/calculate-supply-capability.py')
capability = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capability)


class SupplyCapabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = capability.Screen()
        cls.budget = json.loads((ROOT/'manufacturing/power-budget.json').read_text())

    def test_pd_targets_reproduce_power_budget(self):
        result = self.screen.evaluate(dict(capability.TARGETS))
        whole = self.budget['whole_chain_current_thermal_screen']
        for rail, power in whole['pre_regulator_power_w'].items():
            if rail != 'total':
                self.assertAlmostEqual(result['rails'][rail]['pre_rail_power_w'], power, places=6)
        self.assertAlmostEqual(result['input']['required_weighted_converter_efficiency_at_3a']['14V'],
                               whole['minimum_weighted_converter_efficiency_at14v_3a'], places=9)

    def test_loads_above_ldo_evidence_are_not_screened_as_pass(self):
        result = self.screen.evaluate({'plus12': 1.55, 'minus12': .8, 'plus5': .5})
        self.assertEqual(result['rails']['plus12']['checks']['ldo_characterized_current']['status'], 'EXCEEDS_EVIDENCE')
        self.assertNotIn('pre_rail_power_w', result['rails']['plus12'])
        self.assertNotIn(result['status'], ('PASS_SCREEN', 'PASS_SCREEN_EFFICIENCY_OPEN'))

    def test_fail_outranks_exceeds_evidence(self):
        result = self.screen.evaluate({'plus12': 1.7, 'minus12': 1.6, 'plus5': .3})
        self.assertEqual(result['rails']['plus12']['status'], 'FAIL')
        self.assertEqual(result['status'], 'FAIL')

    def test_floor_uses_source_maximum(self):
        # 1.7/1.6/0.3 A needs about 97% at 15.75 V x 3 A: hard but not infeasible.
        near = self.screen.evaluate({'plus12': 1.7, 'minus12': 1.6, 'plus5': .3})['pre_rail_power_floor']
        self.assertAlmostEqual(near['required_weighted_converter_efficiency_at_3a']['15.75V'], .9706, places=3)
        self.assertEqual(near['status'], 'NOT RUN')
        far = self.screen.evaluate({'plus12': 2.0, 'minus12': 1.9, 'plus5': .4})['pre_rail_power_floor']
        self.assertEqual(far['status'], 'INFEASIBLE')
        # Independent floor: external current times the minimum pre-rail voltage.
        expected = 13.219794240119684*2.0 + 13.483572496263077*1.9 + 6.055019607843137*.4
        self.assertAlmostEqual(far['power_w'], expected, places=6)

    def test_per_rail_limits(self):
        limits = self.screen.rail_limits()
        self.assertAlmostEqual(limits['minus12']['u4_switch_current_limit'], 1.2168, places=3)
        self.assertAlmostEqual(limits['minus12']['input_42w_at_14v_3a_with_weighted_efficiency_1'], 1.2224, places=3)
        self.assertEqual(limits['minus12']['ptc_hold_85c'], .77)
        self.assertNotIn('j10_or_j11_single_header_contact', limits['plus12'])

    def test_committed_report_is_current(self):
        committed = json.loads((ROOT/'manufacturing/supply-capability.json').read_text())
        out = ROOT/'tmp'/'supply-capability-test.json'
        out.parent.mkdir(exist_ok=True)
        import subprocess, sys
        subprocess.run([sys.executable, str(ROOT/'scripts/pcb/calculate-supply-capability.py'), '--output', str(out)], check=True, capture_output=True)
        try:
            self.assertEqual(committed, json.loads(out.read_text()))
        finally:
            out.unlink()

if __name__ == '__main__':
    unittest.main()
