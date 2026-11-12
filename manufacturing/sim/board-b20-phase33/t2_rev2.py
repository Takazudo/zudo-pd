"""D1 T2 rev 2 on -12 V: a sourced low-capacitance clamp diode plus delayed connection, under the revised rules.

Attempt 1 (t2_clamp.py, d1-t2-criteria.md) is unchanged and stays FAILED. Rev 2 differs from it only by:
- DT2K and DT2C use a datasheet-traced .model (DIODE below), with the guaranteed reverse leakage as an explicit
  element, instead of the deck's DBODY placeholder (CJO 20 pF);
- option 1: the clamp connects to TRK12N_FB only 11.9 ms after each enable and is parked at GND while disabled,
  so the capture step and disabled-state leakage never reach the summing node (d1-t2-rev2-paper-check-20261112.md);
- rules 6 and 9 as revised (rules_revision.py, d1-rules-revision-20261112.md);
- a separately labelled matched-variant track for cases that ABORT under the pinned settings.

Nothing here is a design change. prepare refuses to run until DIODE names a sourced owner bundle.

usage (after extract_reference.py prepare / run / identity):
  t2_rev2.py prepare WORK --manifest PATH
  for every LABEL in t2_clamp.LABEL_ORDER: run_ladder.py WORK/t2/LABEL/tracking $(t2_rev2.py pending WORK LABEL) --original-only
  t2_rev2.py analyze WORK --output PATH
  for STEP in 1 2: for every 'LABEL NAMES' line of t2_rev2.py variant-plan WORK STEP: run_ladder.py ... --original-only
  t2_rev2.py variant-analyze WORK --output PATH
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

from extract_reference import derive_decks, single_run
import gap_sensitivity as gap
import rules_revision as rules
import t2_clamp as t1

CRITERIA = 'd1-t2-rev2-criteria.md'
SCOPE = 'T2 rev 2 (sourced clamp diode, delayed connection) on -12 V under the revised rules; model only, not adopted'

# ---------------------------------------------------------------- the clamp diode (filled from the owner bundle)
# Every value must trace to a row of the retained primary datasheet in the owner bundle named by 'owner'.
# Worst case: CJO is the guaranteed maximum Cd at the stated VR with M = 0; leakage is the guaranteed maximum IR.
DIODE = None   # {'owner': '.claude/skills/component-.../', 'mpn': ..., 'model': {'IS':..,'N':..,'RS':..,'CJO':..,
               #  'VJ':..,'M':0,'BV':..,'IBV':..}, 'ir_max_a': .., 'ir_condition': '..', 'rows': {param: 'datasheet row'}}
MODEL_PARAMETERS = ('IS', 'N', 'RS', 'CJO', 'VJ', 'M', 'BV', 'IBV')
LEAK_KNEE_V = 0.05             # leakage reaches its guaranteed maximum within 0.05 V of reverse bias (conservative)

# ---------------------------------------------------------------- option 1: delayed connection with GND parking
DELAY = {'R': ('100k', '+/-1 %'), 'C': ('47n', 'C0G, +/-5 %')}   # tau 4.7 ms from EN_N
CONNECT_BELOW_V = 0.4          # 4.7 ms * ln(5 / 0.4) = 11.9 ms after enable
PARK_ABOVE_V = 0.6             # 0.6 ms after disable; break-before-make between 0.4 and 0.6 V
CONNECT_GATE = f'{t1.CLAMP_GATE}*0.5*(1-tanh((v(t2d)-{CONNECT_BELOW_V})*30))'
PARK_GATE = f'0.5*(1+tanh((v(t2d)-{PARK_ABOVE_V})*30))'


def require_diode():
    if DIODE is None:
        raise ValueError('rev 2 clamp diode not sourced: no owner bundle, so no deck can be prepared')
    missing = [p for p in MODEL_PARAMETERS if p not in DIODE['model'] or p not in DIODE['rows']]
    if missing or 'ir_max_a' not in DIODE or 'ir_max_a' not in DIODE['rows']:
        raise ValueError(f'rev 2 clamp diode: untraced parameters {missing or ["ir_max_a"]}')
    return DIODE


def model_line():
    d = require_diode()
    return ('.model DT2X D(' + ' '.join(f'{p}={d["model"][p]:g}' for p in MODEL_PARAMETERS) + ')'
            + f'  ; {d["mpn"]}, {d["owner"]}')


def leak(name, cathode, anode):
    """The guaranteed maximum reverse leakage, flowing cathode to anode whenever the junction is reverse-biased."""
    return f'{name} {cathode} {anode} I={DIODE["ir_max_a"]:g}*tanh(max(v({cathode},{anode}),0)/{LEAK_KNEE_V})'


def t2_block(inert=False):
    """Attempt 1's block with the sourced diode, its leakage and the delayed, parked connection."""
    require_diode()
    sink = '0' if inert else 'trk12n_fb'
    out = []
    for line in t1.t2_block(inert):
        if line.startswith(('DT2K ', 'DT2C ')):
            line = line.replace(' DBODY', ' DT2X')
        if line.startswith('BT2G '):
            line = t1.switch('BT2G', 't2g', sink, CONNECT_GATE)
        out.append(line)
    out[0] = out[0].replace('candidate under evaluation', 'rev 2 candidate under evaluation').replace(
        'd1-t2-criteria.md', CRITERIA)
    return out + [model_line(), leak('BT2KL', 't2k', 'm12_drv'), leak('BT2CL', 't2o', 't2c'),
                  f"RT2D enn t2d {DELAY['R'][0]}", f"CT2D t2d 0 {DELAY['C'][0]}",
                  t1.switch('BT2D', 't2g', '0', PARK_GATE)]


