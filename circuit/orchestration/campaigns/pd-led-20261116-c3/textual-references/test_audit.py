import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit


class TextualDispositionTests(unittest.TestCase):
    def test_all_locations_and_historical_extracts(self):
        result = audit.audit()
        self.assertEqual(result, audit.audit())
        self.assertEqual(result['locations'], 463)
        self.assertEqual(result['categories'], {
            'contextual_reason_or_condition': 70,
            'held_source_extract': 4,
            'other_locator': 49,
            'source_prefixed_locator': 340,
        })
        self.assertEqual(result['proposed_rewrite_locations'], 459)
        self.assertEqual(result['proposed_exact_token_replacements'], 584)
        self.assertEqual(result['remaining_old_id_locations_in_memory'], 4)
        held = [row for row in result['rows'] if row['category'] == 'held_source_extract']
        self.assertEqual(len(held), 4)
        self.assertTrue(all(row['old_sha256'] == row['proposed_sha256'] and
                            row['replacement_count'] == 0 for row in held))
        self.assertTrue(all(row['old_sha256'] != row['proposed_sha256'] for row in
                            result['rows'] if row not in held))

    def test_exact_token_boundary_and_scan_mismatch(self):
        mapping = {'src-a': 'led-src-a-hash'}
        pattern = audit.token_pattern(mapping)
        old = 'src-a: evidence; xsrc-a and src-a-extra are different identifiers'
        new, count = audit.propose_text(old, ['src-a'], mapping, pattern)
        self.assertEqual(count, 1)
        self.assertEqual(new, 'led-src-a-hash: evidence; xsrc-a and src-a-extra are different identifiers')
        with self.assertRaisesRegex(ValueError, 'scan/replacement mismatch'):
            audit.propose_text(old, ['src-other'], mapping, pattern)

    def test_stale_saved_proposal_fails_before_translation(self):
        proposal = json.loads(audit.PROPOSAL.read_text())
        proposal['source_set_sha256'] = 'invalid'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'proposal.json'
            path.write_text(json.dumps(proposal))
            with patch.object(audit, 'PROPOSAL', path):
                with self.assertRaisesRegex(ValueError, 'source locks differ'):
                    audit.audit()


if __name__ == '__main__':
    unittest.main()
