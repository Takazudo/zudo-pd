import unittest

import verify


class DryRunTests(unittest.TestCase):
    def test_real_proposal_applies_with_closed_references(self):
        result = verify.verify()
        self.assertEqual(result['translated_definitions'], 795)
        self.assertEqual(result['changed_structured_references'], 3896)
        self.assertEqual(result['changed_expressions'], 27)
        self.assertEqual(result['unresolved_translated_references'], 0)
        self.assertEqual(result['unexpected_changed_leaves'], 0)

    def test_pointer_handles_nested_arrays_and_escaped_keys(self):
        document = {'a/b': [{'~key': 'rec-a'}]}
        self.assertEqual(verify.value_at(document, '/a~1b/0/~0key'), 'rec-a')
        verify.set_at(document, '/a~1b/0/~0key', 'led-rec-a')
        self.assertEqual(document['a/b'][0]['~key'], 'led-rec-a')

    def test_changed_leaves_flags_unapproved_payload_mutation(self):
        before = {'facts': [{'fact_id': 'fact-a', 'verdict': 'UNSOURCED'}]}
        after = {'facts': [{'fact_id': 'led-fact-a', 'verdict': 'PASS - primary-source confirmed'}]}
        self.assertEqual(verify.changed_leaves(before, after),
                         {'/facts/0/fact_id', '/facts/0/verdict'})


if __name__ == '__main__':
    unittest.main()
