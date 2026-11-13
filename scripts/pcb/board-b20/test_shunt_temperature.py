"""Check the manufacturer reference-temperature correction without changing the operating interval."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'calculate-board-b20-draft.py'
spec = importlib.util.spec_from_file_location('calculator', SOURCE)
calculator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator)


class ShuntTemperatureTests(unittest.TestCase):
    def test_resi_reference_is_20c_for_the_existing_5_to_45c_interval(self):
        result = calculator.limiter()
        for rail, power in (('+12', 0.0441606375), ('-12', 0.040055)):
            screen = result[rail]['shunt_temperature_screen']
            self.assertEqual(screen['operating_interval_c'], [5, 45])
            self.assertEqual(screen['reference_c'], 20)
            self.assertEqual(screen['maximum_delta_c'], 25)
            self.assertAlmostEqual(screen['resistance_max_ohm'], 0.01001375)
            self.assertAlmostEqual(screen['power_at_contract_max_w'], power)
            self.assertEqual(screen['working_power_bound_w'], 1)
        self.assertEqual(result['let_through']['status'], 'OPEN')

    def test_trip_bounds_widen_without_changing_the_five_volt_case(self):
        result = calculator.limiter()
        self.assertLess(result['+12']['trip_min_a'], 2.04175)
        self.assertGreater(result['+12']['trip_max_a'], 2.08470)
        self.assertLess(result['-12']['trip_min_a'], 1.94231)
        self.assertGreater(result['-12']['trip_max_a'], 1.99529)
        self.assertEqual((result['+5']['trip_min_a'], result['+5']['trip_max_a']), (0.43691, 0.46086))  # widened by the full-range REF5025 load row (D12)


if __name__ == '__main__':
    unittest.main()
