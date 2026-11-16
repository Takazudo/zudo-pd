#!/usr/bin/env python3
"""Build a source-locked, non-adopting LED evidence ID translation proposal."""

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PD = Path('.claude/skills')
LED = Path('products/led-lamp/.claude/skills')
KINDS = {
    'record': ('manifest.json', 'records', 'record_id'),
    'source': ('sources.json', 'sources', 'source_id'),
    'fact': ('facts.json', 'facts', 'fact_id'),
    'coverage': ('coverage.json', 'coverage', 'coverage_id'),
    'interaction': ('interactions.json', 'interactions', 'interaction_id'),
    'routing': ('routing.json', 'routes', 'route_id'),
    'pin_map': ('pin-map.json', 'pin_maps', 'pin_map_id'),
}
REF_KEYS = {
    'record_id': 'record', 'record_ids': 'record', 'recordId': 'record', 'recordIds': 'record',
    'parent_record_id': 'record',
    'line_id': 'line', 'line_ids': 'line',
    'source_id': 'source', 'source_ids': 'source', 'sourceId': 'source', 'sourceIds': 'source',
    'fact_id': 'fact', 'fact_ids': 'fact', 'blocking_fact_ids': 'fact', 'depends_on': 'fact',
    'coverage_id': 'coverage', 'coverage_ids': 'coverage',
    'interaction_id': 'interaction', 'interaction_ids': 'interaction',
    'route_id': 'routing', 'route_ids': 'routing',
    'pin_map_id': 'pin_map', 'pin_map_ids': 'pin_map',
    'rule_id': 'rule', 'rule_ids': 'rule',
}
EXTRA = {
    'line': [Path('component-spec-audit/references/inventory.json'), 'lines', 'line_id'],
    'rule': [Path('circuit-spec-integration/references/rules.json'), 'rules', 'rule_id'],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def pointer(parts):
    return '/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def corpus(side):
    base = LED if side == 'led' else PD
    paths = []
    for folder in sorted((ROOT / base).glob('component-*')):
        if not (folder / 'manifest.json').is_file():
            continue
        for filename, _, _ in KINDS.values():
            file = folder / filename
            if file.is_file():
                paths.append(file.relative_to(ROOT))
    for relative, _, _ in EXTRA.values():
        paths.append(base / relative)
    paths.append(Path('products/led-lamp/circuit/publication/selection.json') if side == 'led'
                 else Path('circuit/publication/selection.json'))
    if side == 'led':
        paths.append(LED / 'circuit-spec-integration/references/forward-tests.json')
        paths.append(LED / 'circuit-spec-integration/references/observed-runs.json')
    return {str(path): json.loads((ROOT / path).read_bytes()) for path in sorted(set(paths))}


def definitions(files, side):
    found = {kind: {} for kind in [*KINDS, *EXTRA]}
    for path, doc in files.items():
        name = Path(path).name
        specs = [(kind, array, key) for kind, (filename, array, key) in KINDS.items()
                 if name == filename and '/component-' in path]
        specs += [(kind, array, key) for kind, (relative, array, key) in EXTRA.items()
                  if path.endswith(str(relative))]
        for kind, array, key in specs:
            for index, item in enumerate(doc[array]):
                identifier = item[key]
                if identifier in found[kind]:
                    raise ValueError(f'duplicate {side} {kind} ID {identifier}: {path}')
                found[kind][identifier] = {
                    'path': path, 'pointer': pointer([array, index, key]),
                    'payload_sha256': digest(canonical(item)),
                    'source_sha256': digest((ROOT / path).read_bytes()),
                }
    return found


def references(files, definitions_by_kind, mapping=None):
    refs, unresolved = [], []
    def key_kind(key):
        if key in REF_KEYS:
            return REF_KEYS[key]
        compact = key.replace('_', '').lower()
        for prefix, kind in [('record', 'record'), ('line', 'line'), ('source', 'source'),
                             ('fact', 'fact'), ('coverage', 'coverage'),
                             ('interaction', 'interaction'), ('route', 'routing'),
                             ('pinmap', 'pin_map'), ('rule', 'rule')]:
            if compact.endswith(prefix + 'ids') or compact.endswith(prefix + 'id'):
                return kind
        return None
    def walk(value, path, parts):
        if isinstance(value, dict):
            for key, child in value.items():
                kind = key_kind(key)
                if kind and child is not None:
                    values = child if isinstance(child, list) else [child]
                    for offset, identifier in enumerate(values):
                        if not isinstance(identifier, str):
                            raise ValueError(f'non-string reference: {path}{pointer(parts+[key])}')
                        loc = pointer(parts + [key] + ([offset] if isinstance(child, list) else []))
                        # A definition also refers to its own ID; it is accounted for here.
                        entry = {'path': path, 'pointer': loc, 'kind': kind, 'id': identifier}
                        if mapping is not None:
                            entry['proposed_id'] = mapping.get(kind, {}).get(identifier)
                        if identifier in definitions_by_kind[kind]:
                            refs.append(entry)
                        else:
                            unresolved.append(entry)
                walk(child, path, parts + [key])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path, parts + [index])
    for path, doc in files.items():
        walk(doc, path, [])
    return refs, unresolved


