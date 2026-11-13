#!/usr/bin/env python3
"""Ceiling-bank corners diagnostic (ceiling-corners-criteria.md): e5lo / e5hi and a uniform-temperature hot case.

The unmodified no-load baseline at the contract ceiling bank (180 / 120 / 180 uF), measured with osc_bank's per-rail
quantities. Measures, never judges: no candidate, no ceiling, no verdict.
- e5lo / e5hi (and e12hi as the in-run anchor) aborted pinned in run 43187732133, so they enter the labelled
  matched-variant ladder directly (abstol, then rshunt).
- hot-<case> is the pinned deck plus one `.temp` line; every solver option stays pinned. An abort enters the same ladder.
- Each hot row is compared with its cold anchor measured under the same solver setting.

usage (after extract_reference.py prepare / run / identity):
  ceiling_corners.py prepare WORK --manifest PATH
  for LABEL in $(ceiling_corners.py labels): run_ladder.py WORK/ceiling/LABEL/tracking $(ceiling_corners.py pending WORK LABEL) --original-only
  ceiling_corners.py variant-plan WORK STEP     (STEP 1 abstol, 2 rshunt; prints "label names" lines and writes the decks)
  ceiling_corners.py analyze WORK --output PATH
"""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import gap_sensitivity as gap
import osc_bank as ob
import t2_rev2

CRITERIA = 'ceiling-corners-criteria.md'
HOT_T_C = t2_rev2.HOT_T_C
RECORDED_PINNED_ABORT_RUN = 43187732133
PINNED = ('nom', 'adv')
VARIANT_ONLY = ('e5lo', 'e5hi', 'e12hi')
HOT = ('nom', 'adv', 'e12hi', 'e5hi')
CROSS_CHECK = 'nom'
FLAG_A = {'-12': 0.300, '+5': 0.140}     # owner: flag an in-region current that would eat most of the 350 / 160 mA margin
TEMPERATURE_TERMS = ('tnom', 'temp', 'tc1', 'tc2', 'xti', 'kt1', 'kt2', 'ute', 'eg', 'tcv', 'trs')


def hot_label(case):
    return f'hot-{case}'


def anchor(lbl):
    return lbl[len('hot-'):] if lbl.startswith('hot-') else None


def with_temperature(text, what):
    if HOT_T_C is None:
        raise ValueError('hot case: the hot-case temperature is not recorded (HOT_T_C)')
    if re.search(r'^\.temp\b', text, re.M | re.I) or text.count('\n.options ') != 1:
        raise ValueError(f'{what}: expected one .options line and no .temp line')
    return text.replace('\n.options ', f'\n.temp {HOT_T_C:g}\n.options ', 1)


def derive_cases():
    """label -> (deck name, deck text, entry); entry 'pinned' runs pinned first, 'variant' enters the ladder directly."""
    out = {}
    for case in PINNED + VARIANT_ONLY:
        name, text = ob.base_deck(case)
        out[case] = (name, text, 'pinned' if case in PINNED else 'variant')
    for case in HOT:
        name, text = ob.base_deck(case)
        out[hot_label(case)] = (name, with_temperature(text, hot_label(case)), 'pinned')
    return out


def tree(work, lbl):
    return Path(work) / 'ceiling' / lbl


def write(work, lbl, name, text):
    root = tree(work, lbl)
    (root / 'tracking').mkdir(parents=True, exist_ok=True)
    if not (root / 'lib').exists():
        shutil.copytree(Path(work) / 'lib', root / 'lib')
        shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
    (root / 'tracking' / f'{name}.cir').write_text(text)
    return gap.sha(text.encode())


def prepare(work):
    manifest = {'criteria': CRITERIA, 'hot_t_c': HOT_T_C, 'labels': {}}
    for lbl, (name, text, entry) in derive_cases().items():
        if entry == 'pinned':
            manifest['labels'][lbl] = {name: {'deck_sha256': write(work, lbl, name, text)}}
        else:
            manifest['labels'][lbl] = {name: {'deck_sha256': gap.sha(text.encode()), 'entry': 'variant ladder'}}
    return manifest


