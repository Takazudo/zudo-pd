#!/usr/bin/env python3
"""D1 -12 V adv without the rshunt step (adv-rshunt-free-criteria.md).

Runs the identity pair's executed adv deck at rshunt=1e10, once at pinned settings and once under the comparable
abstol step, and reports each against the same dispatch's identity adv (rshunt=1e9). Measures only: no ceiling is
judged, and the recorded D1 failure stays.

usage (after extract_reference.py prepare / run / identity):
  adv_rshunt_free.py prepare WORK --manifest PATH
  for LABEL in $(adv_rshunt_free.py labels): run_ladder.py WORK/r10/LABEL/tracking $(adv_rshunt_free.py pending WORK LABEL) --original-only
  adv_rshunt_free.py analyze WORK --output PATH
"""

import argparse
import json
from pathlib import Path
import shutil
import sys

from extract_reference import derive_decks
import gap_sensitivity as gap
import osc_bank as ob
import variant_cross_check as vx

CRITERIA = 'adv-rshunt-free-criteria.md'
NAME = 'adv'
RSHUNT_FREE = ('rshunt=1e9', 'rshunt=1e10')
ABSTOL = dict(ob.VARIANTS)['abstol']
RECORDED = {'peak_slope_in_region_v_per_ms': 1.474778000, 'peak_current_in_region_a': 0.265259332}


def swap(text, old, new, what):
    if text.count(old) != 1:
        raise ValueError(f'{what}: expected exactly one {old}')
    return text.replace(old, new)


def derive_cases():
    """label -> (setting, deck text)."""
    executed = derive_decks()[NAME]['executed']
    r10 = swap(executed, *RSHUNT_FREE, 'r10-adv')
    return {'r10-adv': ('pinned settings at rshunt=1e10', r10),
            'abstol-r10-adv': ('matched variant abstol at rshunt=1e10 (labelled, not pinned)',
                               swap(r10, *ABSTOL, 'abstol-r10-adv'))}


def tree(work, lbl):
    return Path(work) / 'r10' / lbl


def write(work, lbl, text):
    root = tree(work, lbl)
    (root / 'tracking').mkdir(parents=True, exist_ok=True)
    if not (root / 'lib').exists():
        shutil.copytree(Path(work) / 'lib', root / 'lib')
        shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
    (root / 'tracking' / f'{NAME}.cir').write_text(text)
    return gap.sha(text.encode())


def prepare(work):
    return {'criteria': CRITERIA,
            'labels': {lbl: {NAME: {'setting': setting, 'deck_sha256': write(work, lbl, text)}}
                       for lbl, (setting, text) in derive_cases().items()}}


def status(work, lbl):
    return gap.case_status(tree(work, lbl), NAME)


def pending(work, lbl):
    derive_cases()[lbl]
    return [NAME] if status(work, lbl)['status'] == 'NOT RUN' else []


def check_run(work, lbl):
    state = status(work, lbl)['status']
    return {} if state in ('COMPLETE', 'ABORTED') else {NAME: state}


def row(work, lbl, setting, baseline):
    state = status(work, lbl)
    out = {'setting': setting, 'status': state['status']}
    if state['status'] == 'ABORTED':
        out['abort'] = state.get('abort')
    if state['status'] != 'COMPLETE':
        return out
    rails = vx.metrics(state, NAME)
    out['rails'] = rails
    out['minus12_d1'] = {key: {'value': rails['-12'][key], 'recorded_failure': rec,
                               'relative_to_recorded': (rails['-12'][key] - rec) / rec}
                         for key, rec in RECORDED.items()}
    if baseline is not None:
        out['difference_from_identity_adv_rshunt_1e9'] = vx.compare(baseline, rails)
    return out


def analyze(work):
    identity = vx.pinned_status(work, NAME)
    baseline = vx.metrics(identity, NAME) if identity['status'] == 'COMPLETE' else None
    rows = {lbl: row(work, lbl, setting, baseline) for lbl, (setting, _) in derive_cases().items()}
    return {'diagnostic': 'D1 -12 V adv without the rshunt step (adv-rshunt-free-criteria.md); '
                          'measures only, judges no ceiling, the recorded failure stands',
            'identity_adv': identity['status'], 'decks': rows,
            'status': {lbl: r['status'] for lbl, r in rows.items()}}


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
        print(' '.join(derive_cases()))
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
        print(json.dumps(out['status'], indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
