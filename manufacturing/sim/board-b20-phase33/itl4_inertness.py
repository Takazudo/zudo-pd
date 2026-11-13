#!/usr/bin/env python3
"""itl4 inertness diagnostic (itl4-inertness-criteria.md): a solver-setting test, never a verdict run.

Rebuilds the T2 rev 2 pinned decks and the nom/adv baseline exactly as recorded in run 43187732133, changes only
`itl4=200` to `itl4=1000`, runs each deck once and compares every output file with the recorded pinned hashes
(itl4-pinned-reference-20261112.json). No candidate is judged.

usage (after extract_reference.py prepare / run / identity and t2_rev2.py prepare):
  itl4_inertness.py prepare WORK --manifest PATH
  for LABEL in $(itl4_inertness.py labels): run_ladder.py WORK/itl4/LABEL/tracking $(itl4_inertness.py pending WORK LABEL) --original-only
  itl4_inertness.py analyze WORK --output PATH
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import gap_sensitivity as gap
from extract_reference import attempt_dir

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'itl4-pinned-reference-20261112.json'
PINNED = 'itl4=200'
RAISED = 'itl4=1000'
COMPARED_SUFFIXES = ('.dat', '-osc-cap.txt', '-ref.txt', '-servo.txt', '-gap.txt', '-t2.txt', '-a2.txt')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reference():
    return json.loads(REFERENCE.read_text())


def decks_by_label(ref=None):
    out = {}
    for key in (ref or reference())['decks']:
        label, name = key.split('/')
        out.setdefault(label, []).append(name)
    return out


def source_root(work, label):
    """Where the pinned deck was built: the baseline tree for 'run', the t2 tree otherwise."""
    return Path(work) if label == 'run' else Path(work) / 't2' / label


def raise_itl4(text):
    if text.count(PINNED) != 1:
        raise ValueError(f'expected exactly one {PINNED!r} in the deck, found {text.count(PINNED)}')
    return text.replace(PINNED, RAISED)


def prepare(work):
    """Copy each recorded pinned deck's tree and raise itl4; refuse unless the rebuilt deck matches the record."""
    work, ref = Path(work), reference()
    manifest = {'reference': REFERENCE.name, 'change': f'{PINNED} -> {RAISED} only', 'labels': {}}
    for label, names in decks_by_label(ref).items():
        src, root = source_root(work, label), work / 'itl4' / label
        (root / 'tracking').mkdir(parents=True)
        shutil.copytree(src / 'lib', root / 'lib')
        shutil.copyfile(src / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        manifest['labels'][label] = {}
        for name in names:
            text = (src / 'tracking' / f'{name}.cir').read_text()
            recorded = ref['decks'][f'{label}/{name}']['deck_sha256']
            if sha(text.encode()) != recorded:
                raise ValueError(f'{label}/{name}: rebuilt pinned deck differs from the recorded deck')
            raised = raise_itl4(text)
            if sha(raised.replace(RAISED, PINNED).encode()) != recorded:
                raise ValueError(f'{label}/{name}: the itl4 edit is not the only change')
            (root / 'tracking' / f'{name}.cir').write_text(raised)
            manifest['labels'][label][name] = {'pinned_deck_sha256': recorded, 'deck_sha256': sha(raised.encode())}
    return manifest


def pending(work, label):
    return [n for n in decks_by_label()[label]
            if gap.case_status(Path(work) / 'itl4' / label, n)['status'] == 'NOT RUN']


def check_run(work, label):
    """Workflow gate after a nonzero run_ladder: only solver aborts are tolerated."""
    bad = {}
    for name in decks_by_label()[label]:
        state = gap.case_status(Path(work) / 'itl4' / label, name)['status']
        if state not in ('COMPLETE', 'ABORTED'):
            bad[name] = state
    return bad


def outputs(run, name):
    folder = attempt_dir(run, name)
    return {f'{name}{s}': sha((folder / f'{name}{s}').read_bytes())
            for s in COMPARED_SUFFIXES if (folder / f'{name}{s}').is_file()}


def deck_row(work, label, name, recorded):
    state = gap.case_status(Path(work) / 'itl4' / label, name)
    row = {'pinned': recorded['status'], 'itl4': state['status']}
    if state['status'] == 'ABORTED':
        row['abort'] = state.get('abort')
    if recorded['status'] == 'COMPLETE':
        if state['status'] != 'COMPLETE':
            row['identical'] = False
            row['difference'] = f"completed pinned, {state['status']} with {RAISED}"
        else:
            got = outputs(state['run'], name)
            differing = sorted(k for k in set(got) | set(recorded['outputs'])
                               if got.get(k) != recorded['outputs'].get(k))
            row['identical'] = not differing
            if differing:
                row['difference'] = differing
    else:
        row['rescued'] = state['status'] == 'COMPLETE'
    return row


def analyze(work):
    ref = reference()
    rows = {key: deck_row(work, *key.split('/'), recorded) for key, recorded in ref['decks'].items()}
    run_failed = sorted(k for k, r in rows.items() if r['itl4'] not in ('COMPLETE', 'ABORTED'))
    completing = {k: r for k, r in rows.items() if r['pinned'] == 'COMPLETE'}
    aborting = {k: r for k, r in rows.items() if r['pinned'] == 'ABORTED'}
    if run_failed:
        verdict = 'NOT DETERMINED'
    else:
        verdict = 'INERT' if all(r['identical'] for r in completing.values()) else 'NOT INERT'
    return {
        'diagnostic': 'itl4 inertness (itl4-inertness-criteria.md); not a verdict run, judges no candidate',
        'change': f'{PINNED} -> {RAISED} only', 'reference': ref['source'],
        'verdict': verdict,
        'criterion': ('INERT only if every deck that completed pinned completes with every compared output file '
                      'byte-identical to the recorded pinned hash; any difference is NOT INERT and the option is '
                      'dropped; a deck that neither completes nor aborts leaves the result NOT DETERMINED'),
        'run_failed': run_failed,
        'completing_decks': completing,
        'aborting_decks': aborting,
        'rescued': sorted(k for k, r in aborting.items() if r['rescued']),
        'still_aborting': sorted(k for k, r in aborting.items() if r['itl4'] == 'ABORTED'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('work')
    p.add_argument('--manifest', required=True)
    sub.add_parser('labels')
    p = sub.add_parser('pending')
    p.add_argument('work')
    p.add_argument('label')
    p = sub.add_parser('check-run')
    p.add_argument('work')
    p.add_argument('label')
    p = sub.add_parser('analyze')
    p.add_argument('work')
    p.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    if args.command == 'labels':
        print(' '.join(decks_by_label()))
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
        print(json.dumps({k: out[k] for k in ('verdict', 'run_failed', 'rescued', 'still_aborting')}, indent=2))
        return 0 if out['verdict'] != 'NOT DETERMINED' else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
