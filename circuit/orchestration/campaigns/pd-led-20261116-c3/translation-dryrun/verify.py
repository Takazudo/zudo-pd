#!/usr/bin/env python3
"""Verify C3c translation against an in-memory LED mirror; write no source files."""

import ast
import copy
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'translation'))
import propose  # noqa: E402

PROPOSAL_PATH = HERE.parent / 'translation/proposal.json'


def value_at(document, pointer):
    node = document
    for token in pointer.lstrip('/').split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def set_at(document, pointer, value):
    parts = pointer.lstrip('/').split('/')
    node = document
    for token in parts[:-1]:
        token = token.replace('~1', '/').replace('~0', '~')
        node = node[int(token)] if isinstance(node, list) else node[token]
    token = parts[-1].replace('~1', '/').replace('~0', '~')
    node[int(token) if isinstance(node, list) else token] = value


def changed_leaves(before, after, parts=()):
    if type(before) is not type(after):
        return {propose.pointer(parts)}
    if isinstance(before, dict):
        if before.keys() != after.keys():
            return {propose.pointer(parts)}
        return set().union(*(changed_leaves(before[key], after[key], (*parts, key))
                             for key in before))
    if isinstance(before, list):
        if len(before) != len(after):
            return {propose.pointer(parts)}
        return set().union(*(changed_leaves(left, right, (*parts, index))
                             for index, (left, right) in enumerate(zip(before, after))))
    return {propose.pointer(parts)} if before != after else set()


def verify():
    proposal = json.loads(PROPOSAL_PATH.read_text())
    if proposal != propose.proposal():
        raise ValueError('proposal no longer matches its source locks')
    original = propose.corpus('led')
    translated = copy.deepcopy(original)
    allowed = {path: set() for path in translated}
    for ref in proposal['reference_translation']:
        path, pointer = ref['path'], ref['pointer']
        if value_at(translated[path], pointer) != ref['id']:
            raise ValueError(f'structured reference drift: {path}{pointer}')
        if not ref['proposed_id']:
            raise ValueError(f'no translation: {path}{pointer}')
        set_at(translated[path], pointer, ref['proposed_id'])
        allowed[path].add(pointer)
    for row in proposal['arithmetic_expression_review']:
        path, pointer = row['path'], row['pointer'] + '/expression'
        if value_at(translated[path], pointer) != row['original_expression']:
            raise ValueError(f'expression drift: {path}{pointer}')
        expression = row['proposed_expression_for_review']
        names = {node.id for node in ast.walk(ast.parse(expression, mode='eval'))
                 if isinstance(node, ast.Name)}
        expected = {binding['proposed_symbol'] for binding in row['dependency_bindings']}
        if names != expected or row['unmatched_expression_symbols'] or row['unused_dependency_symbols']:
            raise ValueError(f'dependency/expression mismatch: {path}{pointer}')
        set_at(translated[path], pointer, expression)
        allowed[path].add(pointer)
    unexpected = []
    for path in original:
        changed = changed_leaves(original[path], translated[path])
        if changed != allowed[path]:
            unexpected.append({'path': path, 'unexpected': sorted(changed - allowed[path]),
                               'unchanged': sorted(allowed[path] - changed)})
    if unexpected:
        raise ValueError(f'unexpected or missing changes: {unexpected[:3]}')
    led_defs = propose.definitions(translated, 'led')
    pd_defs = propose.definitions(propose.corpus('pd'), 'pd')
    for kind in led_defs:
        if set(led_defs[kind]) & set(pd_defs[kind]):
            raise ValueError(f'PD collision after translation: {kind}')
    refs, unresolved = propose.references(translated, led_defs)
    if unresolved or len(refs) != len(proposal['reference_translation']):
        raise ValueError(f'translated reference closure failed: {len(unresolved)} unresolved')
    return {
        'schema': 'pd-led-c3d-translation-dryrun/1',
        'proposal_source_set_sha256': proposal['source_set_sha256'],
        'changed_structured_references': len(proposal['reference_translation']),
        'changed_expressions': len(proposal['arithmetic_expression_review']),
        'structured_by_kind': dict(sorted(Counter(ref['kind'] for ref in proposal['reference_translation']).items())),
        'translated_definitions': sum(map(len, led_defs.values())),
        'unresolved_translated_references': len(unresolved),
        'unexpected_changed_leaves': len(unexpected),
        'textual_locations_still_held': len(proposal['textual_references_for_manual_review']),
        'status': 'in-memory feasibility only; no canonical adoption or validator sign-off',
    }


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2) + '\n', end='')
