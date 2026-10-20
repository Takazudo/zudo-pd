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
        result = self.screen.evaluate({'plus12': 1.7, 'minus12': .8, 'plus5': .5})
        self.assertEqual(result['rails']['plus12']['status'], 'EXCEEDS_EVIDENCE')
        self.assertEqual(result['status'], 'EXCEEDS_EVIDENCE')

    def test_floor_marks_impossible_input_budget(self):
        result = self.screen.evaluate({'plus12': 2.0, 'minus12': 1.9, 'plus5': .4})
        self.assertEqual(result['pre_rail_power_floor']['status'], 'INFEASIBLE')

    def test_committed_report_is_current(self):
        committed = json.loads((ROOT/'manufacturing/supply-capability.json').read_text())
        self.assertEqual(committed['pd_target_evaluation'], json.loads(json.dumps(self.screen.evaluate(dict(capability.TARGETS)))))


if __name__ == '__main__':
    unittest.main()
