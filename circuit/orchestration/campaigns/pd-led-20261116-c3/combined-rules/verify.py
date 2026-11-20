#!/usr/bin/env python3
"""Validate combined PD and translated LED integration rules in memory only."""

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parent
for directory in ('translation', 'calculation-feasibility'):
    sys.path.insert(0, str(CAMPAIGN / directory))
import propose  # noqa: E402
import audit as calculation_audit  # noqa: E402
sys.path.insert(0, str(ROOT / 'node_modules/@takazudo/zudo-circuit-doc/python'))
from circuit_evidence.integration.rules import validate_rules  # noqa: E402

PROPOSAL_PATH = CAMPAIGN / 'translation/proposal.json'
CALC_RESULT_PATH = CAMPAIGN / 'calculation-feasibility/result.json'
PD_SCHEMA_PATH = ROOT / '.claude/skills/component-spec-audit/references/schema.json'
LED_SCHEMA_PATH = ROOT / 'products/led-lamp/.claude/skills/component-spec-audit/references/schema.json'
LED_RULE_PATH = 'products/led-lamp/.claude/skills/circuit-spec-integration/references/rules.json'


def value_at(document, pointer):
    node = document
    for token in pointer.lstrip('/').split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def set_at(document, pointer, value):
    tokens = pointer.lstrip('/').split('/')
    node = document
    for token in tokens[:-1]:
        token = token.replace('~1', '/').replace('~0', '~')
        node = node[int(token)] if isinstance(node, list) else node[token]
    tail = tokens[-1].replace('~1', '/').replace('~0', '~')
    node[int(tail) if isinstance(node, list) else tail] = value


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def checked_inputs():
    proposal = json.loads(PROPOSAL_PATH.read_text())
    if proposal != propose.proposal():
        raise ValueError('C3c proposal/source locks differ')
    calculations = json.loads(CALC_RESULT_PATH.read_text())
    if calculations != calculation_audit.audit():
        raise ValueError('C3f calculation result/source locks differ')
    if calculations['proposal_source_set_sha256'] != proposal['source_set_sha256']:
        raise ValueError('proposal/calculation source set mismatch')
    pd_schema_bytes, led_schema_bytes = PD_SCHEMA_PATH.read_bytes(), LED_SCHEMA_PATH.read_bytes()
    pd_schema, led_schema = json.loads(pd_schema_bytes), json.loads(led_schema_bytes)
    if pd_schema['verdicts'] != led_schema['verdicts']:
        raise ValueError('PD/LED verdict contracts differ')
    return proposal, calculations, pd_schema, {
        str(PD_SCHEMA_PATH.relative_to(ROOT)): sha256(pd_schema_bytes),
        str(LED_SCHEMA_PATH.relative_to(ROOT)): sha256(led_schema_bytes),
        'node_modules/@takazudo/zudo-circuit-doc/python/circuit_evidence/integration/rules.py':
            sha256((ROOT / 'node_modules/@takazudo/zudo-circuit-doc/python/circuit_evidence/integration/rules.py').read_bytes()),
    }


def translate_led(original, proposal, calculations):
    translated = copy.deepcopy(original)
    for ref in proposal['reference_translation']:
        path, pointer = ref['path'], ref['pointer']
        if value_at(translated[path], pointer) != ref['id']:
            raise ValueError(f'structured reference drift: {path}{pointer}')
        set_at(translated[path], pointer, ref['proposed_id'])
    for row in proposal['arithmetic_expression_review']:
        path, pointer = row['path'], row['pointer'] + '/expression'
        if value_at(translated[path], pointer) != row['original_expression']:
            raise ValueError(f'fact expression drift: {path}{pointer}')
        set_at(translated[path], pointer, row['proposed_expression_for_review'])
    calc_map = {row['old_calculation_id']: row for row in calculations['calculation_rows']}
    original_rules = original[LED_RULE_PATH]['rules']
    translated_rules = translated[LED_RULE_PATH]['rules']
    seen = set()
    for old_rule, new_rule in zip(original_rules, translated_rules):
        for old_calc, new_calc in zip(old_rule.get('conditioned_calculations', []),
                                      new_rule.get('conditioned_calculations', [])):
            row = calc_map[old_calc['calculation_id']]
            if row['rule_id'] != old_rule['rule_id'] or row['old_expression'] != old_calc['expression']:
                raise ValueError(f'calculation provenance drift: {old_calc["calculation_id"]}')
            new_calc['calculation_id'] = row['proposed_calculation_id']
            new_calc['expression'] = row['proposed_expression_for_review']
            seen.add(old_calc['calculation_id'])
    if seen != set(calc_map):
        raise ValueError('calculation proposal does not cover every LED calculation')
    return translated


def collect(files, section):
    filename, field = {'records': ('manifest.json', 'records'),
                       'facts': ('facts.json', 'facts'),
                       'sources': ('sources.json', 'sources')}[section]
    return [item for path, document in files.items()
            if path.endswith('/' + filename) and '/component-' in path
            for item in document[field]]


def combined_data():
    proposal, calculations, schema, tool_hashes = checked_inputs()
    pd_files, led_original = propose.corpus('pd'), propose.corpus('led')
    led = translate_led(led_original, proposal, calculations)
    aggregate = {section: collect(pd_files, section) + collect(led, section)
                 for section in ('records', 'facts', 'sources')}
    for section, key in [('records', 'record_id'), ('facts', 'fact_id'), ('sources', 'source_id')]:
        ids = [item[key] for item in aggregate[section]]
        if len(ids) != len(set(ids)):
            raise ValueError(f'combined {section} collision')
    pd_rule_path = '.claude/skills/circuit-spec-integration/references/rules.json'
    pd_count = len(pd_files[pd_rule_path]['rules'])
    rules = pd_files[pd_rule_path]['rules'] + led[LED_RULE_PATH]['rules']
    pd_candidates = {record['record_id'] for record in aggregate['records']
                     if record.get('candidate_id') is not None}
    candidate_facts = {fact['fact_id'] for fact in aggregate['facts']
                       if fact['record_id'] in pd_candidates}
    return aggregate, rules, schema, pd_candidates, candidate_facts, proposal, calculations, tool_hashes, pd_count


def verify():
    aggregate, rules, schema, candidates, candidate_facts, proposal, calculations, hashes, pd_count = combined_data()
    validate_rules(rules, aggregate, schema, candidate_record_ids=candidates,
                   candidate_fact_ids=candidate_facts)
    return {
        'schema': 'pd-led-c3g-combined-rules/1',
        'base_commit': 'd360b3954a43e01cad02b735a50161ddd18cde41',
        'proposal_source_set_sha256': proposal['source_set_sha256'],
        'tool_sha256': hashes,
        'pd_rules': pd_count, 'translated_led_rules': len(rules) - pd_count,
        'combined_rules_validated': len(rules),
        'combined_records': len(aggregate['records']),
        'combined_facts': len(aggregate['facts']),
        'combined_sources': len(aggregate['sources']),
        'translated_led_calculations': calculations['calculation_count'],
        'held_textual_locations': proposal['counts']['textual_reference_locations'],
        'status': 'in-memory generic integration-rule function PASS; no active merged corpus or generated site',
        'holds': [
            'No combined inventory, owner-root, CAD, publication or generated-page validator was run.',
            'Identity/SMAJ, DNP, textual, private-resource, #307 and physical decisions remain held.',
        ],
    }


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
