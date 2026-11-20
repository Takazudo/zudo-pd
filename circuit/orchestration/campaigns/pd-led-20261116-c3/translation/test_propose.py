import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import propose


class TranslationTests(unittest.TestCase):
    def test_real_corpus_is_closed_collision_free_and_repeatable(self):
        first = propose.proposal()
        self.assertEqual(first, propose.proposal())
        self.assertEqual(first['counts']['unresolved_led_references'], 0)
        mappings = first['mappings']
        ids = [row['proposed_id'] for row in mappings]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), first['counts']['led_definitions'])
        self.assertTrue(all(ref['proposed_id'] for ref in first['reference_translation']))
        self.assertTrue(any('/record_ids/' in ref['pointer'] and ref['kind'] == 'record'
                            for ref in first['reference_translation']))
        self.assertTrue(any('/depends_on/' in ref['pointer'] and ref['kind'] == 'fact'
                            for ref in first['reference_translation']))
        self.assertTrue(any(row['kind'] == 'fact' and row['pd_collision']
                            for row in mappings))
        self.assertTrue(any(row['kind'] == 'rule' and row['pd_collision']
                            for row in mappings))
        self.assertEqual(first['counts']['arithmetic_expression_reviews'], 27)
        self.assertEqual(first['counts']['arithmetic_expression_mismatches'], 0)

    def test_global_duplicate_detection_ignores_owner_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = {}
            for owner in ('component-one', 'component-two'):
                path = f'products/led-lamp/.claude/skills/{owner}/facts.json'
                target = root / path
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps({'facts': [{'fact_id': 'fact-shared'}]}))
                files[path] = json.loads(target.read_text())
            with patch.object(propose, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'duplicate led fact ID'):
                    propose.definitions(files, 'led')

    def test_nested_refs_and_missing_dependency_are_explicit(self):
        files = {'fixture.json': {'interactions': [
            {'record_ids': ['rec-a', 'rec-b'], 'fact_ids': ['fact-a']}],
            'facts': [{'depends_on': ['fact-a', 'fact-missing']}],
            'routing_queries': [{'expected_line_ids': ['line-a']}]}}
        defs = {kind: {} for kind in [*propose.KINDS, *propose.EXTRA]}
        for kind, ids in {'record': ('rec-a', 'rec-b'), 'fact': ('fact-a',),
                          'line': ('line-a',)}.items():
            defs[kind] = {id_: {} for id_ in ids}
        refs, missing = propose.references(files, defs,
            {'record': {'rec-a': 'led-rec-a', 'rec-b': 'led-rec-b'},
             'fact': {'fact-a': 'led-fact-a'}, 'line': {'line-a': 'led-line-a'}})
        self.assertEqual(len(refs), 5)
        self.assertEqual([(item['id'], item['pointer']) for item in missing],
                         [('fact-missing', '/facts/0/depends_on/1')])
        self.assertIn(('rec-b', 'led-rec-b'),
                      [(item['id'], item['proposed_id']) for item in refs])

    def test_payload_and_file_bytes_bind_definition(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = 'products/led-lamp/.claude/skills/component-one/facts.json'
            target = root / path
            target.parent.mkdir(parents=True)
            with patch.object(propose, 'ROOT', root):
                target.write_text('{"facts":[{"fact_id":"fact-a","value":1}]}')
                original = propose.definitions({path: json.loads(target.read_text())}, 'led')['fact']['fact-a']
                target.write_text('{"facts":[{"fact_id":"fact-a","value":2}]}')
                revised = propose.definitions({path: json.loads(target.read_text())}, 'led')['fact']['fact-a']
            self.assertNotEqual(original['payload_sha256'], revised['payload_sha256'])
            self.assertNotEqual(original['source_sha256'], revised['source_sha256'])

    def test_textual_id_in_string_list_has_precise_pointer(self):
        files = {'fixture.json': {'notes': ['none', 'See fact-a and rec-b'],
                                  'nested': [{'phrases': ['src-c: locator']}],
                                  'fact_ids': ['fact-a']}}
        found = propose.textual_references(files, {'fact-a', 'rec-b', 'src-c'})
        self.assertEqual(found, [
            {'path': 'fixture.json', 'pointer': '/notes/1', 'ids': ['fact-a', 'rec-b']},
            {'path': 'fixture.json', 'pointer': '/nested/0/phrases/0', 'ids': ['src-c']},
        ])

    def test_arithmetic_dependency_and_expression_stay_paired(self):
        files = {'component-one/facts.json': {'facts': [{
            'fact_id': 'fact-total', 'depends_on': ['fact-a', 'fact-b'],
            'expression': 'fact_a + fact_b'}]}}
        rows = propose.arithmetic_review(files, {
            'fact-total': 'led-fact-total-1', 'fact-a': 'led-fact-a-1',
            'fact-b': 'led-fact-b-1'})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['proposed_expression_for_review'],
                         'led_fact_a_1 + led_fact_b_1')
        self.assertEqual(rows[0]['unmatched_expression_symbols'], [])
        self.assertEqual(rows[0]['unused_dependency_symbols'], [])


if __name__ == '__main__':
    unittest.main()