def proposal():
    pd_files, led_files = corpus('pd'), corpus('led')
    pd_defs, led_defs = definitions(pd_files, 'pd'), definitions(led_files, 'led')
    mapping = {}
    rows = []
    for kind in sorted(led_defs):
        mapping[kind] = {}
        for old, evidence in sorted(led_defs[kind].items()):
            # Every LED identity stays separate, including equal-byte collisions.
            proposed = f'led-{old}-{evidence["payload_sha256"][:12]}-{evidence["source_sha256"][:8]}'
            mapping[kind][old] = proposed
            rows.append({'kind': kind, 'old_id': old, 'proposed_id': proposed,
                         'pd_collision': old in pd_defs[kind], **evidence})
    proposed_ids = [row['proposed_id'] for row in rows]
    pd_ids = {identifier for group in pd_defs.values() for identifier in group}
    if len(set(proposed_ids)) != len(proposed_ids) or set(proposed_ids) & pd_ids:
        raise ValueError('proposed ID collision')
    led_refs, unresolved = references(led_files, led_defs, mapping)
    pd_refs, pd_unresolved = references(pd_files, pd_defs)
    if pd_unresolved:
        raise ValueError(f'baseline PD has {len(pd_unresolved)} unresolved structured references')
    # Keep prose/locator references visible for manual migration. Replacing them
    # blindly can alter quoted source evidence, so they are not auto-translated.
    old_ids = {old: new for group in mapping.values() for old, new in group.items()}
    pattern = re.compile(r'(?<![A-Za-z0-9_-])(' + '|'.join(re.escape(x) for x in sorted(old_ids, key=len, reverse=True)) + r')(?![A-Za-z0-9_-])')
    textual = []
    def scan_text(value, path, parts):
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, str) and key not in REF_KEYS and not key.endswith('_id'):
                    matches = sorted(set(pattern.findall(child)))
                    if matches:
                        textual.append({'path': path, 'pointer': pointer(parts + [key]),
                                        'ids': matches})
                elif isinstance(child, (dict, list)):
                    scan_text(child, path, parts + [key])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                scan_text(child, path, parts + [index])
    for path, doc in led_files.items():
        scan_text(doc, path, [])
    locks = {path: digest((ROOT / path).read_bytes()) for path in sorted(led_files | pd_files)}
    return {
        'schema': 'pd-led-c3c-evidence-translation/1',
        'policy': 'proposal only; preserve PD IDs and all original LED payloads; no equivalence or adoption',
        'base_commit': 'c5e45fb0392a8040d6ba304d2be4125ef911e707',
        'source_locks_sha256': locks,
        'source_set_sha256': digest(canonical(locks)),
        'counts': {'pd_definitions': sum(map(len, pd_defs.values())),
                   'led_definitions': len(rows), 'led_structured_references': len(led_refs),
                   'pd_structured_references': len(pd_refs), 'unresolved_led_references': len(unresolved),
                   'textual_reference_locations': len(textual),
                   'shared_original_ids_by_kind': {kind: len(set(led_defs[kind]) & set(pd_defs[kind]))
                                                   for kind in sorted(led_defs)}},
        'mappings': rows,
        'reference_translation': led_refs,
        'unresolved_references': unresolved,
        'textual_references_for_manual_review': textual,
        'holds': ['No ID equality implies matching identity, payload, verdict, conditions or source authority.',
                  'SMAJ footprint and CAD pin equivalence require separate native review.',
                  'LED line DNP flags require placement-level review; #307 remains independent.',
                  'Historical LED evidence, raw resources, private vendor material and publication stay held.'],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='compare committed proposal with fresh output')
    args = parser.parse_args()
    path = Path(__file__).with_name('proposal.json')
    output = json.dumps(proposal(), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if path.read_text() != output:
            raise SystemExit('proposal drift')
        print('proposal matches source-locked regeneration')
    else:
        path.write_text(output)
        print(path)


if __name__ == '__main__':
    main()