def status(work, lbl, name):
    return gap.case_status(tree(work, lbl), name)


def pending(work, lbl):
    name, _, entry = derive_cases()[lbl]
    return [name] if entry == 'pinned' and status(work, lbl, name)['status'] == 'NOT RUN' else []


def check_run(work, lbl):
    base = lbl.split('-', 2)[2] if lbl.startswith('v-') else lbl
    name = derive_cases()[base][0]
    state = status(work, lbl, name)['status']
    return {} if state in ('COMPLETE', 'ABORTED') else {name: state}


def setting(work, lbl, name):
    """(solver setting, status) the label is measured under: pinned if COMPLETE, else the first COMPLETE variant."""
    pinned = status(work, lbl, name)
    if pinned['status'] == 'COMPLETE':
        return 'pinned', pinned
    for variant, _ in ob.VARIANTS:
        varied = status(work, ob.vlabel(variant, lbl), name)
        if varied['status'] == 'COMPLETE':
            return variant, varied
    return None, None


def needs_variant(work, lbl, name, entry, step):
    if entry == 'pinned' and status(work, lbl, name)['status'] != 'ABORTED':
        return False
    return all(status(work, ob.vlabel(v, lbl), name)['status'] != 'COMPLETE' for v, _ in ob.VARIANTS[:step - 1])


def variant_plan(work, step):
    """Write step STEP's decks; return {variant label: name}. Adds the cold anchor of every hot row in the plan, and
    the pinned-COMPLETE cross-check deck, under the same variant."""
    variant = ob.VARIANTS[step - 1][0]
    cases = derive_cases()
    chosen = [lbl for lbl, (name, _, entry) in cases.items() if needs_variant(work, lbl, name, entry, step)]
    chosen = [lbl for lbl in chosen if ob.apply_variant(cases[lbl][1], variant) is not None]
    chosen += [anchor(lbl) for lbl in list(chosen) if anchor(lbl) and anchor(lbl) not in chosen]
    if chosen and CROSS_CHECK not in chosen and status(work, CROSS_CHECK, cases[CROSS_CHECK][0])['status'] == 'COMPLETE':
        chosen.append(CROSS_CHECK)
    plan = {}
    for lbl in chosen:
        name, text, _ = cases[lbl]
        write(work, ob.vlabel(variant, lbl), name, ob.apply_variant(text, variant))
        plan[ob.vlabel(variant, lbl)] = name
    return plan


def metrics(source, name):
    record = gap.case_record(source['run'], name)
    return {rail: ob.rail_metrics(record, rail) for rail in ob.RAIL_ROWS}


def deck_row(work, lbl, name, entry):
    row = {'entry': entry}
    if entry == 'pinned':
        pinned = status(work, lbl, name)
        row['pinned'] = pinned['status']
        if pinned['status'] == 'ABORTED':
            row['abort'] = pinned.get('abort')
    else:
        row['pinned'] = f'not rerun; ABORTED in recorded run {RECORDED_PINNED_ABORT_RUN}'
    for variant, _ in ob.VARIANTS:
        varied = status(work, ob.vlabel(variant, lbl), name)
        if varied['status'] != 'NOT RUN':
            row[f'variant_{variant}'] = varied['status']
    used, source = setting(work, lbl, name)
    row['measured_under'] = None if used is None else (
        'pinned' if used == 'pinned' else f'matched variant {used} (labelled, not pinned)')
    if source is not None:
        row['rails'] = metrics(source, name)
    return row


def difference(a, b):
    return {rail: {k: b[rail][k] - v for k, v in a[rail].items() if isinstance(v, float)
                   and isinstance(b[rail].get(k), float)} for rail in a}