def prepare(work):
    return t1.prepare(work, block=t2_block, scope=SCOPE, criteria=CRITERIA)


def analyze(work):
    out = t1.analyze(work, judge=rules.judge, scope=SCOPE, criteria=CRITERIA)
    out['rules'] = 'rules 1-9 as revised (d1-rules-revision-20261112.md); 10-14 and L1-L4 unchanged'
    return out


# ---------------------------------------------------------------- matched-variant track (labelled, never PASS/FAIL)
VARIANTS = (('abstol', ('abstol=1e-9', 'abstol=1e-8')), ('rshunt', ('rshunt=1e10', 'rshunt=1e9')))
VARIANT_VERDICT = 'VARIANT-EVALUATED'
CROSS_CHECK = ('t2', 'adv')    # a case that completes pinned, rerun under each variant used
# case -> its comparison baseline; 'run' is the pinned identity pair, 'base' the loaded baselines
BASELINE = {**{(lbl, n): b for (lbl, n), b in t1.NO_LOAD_T2.items()},
            **{(lbl, 'nom'): ('run', 'nom') for lbl in t1.CORNER_CASES},
            **{('t2load', n): ('base', n) for n in t1.LOADED}}


def apply_variant(text, variant):
    old, new = dict(VARIANTS)[variant]
    return text.replace(old, new) if text.count(old) == 1 else None


def pinned_decks():
    executed = {k: v['executed'] for k, v in derive_decks().items()}
    decks = {('run', 'nom'): executed['nom'], ('run', 'adv'): executed['adv']}
    for label, names in t1.derive_cases(t2_block).items():
        decks.update({(label, n): text for n, text in names.items()})
    return decks


def pinned_status(work, label, name):
    if label == 'run':
        return {'status': 'COMPLETE', 'run': single_run(work)}
    return t1.status(work, label, name)


def vlabel(variant, label):
    return f'v-{variant}-{label}'


def unit(case):
    """A case and its baseline chain down to a pinned reference ('run' or 'base'); they run together."""
    chain = [case]
    while chain[-1] in BASELINE:
        chain.append(BASELINE[chain[-1]])
    return chain


