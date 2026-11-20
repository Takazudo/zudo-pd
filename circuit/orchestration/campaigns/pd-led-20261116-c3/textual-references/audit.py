#!/usr/bin/env python3
"""Source-bound, non-adopting disposition of LED textual ID mentions."""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
sys.path.insert(0, str(CAMPAIGN / 'translation'))
import propose  # noqa: E402

PROPOSAL = CAMPAIGN / 'translation/proposal.json'


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def at(document, pointer):
    node = document
    for token in pointer.lstrip('/').split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def set_at(document, pointer, value):
    tokens = [token.replace('~1', '/').replace('~0', '~')
              for token in pointer.lstrip('/').split('/')]
    node = document
    for token in tokens[:-1]:
        node = node[int(token)] if isinstance(node, list) else node[token]
    tail = tokens[-1]
    node[int(tail) if isinstance(node, list) else tail] = value


def token_pattern(ids):
    return re.compile(r'(?<![A-Za-z0-9_-])(' + '|'.join(
        re.escape(identifier) for identifier in sorted(ids, key=len, reverse=True)) +
        r')(?![A-Za-z0-9_-])')


def propose_text(source, ids, mapping, pattern):
    encountered = []

    def replace(match):
        old = match.group()
        encountered.append(old)
        return mapping[old]

    new = pattern.sub(replace, source)
    if sorted(set(encountered)) != ids or new == source:
        raise ValueError('textual scan/replacement mismatch')
    return new, len(encountered)


def audit():
    saved = json.loads(PROPOSAL.read_text())
    current = propose.proposal()
    if saved != current:
        raise ValueError('C3c proposal or source locks differ')
    mapping = {row['old_id']: row['proposed_id'] for row in saved['mappings']}
    if len(mapping) != len(saved['mappings']):
        raise ValueError('cross-kind old ID collision')
    pattern = token_pattern(mapping)
    original = propose.corpus('led')
    translated = copy.deepcopy(original)
    rows = []
    for entry in saved['textual_references_for_manual_review']:
        path, pointer, ids = entry['path'], entry['pointer'], entry['ids']
        old = at(original[path], pointer)
        if not isinstance(old, str) or sorted(set(pattern.findall(old))) != ids:
            raise ValueError(f'textual source drift: {path}{pointer}')
        filename, field = Path(path).name, pointer.split('/')[-1]
        held = (filename, field) == ('sources.json', 'evidence_extract')
        if held:
            category = 'held_source_extract'
            new, count = old, 0
        else:
            if (filename, field) == ('facts.json', 'locator'):
                category = ('source_prefixed_locator' if len(ids) == 1 and
                            old.startswith(ids[0] + ':') else 'other_locator')
            elif field in ('reason', 'conditions'):
                category = 'contextual_reason_or_condition'
            else:
                raise ValueError(f'unclassified textual location: {path}{pointer}')
            new, count = propose_text(old, ids, mapping, pattern)
            set_at(translated[path], pointer, new)
        rows.append({'path': path, 'pointer': pointer, 'category': category,
                     'old_ids': ids, 'old_sha256': sha(old),
                     'proposed_sha256': sha(new), 'replacement_count': count})
    remaining = propose.textual_references(translated, set(mapping))
    expected_held = [entry for entry, row in zip(saved['textual_references_for_manual_review'], rows)
                     if row['category'] == 'held_source_extract']
    if remaining != expected_held:
        raise ValueError('translated corpus has unexpected old textual IDs')
    counts = {category: sum(row['category'] == category for row in rows)
              for category in sorted(set(row['category'] for row in rows))}
    return {
        'schema': 'pd-led-c3h-textual-reference-disposition/1',
        'base_commit': 'b0b08d6ab4b3bf5054919286e2c1c41bfcef0779',
        'proposal_source_set_sha256': saved['source_set_sha256'],
        'locations': len(rows), 'categories': counts,
        'proposed_rewrite_locations': len(rows) - len(expected_held),
        'proposed_exact_token_replacements': sum(row['replacement_count'] for row in rows),
        'held_source_extract_locations': len(expected_held),
        'remaining_old_id_locations_in_memory': len(remaining),
        'rows': rows,
        'status': 'in-memory textual ID proposal only; original source and historical extracts unchanged',
        'holds': ['Every proposed prose/locator edit requires exact-head review before adoption.',
                  'Four source evidence extracts remain verbatim historical text.',
                  'Identity/SMAJ, DNP, private resources, #307, CAD, publication and physical holds remain.'],
    }


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
