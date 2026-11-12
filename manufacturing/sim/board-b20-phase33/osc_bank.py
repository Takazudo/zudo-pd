#!/usr/bin/env python3
"""OSC-bank baseline diagnostic (osc-bank-criteria.md): the unmodified baseline at the OSC module's fitted bank.

Measures, never judges: each rail's peak adjacent-sample slope inside and above its no-load exception voltage region,
the peak OSC capacitor (ESR-branch) current, and the charge into the bank inside that region, with the OSC bank at its fitted value and at +/-20 %.
No candidate, no ceiling, no verdict. Pinned decks run first; a pinned ABORTED deck enters the labelled
matched-variant ladder (abstol, then rshunt) only.

usage (after extract_reference.py prepare / run / identity):
  osc_bank.py prepare WORK --manifest PATH
  for LABEL in $(osc_bank.py labels): run_ladder.py WORK/bank/LABEL/tracking $(osc_bank.py pending WORK LABEL) --original-only
  osc_bank.py variant-plan WORK STEP     (STEP 1 abstol, 2 rshunt; prints "label names" lines and writes the decks)
  osc_bank.py analyze WORK --output PATH
"""

import argparse
import json
from pathlib import Path
import shutil
import sys

from extract_reference import derive_decks
import gap_sensitivity as gap
import t2_clamp as t1

HERE = Path(__file__).resolve().parent
CRITERIA = 'osc-bank-criteria.md'
# OSC owner-reported fitted capacitance, all MLCC (zudo-osc-hole-field power-contract README L262/L273 Q6, read
# 2026-11-12 at 05b1498); the decks otherwise use the 180 / 120 / 180 uF contract ceiling.
FITTED_UF = {'+12': 49.9, '+5': 24.5, '-12': 42.2}
SCALES = {'lo': 0.8, 'nom': 1.0, 'hi': 1.2}     # the contract's 20 % capacitance tolerance, applied both ways
BANK_LINES = {'+12': ('CL12 p12_out cl12 180u', 'CL12 p12_out cl12 {}u'),
              '+5': ('CL5 p5_out cl5 120u', 'CL5 p5_out cl5 {}u'),
              '-12': ('CLN 0 cln 180u', 'CLN 0 cln {}u')}
CASES = ('nom', 'adv', 'e12lo', 'e12hi', 'e5lo', 'e5hi')
VARIANTS = (('abstol', ('abstol=1e-9', 'abstol=1e-8')), ('rshunt', ('rshunt=1e10', 'rshunt=1e9')))
# rail -> (row index after time, sign, exception voltage region in V); +12 has no exception, so 0.75 V is used only
# to split its report the same way as -12.
RAIL_ROWS = {'+12': (1, 1, 0.75), '+5': (2, 1, 0.45), '-12': (3, -1, 0.75)}


def bank_value(rail, scale):
    return round(FITTED_UF[rail] * SCALES[scale], 4)


def with_bank(text, scale, what):
    for rail, (old, new) in BANK_LINES.items():
        text = t1.replace_once(text, old, new.format(f'{bank_value(rail, scale):g}'), what)
    return text


def base_deck(case):
    """The case's pinned deck at the contract ceiling bank: nom / adv as executed, corners as in T2 rev 2."""
    executed = {k: v['executed'] for k, v in derive_decks().items()}
    if case in ('nom', 'adv'):
        return case, t1.no_load(executed[case], case)
    rail, which = t1.CORNER_CASES[case]
    return 'nom', t1.no_load(t1.corner(executed['nom'], rail, which, case), 'nom')


def label(scale, case):
    return f'{scale}-{case}'


def derive_cases():
    """label -> (deck name, deck text). One deck per label, so every deck keeps its own name and outputs."""
    out = {}
    for scale in SCALES:
        for case in CASES:
            name, text = base_deck(case)
            out[label(scale, case)] = (name, with_bank(text, scale, label(scale, case)))
    return out


def tree(work, lbl):
    return Path(work) / 'bank' / lbl


def write(work, lbl, name, text):
    root = tree(work, lbl)
    (root / 'tracking').mkdir(parents=True, exist_ok=True)
    if not (root / 'lib').exists():
        shutil.copytree(Path(work) / 'lib', root / 'lib')
        shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
    (root / 'tracking' / f'{name}.cir').write_text(text)
    return gap.sha(text.encode())


def prepare(work):
    manifest = {'criteria': CRITERIA, 'fitted_uF': FITTED_UF, 'scales': SCALES, 'labels': {}}
    for lbl, (name, text) in derive_cases().items():
        manifest['labels'][lbl] = {name: {'deck_sha256': write(work, lbl, name, text)}}
    return manifest


def status(work, lbl, name):
    return gap.case_status(tree(work, lbl), name)


def pending(work, lbl):
    name = derive_cases()[lbl][0]
    return [name] if status(work, lbl, name)['status'] == 'NOT RUN' else []


def check_run(work, lbl):
    name = (derive_cases().get(lbl) or derive_cases()[lbl.split('-', 2)[2]])[0]
    state = status(work, lbl, name)['status']
    return {} if state in ('COMPLETE', 'ABORTED') else {name: state}


def vlabel(variant, lbl):
    return f'v-{variant}-{lbl}'


def apply_variant(text, variant):
    old, new = dict(VARIANTS)[variant]
    return text.replace(old, new) if text.count(old) == 1 else None


