#!/usr/bin/env python3
"""Source-bound in-memory feasibility audit for nine LED integration calculations."""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'translation'))
import propose  # noqa: E402
sys.path.insert(0, str(ROOT / 'node_modules/@takazudo/zudo-circuit-doc/python'))
from circuit_evidence.facts import expression_names  # noqa: E402
from circuit_evidence.integration.rules import validate_calculation  # noqa: E402

PROPOSAL = HERE.parent / 'translation/proposal.json'
LED_RULES = 'products/led-lamp/.claude/skills/circuit-spec-integration/references/rules.json'
PD_RULES = '.claude/skills/circuit-spec-integration/references/rules.json'
SLUG_PATTERN = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def locked_json(path, locks):
    bytes_ = (ROOT / path).read_bytes()
    if sha256(bytes_) != locks[path]:
        raise ValueError(f'locked input changed: {path}')
    return json.loads(bytes_)


def replace_symbols(expression, bindings):
    return re.sub(r'[A-Za-z_][A-Za-z_0-9]*',
                  lambda match: bindings.get(match.group(), match.group()), expression)


def audit():
    proposal = json.loads(PROPOSAL.read_text())
    if proposal != propose.proposal():
        raise ValueError('C3c proposal differs from its source-locked regeneration')
    locks = proposal['source_locks_sha256']
    led_rules = locked_json(LED_RULES, locks)['rules']
    pd_rules = locked_json(PD_RULES, locks)['rules']
    fact_map = {row['old_id']: row['proposed_id'] for row in proposal['mappings']
                if row['kind'] == 'fact'}
    rule_map = {row['old_id']: row['proposed_id'] for row in proposal['mappings']
                if row['kind'] == 'rule'}
    facts = {}
    fact_paths = {row['path'] for row in proposal['mappings'] if row['kind'] == 'fact'}
    for path in sorted(fact_paths):
        for fact in locked_json(path, locks)['facts']:
            if fact['fact_id'] in facts:
                raise ValueError(f'duplicate LED fact: {fact["fact_id"]}')
            facts[fact['fact_id']] = fact
    translated_facts = {fact_map[old]: {**copy.deepcopy(fact), 'fact_id': fact_map[old]}
                        for old, fact in facts.items()}
    pd_ids = {calc['calculation_id'] for rule in pd_rules
              for calc in rule.get('conditioned_calculations', [])}
    rows = []
    old_ids, proposed_ids = set(), set()
    rules_sha = locks[LED_RULES]
    for rule in led_rules:
        proposed_rule = {'fact_ids': [fact_map[fact_id] for fact_id in rule['fact_ids']]}
        for calc in rule.get('conditioned_calculations', []):
            old_id = calc['calculation_id']
            if old_id in old_ids:
                raise ValueError(f'duplicate LED calculation ID: {old_id}')
            old_ids.add(old_id)
            proposed_id = f'led-{old_id}-{sha256(propose.canonical(calc))[:12]}-{rules_sha[:8]}'
            if proposed_id in proposed_ids or proposed_id in pd_ids or not SLUG_PATTERN.fullmatch(proposed_id):
                raise ValueError(f'proposed calculation ID collision or invalid anchor: {proposed_id}')
            proposed_ids.add(proposed_id)
            bindings = {old.replace('-', '_'): fact_map[old].replace('-', '_')
                        for old in calc['fact_ids']}
            old_names = expression_names(calc['expression'])
            old_fact_names = {name for name in old_names if name.startswith('fact_')}
            if not old_fact_names <= set(bindings):
                raise ValueError(f'old expression/fact mismatch: {old_id}')
            translated = copy.deepcopy(calc)
            translated['calculation_id'] = proposed_id
            translated['fact_ids'] = [fact_map[fact_id] for fact_id in calc['fact_ids']]
            translated['expression'] = replace_symbols(calc['expression'], bindings)
            new_names = expression_names(translated['expression'])
            used_new_fact_names = {bindings[name] for name in old_fact_names}
            if {name for name in new_names if name.startswith('led_fact_')} != used_new_fact_names:
                raise ValueError(f'translated expression/fact mismatch: {old_id}')
            scenario_names = sorted(old_names - old_fact_names)
            if sorted(new_names - used_new_fact_names) != scenario_names:
                raise ValueError(f'scenario variable drift: {old_id}')
            validate_calculation(translated, proposed_rule, translated_facts)
            allowed_changes = {'calculation_id', 'fact_ids', 'expression'}
            if {key for key in calc if calc[key] != translated[key]} != allowed_changes:
                raise ValueError(f'unexpected or missing calculation change: {old_id}')
            rows.append({
                'rule_id': rule['rule_id'], 'proposed_rule_id': rule_map[rule['rule_id']],
                'old_calculation_id': old_id, 'proposed_calculation_id': proposed_id,
                'payload_sha256': sha256(propose.canonical(calc)),
                'rules_file_sha256': rules_sha,
                'old_fact_ids': calc['fact_ids'], 'proposed_fact_ids': translated['fact_ids'],
                'old_expression': calc['expression'], 'proposed_expression_for_review': translated['expression'],
                'scenario_variables_preserved': scenario_names,
                'scenario_count': len(calc.get('results', [])) or 1,
                'focused_validator_result': 'PASS',
            })
    if len(rows) != 9:
        raise ValueError(f'expected nine LED calculations, found {len(rows)}')
    package = ROOT / 'node_modules/@takazudo/zudo-circuit-doc'
    package_version = json.loads((package / 'package.json').read_text())['version']
    if package_version != '0.3.0':
        raise ValueError(f'unexpected installed package version: {package_version}')
    tool_paths = [
        ROOT / 'pnpm-lock.yaml', ROOT / 'patches/@takazudo__zudo-circuit-doc@0.3.0.patch',
        package / 'python/circuit_evidence/facts.py',
        package / 'python/circuit_evidence/integration/rules.py',
        package / 'lib/core/ids.js',
    ]
    return {
        'schema': 'pd-led-c3f-calculation-feasibility/1',
        'base_commit': '4962df857d995ed8de5e363507a0c67ba378e08f',
        'installed_package_version': package_version,
        'tool_sha256': {str(path.relative_to(ROOT)): sha256(path.read_bytes()) for path in tool_paths},
        'proposal_source_set_sha256': proposal['source_set_sha256'],
        'led_rules_sha256': rules_sha,
        'pd_rules_sha256': locks[PD_RULES],
        'led_fact_files_verified': len(fact_paths),
        'calculation_count': len(rows),
        'current_pd_calculation_id_collisions': len(old_ids & pd_ids),
        'proposed_pd_calculation_id_collisions': len(proposed_ids & pd_ids),
        'focused_validator_passes': len(rows),
        'calculation_rows': rows,
        'holds': [
            'In-memory focused validate_calculation only; no merged-corpus validator or generated pages ran.',
            'Proposed calculation IDs and expressions are not canonical adoption or identity approval.',
            'All textual, identity/CAD/SMAJ, DNP, publication, private-resource, #307 and physical holds remain.',
        ],
    }


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, ensure_ascii=False))
