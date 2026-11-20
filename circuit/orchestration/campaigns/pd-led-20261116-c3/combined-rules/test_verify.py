import copy
import unittest

import verify


class CombinedRuleTests(unittest.TestCase):
    def test_combined_rules_pass_and_repeat(self):
        first = verify.verify()
        self.assertEqual(first, verify.verify())
        self.assertEqual(first['pd_rules'], 11)
        self.assertEqual(first['translated_led_rules'], 8)
        self.assertEqual(first['combined_rules_validated'], 19)
        self.assertEqual(first['combined_records'], 180)
        self.assertEqual(first['combined_facts'], 1868)
        self.assertEqual(first['combined_sources'], 464)
        self.assertEqual(first['translated_led_calculations'], 9)
        self.assertEqual(first['held_textual_locations'], 463)

    def test_missing_cross_corpus_fact_fails_closed(self):
        aggregate, rules, schema, candidates, candidate_facts, _, _, _, pd_count = verify.combined_data()
        damaged = copy.deepcopy(rules)
        damaged[pd_count]['fact_ids'][0] = 'fact-absent'
        with self.assertRaisesRegex(Exception, 'unknown record/fact ID'):
            verify.validate_rules(damaged, aggregate, schema,
                                  candidate_record_ids=candidates,
                                  candidate_fact_ids=candidate_facts)

    def test_stale_led_scenario_fails_closed(self):
        aggregate, rules, schema, candidates, candidate_facts, _, _, _, pd_count = verify.combined_data()
        damaged = copy.deepcopy(rules)
        led_rules = damaged[pd_count:]
        calc = next(calc for rule in led_rules for calc in rule.get('conditioned_calculations', [])
                    if calc.get('results'))
        calc['results'][0][calc['result_key']] += 1
        with self.assertRaisesRegex(Exception, 'scenario result is stale'):
            verify.validate_rules(damaged, aggregate, schema,
                                  candidate_record_ids=candidates,
                                  candidate_fact_ids=candidate_facts)


if __name__ == '__main__':
    unittest.main()
