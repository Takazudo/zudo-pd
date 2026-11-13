#!/usr/bin/env python3
"""D1 pinned-versus-variant cross-check (variant-cross-check-criteria.md).

Reruns the identity pair's executed nom / adv decks under each matched-variant step that applies, and compares each
with the same dispatch's pinned identity run. Measures and reads solver-setting comparability only: no candidate,
no ceiling, no verdict on the circuit.

usage (after extract_reference.py prepare / run / identity):
  variant_cross_check.py prepare WORK --manifest PATH
  for LABEL in $(variant_cross_check.py labels): run_ladder.py WORK/xcheck/LABEL/tracking $(variant_cross_check.py pending WORK LABEL) --original-only
  variant_cross_check.py analyze WORK --output PATH
"""

import argparse
import json
from pathlib import Path
import shutil
import sys

from extract_reference import CASES, derive_decks
import gap_sensitivity as gap
import osc_bank as ob

CRITERIA = 'variant-cross-check-criteria.md'
READ_RAILS = ('+5', '-12')
READ_KEYS = ('peak_slope_in_region_v_per_ms', 'peak_current_in_region_a')
READ_BOUND = 1e-4   # 0.01 % of the pinned value: ten times below the smallest recorded D1 exceedance (0.10 %)


def label(variant, name):
    return f'{variant}-{name}'


def derive_cases():
    """label -> (deck name, variant, deck text) for every variant step that applies; plus the inapplicable ones."""
    executed = {name: deck['executed'] for name, deck in derive_decks().items()}
    out, skipped = {}, {}
    for variant, _ in ob.VARIANTS:
        for name in CASES:
            text = ob.apply_variant(executed[name], variant)
            if text is None:
                skipped[label(variant, name)] = f'{name} has no single {dict(ob.VARIANTS)[variant][0]} option'
            else:
                out[label(variant, name)] = (name, variant, text)
    return out, skipped


def tree(work, lbl):
    return Path(work) / 'xcheck' / lbl


def write(work, lbl, name, text):
    root = tree(work, lbl)
    (root / 'tracking').mkdir(parents=True, exist_ok=True)
    if not (root / 'lib').exists():
        shutil.copytree(Path(work) / 'lib', root / 'lib')
        shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
    (root / 'tracking' / f'{name}.cir').write_text(text)
    return gap.sha(text.encode())


def prepare(work):
    cases, skipped = derive_cases()
    manifest = {'criteria': CRITERIA, 'labels': {}, 'not_applicable': skipped}
    for lbl, (name, variant, text) in cases.items():
        manifest['labels'][lbl] = {name: {'variant': variant, 'deck_sha256': write(work, lbl, name, text)}}
    return manifest


def pinned_status(work, name):
    """The identity run of this dispatch: WORK/ladder-* holds the pinned nom / adv."""
    return gap.case_status(work, name)


def variant_status(work, lbl, name):
    return gap.case_status(tree(work, lbl), name)


def pending(work, lbl):
    name = derive_cases()[0][lbl][0]
    return [name] if variant_status(work, lbl, name)['status'] == 'NOT RUN' else []


def check_run(work, lbl):
    name = derive_cases()[0][lbl][0]
    state = variant_status(work, lbl, name)['status']
    return {} if state in ('COMPLETE', 'ABORTED') else {name: state}


def metrics(source, name):
    record = gap.case_record(source['run'], name)
    return {rail: ob.rail_metrics(record, rail) for rail in ob.RAIL_ROWS}


def compare(pinned, varied):
    """variant - pinned for every float quantity, and its size relative to the pinned value."""
    out = {}
    for rail, values in pinned.items():
        out[rail] = {}
        for key, value in values.items():
            other = varied[rail].get(key)
            if isinstance(value, float) and isinstance(other, float):
                diff = other - value
                out[rail][key] = {'pinned': value, 'variant': other, 'difference': diff,
                                  'relative': abs(diff) / abs(value) if value else None}
    return out


def reading(diff):
    """COMPARABLE or NOT COMPARABLE under the pre-registered rule; lists every read quantity."""
    checked = []
    for rail in READ_RAILS:
        for key in READ_KEYS:
            row = diff.get(rail, {}).get(key)
            relative = None if row is None else row['relative']
            checked.append({'rail': rail, 'quantity': key, 'relative': relative,
                            'within': relative is not None and relative <= READ_BOUND})
    return ('COMPARABLE' if all(c['within'] for c in checked) else 'NOT COMPARABLE'), checked


def pair(work, lbl, name, variant):
    pinned, varied = pinned_status(work, name), variant_status(work, lbl, name)
    row = {'deck': name, 'variant': variant, 'pinned': pinned['status'], 'variant_status': varied['status']}
    for side, state in (('pinned', pinned), ('variant', varied)):
        if state['status'] == 'ABORTED':
            row[f'{side}_abort'] = state.get('abort')
    if pinned['status'] != 'COMPLETE' or varied['status'] != 'COMPLETE':
        row['reading'] = 'NOT FORMED'
        return row
    row['difference'] = compare(metrics(pinned, name), metrics(varied, name))
    row['reading'], row['read'] = reading(row['difference'])
    return row


def analyze(work):
    cases, skipped = derive_cases()
    pairs = {lbl: pair(work, lbl, name, variant) for lbl, (name, variant, _) in cases.items()}
    return {'diagnostic': 'D1 pinned-versus-variant cross-check (variant-cross-check-criteria.md); '
                          'reads solver-setting comparability only, judges no circuit margin',
            'read_rails': list(READ_RAILS), 'read_quantities': list(READ_KEYS), 'read_bound_relative': READ_BOUND,
            'pairs': pairs, 'not_applicable': skipped,
            'readings': {lbl: row['reading'] for lbl, row in pairs.items()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('work')
    p.add_argument('--manifest', required=True)
    sub.add_parser('labels')
    for cmd in ('pending', 'check-run'):
        p = sub.add_parser(cmd)
        p.add_argument('work')
        p.add_argument('label')
    p = sub.add_parser('analyze')
    p.add_argument('work')
    p.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    if args.command == 'labels':
        print(' '.join(derive_cases()[0]))
    elif args.command == 'prepare':
        Path(args.manifest).write_text(json.dumps(prepare(args.work), indent=2) + '\n')
    elif args.command == 'pending':
        print(' '.join(pending(args.work, args.label)))
    elif args.command == 'check-run':
        bad = check_run(args.work, args.label)
        if bad:
            print(json.dumps(bad), file=sys.stderr)
            return 1
    elif args.command == 'analyze':
        out = analyze(args.work)
        Path(args.output).write_text(json.dumps(out, indent=2, default=str) + '\n')
        print(json.dumps(out['readings'], indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