def resolved(work, lbl, name, step):
    """True once the label completed pinned or under any earlier variant step."""
    if status(work, lbl, name)['status'] == 'COMPLETE':
        return True
    return any(status(work, vlabel(v, lbl), name)['status'] == 'COMPLETE' for v, _ in VARIANTS[:step])


def variant_plan(work, step):
    """Write step STEP's decks for pinned ABORTED labels not yet resolved; return {variant label: name}."""
    variant = VARIANTS[step - 1][0]
    plan = {}
    for lbl, (name, text) in derive_cases().items():
        if status(work, lbl, name)['status'] != 'ABORTED' or resolved(work, lbl, name, step - 1):
            continue
        varied = apply_variant(text, variant)
        if varied is None:
            continue
        write(work, vlabel(variant, lbl), name, varied)
        plan[vlabel(variant, lbl)] = name
    return plan


def region_charge(times, current, inside):
    """Charge into the bank while the output is inside the exception voltage region (trapezoid, both ends inside)."""
    return sum((times[k + 1] - times[k]) * (current[k] + current[k + 1]) / 2
               for k in range(len(times) - 1) if inside[k] and inside[k + 1])


def half_width(times, current, peak_index):
    """Width of the contiguous span around the peak where the current stays at or above half the peak."""
    floor = 0.5 * current[peak_index]
    lo = hi = peak_index
    while lo > 0 and current[lo - 1] >= floor:
        lo -= 1
    while hi < len(current) - 1 and current[hi + 1] >= floor:
        hi += 1
    return times[hi] - times[lo]


def rail_metrics(record, rail):
    index, sign, region = RAIL_ROWS[rail]
    rows, side = record['rows'], record['side']
    start, stop = gap.SCREEN_WINDOW_S
    keep = [k for k, r in enumerate(rows) if start <= r[0] < stop]
    on = [rows[k] for k in keep]
    if rail == '-12':
        cur = [(side[k][3] - rows[k][3]) / .05 for k in keep]
    else:
        cur = [side[k][index] / .05 for k in keep]
    inside, above = [], []
    for a, b in zip(on, on[1:]):
        slope = abs(b[index] - a[index]) / (b[0] - a[0]) / 1000
        (inside if max(sign * a[index], sign * b[index]) <= region else above).append((slope, a[0], sign * a[index]))
    times = [r[0] for r in on]
    in_region = [k for k, r in enumerate(on) if 0 <= sign * r[index] <= region]
    peak_k = max(in_region, key=lambda k: cur[k]) if in_region else None
    out = {'region_v': region,
           'peak_slope_in_region_v_per_ms': max(inside)[0] if inside else None,
           'peak_slope_in_region_at_ms': max(inside)[1] * 1e3 if inside else None,
           'peak_slope_above_region_v_per_ms': max(above)[0] if above else None,
           'peak_slope_above_region_at_ms': max(above)[1] * 1e3 if above else None,
           'peak_current_in_region_a': cur[peak_k] if peak_k is not None else None,
           'peak_current_in_region_at_ms': times[peak_k] * 1e3 if peak_k is not None else None,
           'peak_current_a': max(cur)}
    inside_flags = [0 <= sign * r[index] <= region for r in on]
    out['charge_in_region_c'] = region_charge(times, cur, inside_flags)
    if peak_k is not None and cur[peak_k] > 0:
        out['current_half_width_ms'] = half_width(times, cur, peak_k) * 1e3
    return out


def deck_row(work, lbl, name):
    pinned = status(work, lbl, name)
    row = {'pinned': pinned['status']}
    if pinned['status'] == 'ABORTED':
        row['abort'] = pinned.get('abort')
    source = pinned if pinned['status'] == 'COMPLETE' else None
    for variant, _ in VARIANTS:
        if source is not None:
            break
        varied = status(work, vlabel(variant, lbl), name)
        if varied['status'] != 'NOT RUN':
            row[f'variant_{variant}'] = varied['status']
        if varied['status'] == 'COMPLETE':
            source, row['measured_under'] = varied, f'matched variant {variant} (labelled, not pinned)'
    if source is None:
        row['measured_under'] = None
        return row
    row.setdefault('measured_under', 'pinned')
    record = gap.case_record(source['run'], name)
    row['rails'] = {rail: rail_metrics(record, rail) for rail in RAIL_ROWS}
    return row


def analyze(work):
    rows = {lbl: deck_row(work, lbl, name) for lbl, (name, _) in derive_cases().items()}
    worst = {}
    for rail in RAIL_ROWS:
        for key in ('peak_slope_in_region_v_per_ms', 'peak_slope_above_region_v_per_ms', 'peak_current_in_region_a',
                    'peak_current_a', 'charge_in_region_c'):
            vals = [(r['rails'][rail].get(key), lbl) for lbl, r in rows.items() if r.get('rails')
                    and r['rails'][rail].get(key) is not None]
            if vals:
                worst.setdefault(rail, {})[key] = dict(zip(('value', 'deck'), max(vals)))
    return {'diagnostic': 'OSC-bank baseline (osc-bank-criteria.md); measures only, judges nothing',
            'fitted_uF': FITTED_UF, 'scales': SCALES,
            'bank_uF': {s: {r: bank_value(r, s) for r in FITTED_UF} for s in SCALES},
            'decks': rows, 'worst_measured': worst,
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
        print(json.dumps({'worst_measured': out['worst_measured'], 'unknown': out['unknown']}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
