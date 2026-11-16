import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit


class CalculationFeasibilityTests(unittest.TestCase):
    def test_real_locked_calculations_validate_and_repeat(self):
        first = audit.audit()
        self.assertEqual(first, audit.audit())
        self.assertEqual(first['calculation_count'], 9)
        self.assertEqual(first['focused_validator_passes'], 9)
        self.assertEqual(first['current_pd_calculation_id_collisions'], 0)
        self.assertEqual(first['proposed_pd_calculation_id_collisions'], 0)
        self.assertEqual(len({row['proposed_calculation_id'] for row in first['calculation_rows']}), 9)
        self.assertEqual(sum(row['scenario_count'] for row in first['calculation_rows']), 19)
        self.assertTrue(all(row['focused_validator_result'] == 'PASS'
                            for row in first['calculation_rows']))

    def test_symbol_replacement_preserves_scenario_variables_and_tokens(self):
        expression = 'fact_a + fact_ab + rail_v + fact_a_extra'
        translated = audit.replace_symbols(expression, {'fact_a': 'led_fact_a_1',
                                                        'fact_ab': 'led_fact_ab_2'})
        self.assertEqual(translated, 'led_fact_a_1 + led_fact_ab_2 + rail_v + fact_a_extra')

    def test_changed_locked_input_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = 'source.json'
            (root / path).write_text(json.dumps({'x': 1}))
            locks = {path: audit.sha256((root / path).read_bytes())}
            with patch.object(audit, 'ROOT', root):
                self.assertEqual(audit.locked_json(path, locks), {'x': 1})
                (root / path).write_text(json.dumps({'x': 2}))
                with self.assertRaisesRegex(ValueError, 'locked input changed'):
                    audit.locked_json(path, locks)

    def test_installed_calculation_validator_rejects_stale_alias(self):
        facts = {'led-fact-a': {'value': 2}}
        rule = {'fact_ids': ['led-fact-a']}
        calc = {'calculation_id': 'led-calc-a', 'fact_ids': ['led-fact-a'],
                'expression': 'fact_a + 1', 'result_key': 'result', 'result': 3,
                'conditions': 'fixture'}
        with self.assertRaisesRegex(Exception, 'declared numeric fact is unused'):
            audit.validate_calculation(calc, rule, facts)
        calc['expression'] = 'led_fact_a + 1'
        audit.validate_calculation(calc, rule, facts)


if __name__ == '__main__':
    unittest.main()