def hot_minus_cold(work):
    out = {}
    cases = derive_cases()
    for case in HOT:
        lbl, name = hot_label(case), cases[hot_label(case)][0]
        used, hot = setting(work, lbl, name)
        if used is None:
            out[lbl] = {'comparable': False, 'why': 'hot row has no completed run'}
            continue
        cold = status(work, case if used == 'pinned' else ob.vlabel(used, case), name)
        if cold['status'] != 'COMPLETE':
            out[lbl] = {'comparable': False, 'setting': used, 'why': f'cold anchor {cold["status"]} under {used}'}
            continue
        out[lbl] = {'comparable': True, 'setting': used, 'hot_minus_cold': difference(metrics(cold, name), metrics(hot, name))}
    return out


def cross_check(work):
    name = derive_cases()[CROSS_CHECK][0]
    pinned = status(work, CROSS_CHECK, name)
    out = {}
    for variant, _ in ob.VARIANTS:
        varied = status(work, ob.vlabel(variant, CROSS_CHECK), name)
        if varied['status'] == 'NOT RUN':
            continue
        row = {'pinned': pinned['status'], 'variant': varied['status']}
        if pinned['status'] == varied['status'] == 'COMPLETE':
            row['difference'] = difference(metrics(pinned, name), metrics(varied, name))
        out[variant] = row
    return out


def temperature_terms(work):
    """Counts of temperature keywords per model file: whether a .temp line can reach each model. Counts only, no bytes."""
    out = {}
    for path in sorted((Path(work) / 'lib').glob('*.lib')):
        text = path.read_text(errors='replace').lower()
        out[path.name] = {term: len(re.findall(rf'\b{term}\b', text)) for term in TEMPERATURE_TERMS}
    return out


def flags(rows):
    out = []
    for lbl, row in rows.items():
        for rail, limit in FLAG_A.items():
            value = (row.get('rails') or {}).get(rail, {}).get('peak_current_in_region_a')
            if value is not None and value > limit:
                out.append({'label': lbl, 'rail': rail, 'peak_current_in_region_a': value, 'flag_above_a': limit,
                            'measured_under': row['measured_under']})
    return out


def analyze(work):
    rows = {lbl: deck_row(work, lbl, name, entry) for lbl, (name, _, entry) in derive_cases().items()}
    largest = {}
    for rail in ob.RAIL_ROWS:
        for key in ('peak_slope_in_region_v_per_ms', 'peak_slope_above_region_v_per_ms', 'peak_current_in_region_a',
                    'peak_current_a', 'charge_in_region_c'):
            vals = [(r['rails'][rail][key], lbl) for lbl, r in rows.items()
                    if r.get('rails') and r['rails'][rail].get(key) is not None]
            if vals:
                largest.setdefault(rail, {})[key] = dict(zip(('value', 'deck'), max(vals)))
    return {'diagnostic': 'ceiling-bank corners (ceiling-corners-criteria.md); measures only, judges nothing',
            'bank_uF': {'+12': 180, '+5': 120, '-12': 180}, 'hot_t_c': HOT_T_C,
            'decks': rows, 'largest_measured': largest, 'flags': flags(rows), 'hot_minus_cold': hot_minus_cold(work),
            'variant_cross_check': cross_check(work), 'model_temperature_terms': temperature_terms(work),
            'unknown': sorted(lbl for lbl, r in rows.items() if r['measured_under'] is None)}


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
    p = sub.add_parser('variant-plan')
    p.add_argument('work')
    p.add_argument('step', type=int, choices=(1, 2))
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
    elif args.command == 'variant-plan':
        for lbl, name in variant_plan(args.work, args.step).items():
            print(lbl, name)
    elif args.command == 'analyze':
        out = analyze(args.work)
        Path(args.output).write_text(json.dumps(out, indent=2, default=str) + '\n')
        print(json.dumps({'largest_measured': out['largest_measured'], 'flags': out['flags'],
                          'unknown': out['unknown']}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