def aborted_pinned(work):
    return [case for case in BASELINE if pinned_status(work, *case)['status'] == 'ABORTED']


def resolved(work, case, step):
    """The variant step at which both the case and its baseline completed, or None."""
    for k, (variant, _) in enumerate(VARIANTS[:step], 1):
        if all(t1.status(work, vlabel(variant, lbl), n)['status'] == 'COMPLETE' for lbl, n in unit(case)):
            return k
    return None


def variant_plan(work, step):
    """Prepare step STEP's decks; return {variant label: [deck names]}. Only pinned ABORTED cases enter."""
    work = Path(work)
    variant = VARIANTS[step - 1][0]
    pending = [c for c in aborted_pinned(work) if resolved(work, c, step - 1) is None]
    if not pending:
        return {}
    decks = pinned_decks()
    wanted = {m for c in pending for m in unit(c)} | set(unit(CROSS_CHECK))
    plan = {}
    for label, name in sorted(wanted):
        text = apply_variant(decks[(label, name)], variant)
        if text is None:
            continue           # this variant's option is not in the deck as pinned; the step does not apply
        root = work / 't2' / vlabel(variant, label)
        (root / 'tracking').mkdir(parents=True, exist_ok=True)
        if not (root / 'lib').exists():
            shutil.copytree(work / 'lib', root / 'lib')
            shutil.copyfile(work / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        (root / 'tracking' / f'{name}.cir').write_text(text)
        plan.setdefault(vlabel(variant, label), []).append(name)
    return plan


def reference_match(work, variant, label, name):
    """The variant baseline against its pinned record, over the whole run, within the L2 tolerance."""
    pinned, varied = pinned_status(work, label, name), t1.status(work, vlabel(variant, label), name)
    if pinned['status'] != 'COMPLETE' or varied['status'] != 'COMPLETE':
        return {'matches': False, 'reason': f'pinned {pinned["status"]}, variant {varied["status"]}'}
    a, b = t1.plain_record(pinned['run'], name), t1.plain_record(varied['run'], name)
    diff = t1.tracking_difference(a, b, 0.0, min(a['times'][-1], b['times'][-1]) - gap.BIN_S)
    return {'matches': all(d['within_tolerance'] for d in diff.values()), 'differences': diff}


def variant_case(work, case, step):
    label, name = case
    variant = VARIANTS[step - 1][0]
    row = {'variant': variant, 'verdict': VARIANT_VERDICT}
    base = BASELINE[case]
    row['reference_match'] = reference_match(work, variant, *unit(case)[-1])
    if not row['reference_match']['matches']:
        return {**row, 'verdict': 'NOT EVALUATED', 'reason': 'variant baseline does not match the pinned record'}
    run = t1.status(work, vlabel(variant, label), name)['run']
    brun = t1.status(work, vlabel(variant, base[0]), base[1])['run']
    try:
        if label in t1.CORNER_CASES:
            rail = t1.CORNER_CASES[label][0]
            m = gap.rail_metrics(gap.case_record(run, name), rail)
            row['corner'] = {k: m.get(k) for k in ('enable_vgs_max_v', 'enable_min_distance_to_conduction_v',
                                                    'enable_peak_current_a', 'enable_edge_extremes_v')}
            row['conduction'] = m['enable_conduction']
        elif label == 't2load':
            row['note'] = 'loaded rules L1-L4 against the matched variant baseline'
            row['rules'] = loaded_rules(t1.plain_record(brun, name), t1.case_record(run, name, t2=True, loaded=True),
                                        name)
        else:
            base_rec, rec = gap.case_record(brun, name), t1.case_record(run, name, t2=True)
            bs, vs = gap.screens(base_rec), gap.screens(rec)
            b, v = gap.rail_metrics(base_rec, '-12'), gap.rail_metrics(rec, '-12')
            judged = rules.judge('-12', vs, bs, v, b, rec)
            row['rules'] = {f'{k + 1} {r}': ok for k, (r, ok) in enumerate(judged.items())}
            row['rules'].update(t1.t2_rules(t1.t2_metrics(rec)))
            row['rule_detail'] = rules.detail('-12', v, b, rec)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        return {**row, 'verdict': 'NOT EVALUATED', 'reason': f'{type(error).__name__}: {error}'}
    return row


def loaded_rules(base, record, name):
    out = {}
    for k, (start, stop) in enumerate(t1.LOADED_WINDOWS[name]):
        tag = 'startup' if k == 0 else 're-enable'
        bs, vs = t1.loaded_screens(base, start, stop), t1.loaded_screens(record, start, stop)
        out[f'L1 {tag}'] = all(gap.screen_passes(vs[r]) or not gap.screen_passes(bs[r]) for r in vs)
        diff = t1.tracking_difference(base, record, start, stop)
        out[f'L2 {tag}'] = all(d['within_tolerance'] for d in diff.values())
        out[f'L3 {tag}'] = t1.peak_current(record, start, stop) <= t1.peak_current(base, start, stop) * (1 + t1.RELTOL)
    return out


def variant_analyze(work):
    work = Path(work)
    out = {'track': 'matched-variant (labelled; never PASS or FAIL in the pre-registered sense)',
           'ladder': [v for v, _ in VARIANTS], 'cases': {}, 'cross_check': {}}
    for case in aborted_pinned(work):
        step = resolved(work, case, len(VARIANTS))
        out['cases']['/'.join(case)] = (variant_case(work, case, step) if step else
                                        {'verdict': 'NOT EVALUATED', 'reason': 'ABORTED through the whole ladder'})
    for variant, _ in VARIANTS:
        if all(t1.status(work, vlabel(variant, lbl), n)['status'] == 'COMPLETE' for lbl, n in unit(CROSS_CHECK)):
            out['cross_check'][variant] = variant_case(work, CROSS_CHECK, [v for v, _ in VARIANTS].index(variant) + 1)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('work', type=Path); p.add_argument('--manifest', type=Path, required=True)
    for cmd in ('analyze', 'variant-analyze'):
        a = sub.add_parser(cmd); a.add_argument('work', type=Path); a.add_argument('--output', type=Path, required=True)
    n = sub.add_parser('pending'); n.add_argument('work', type=Path); n.add_argument('label', choices=t1.LABEL_ORDER)
    c = sub.add_parser('check-run'); c.add_argument('work', type=Path); c.add_argument('label')
    v = sub.add_parser('variant-plan'); v.add_argument('work', type=Path); v.add_argument('step', type=int, choices=(1, 2))
    args = parser.parse_args(argv)
    if args.command == 'pending':
        print(' '.join(t1.pending(args.work, args.label)))
        return 0
    if args.command == 'check-run' and args.label in t1.LABEL_ORDER:
        bad = t1.check_run(args.work, args.label)
        for name, state in bad.items():
            print(f'{args.label} {name}: {state}; not a solver abort, failing the step', file=sys.stderr)
        return 1 if bad else 0
    if args.command == 'check-run':
        bad = {n: s for n, s in ((n, t1.status(args.work, args.label, n)['status'])
                                 for n in sorted(p.stem for p in (args.work / 't2' / args.label / 'tracking').glob('*.cir')))
               if s not in ('COMPLETE', 'ABORTED')}
        for name, state in bad.items():
            print(f'{args.label} {name}: {state}; not a solver abort, failing the step', file=sys.stderr)
        return 1 if bad else 0
    if args.command == 'variant-plan':
        for label, names in variant_plan(args.work, args.step).items():
            print(label, ' '.join(names))
        return 0
    if args.command == 'prepare':
        args.manifest.write_text(json.dumps(prepare(args.work), indent=2) + '\n')
        return 0
    result = analyze(args.work) if args.command == 'analyze' else variant_analyze(args.work)
    text = json.dumps(result, indent=2, default=str) + '\n'
    args.output.write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
