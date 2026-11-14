"""D2 discrete -12 V sequencer (d2-sequencer-design.md) in the compact shutdown deck, at threshold and zener corners.

The behavioural BHOLD clamp of d2_sequenced.py is replaced by the drafted QR / QP / QH / QN / DZS network. The small
FETs and the zener are generic level-1 / diode models set to the corner values (PA where the datasheets give no bound);
they are not vendor models. Corners: H = VZ + VGS(th, QN) low (3.0 + 0.5 V) and high (4.1 + 1.5 V) x release
VGS(th, QR) 0.5 / 1.5 V.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import d2_fast_discharge as fd
import d2_sequenced as sq
import gap_sensitivity as gap

CRITERIA = 'd2-sequencer-circuit-criteria.md'
NAME = fd.NAME
# label -> (QN VTO, zener voltage at the switching current, QR VTO)
COMBOS = {'hlrl': (0.5, 3.0, 0.5), 'hlrh': (0.5, 3.0, 1.5), 'hhrl': (1.5, 4.1, 0.5), 'hhrh': (1.5, 4.1, 1.5)}


def network(vto_n, vz, vto_r):
    return f"""* discrete sequencer (d2-sequencer-design.md, PROPOSED); generic corner models, not vendor models
.model NSQN NMOS(LEVEL=1 VTO={vto_n} KP=0.1 LAMBDA=0.01)
.model NSQR NMOS(LEVEL=1 VTO={vto_r} KP=0.1 LAMBDA=0.01)
.model NSQH NMOS(LEVEL=1 VTO=1.5 KP=0.1 LAMBDA=0.01)
.model PSQP PMOS(LEVEL=1 VTO=-2.5 KP=0.1 LAMBDA=0.01)
.model DZSQ D(BV={vz} IBV=0.2m N=1 RS=10 IS=1e-14)
RSQG p12_out sqrg 10k
RSQGD sqrg 0 1meg
MQR sqen sqrg 0 0 NSQR
RSQ1 dis sqen 100k
MQP sqpd sqen dis dis PSQP
RSQ2 sqpd sqg 100k
RSQ3 sqg m12_out 100k
MQH dgn sqg m12_out m12_out NSQH
DZS sqz 0 DZSQ
RSQ4 sqz m12_out 4.7k
MQN sqg sqz m12_out m12_out NSQN
"""


def deck(label, caps, corner, combo):
    text = sq.deck(label, caps, corner)
    hold = next(line for line in text.splitlines(True) if line.startswith('BHOLD '))
    text = text.replace(hold, network(*COMBOS[combo]))
    return text.replace(f'* d2sq {label}: B20 sequenced -12 V discharge candidate ({sq.CRITERIA})',
                        f'* d2sc {combo}-{label}: B20 discrete -12 V sequencer ({CRITERIA})', 1)


def derive_cases():
    return {f'{c}-{b}-{l}': (c, b, corner, deck(f'{b}-{l}', caps, corner, c))
            for c in COMBOS for b, caps in fd.banks().items() for l, corner in sq.load_corners().items()}


def tree(work, lbl):
    return Path(work) / 'd2sc' / lbl


def prepare(work):
    manifest = {'criteria': CRITERIA, 'labels': {}}
    for lbl, (combo, bank_label, corner, text) in derive_cases().items():
        root = tree(work, lbl)
        (root / 'tracking').mkdir(parents=True, exist_ok=True)
        if not (root / 'lib').exists():
            shutil.copytree(Path(work) / 'lib', root / 'lib')
            shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        (root / 'tracking' / f'{NAME}.cir').write_text(text)
        manifest['labels'][lbl] = {'combo': combo, 'bank': bank_label, 'loads': corner,
                                   'deck_sha256': gap.sha(text.encode())}
    return manifest


def status(work, lbl):
    return gap.case_status(tree(work, lbl), NAME)


def analyze(work):
    out, states = {}, {}
    for lbl, (combo, bank_label, corner, _) in derive_cases().items():
        state = status(work, lbl)
        states[lbl] = state['status']
        row = {'combo': combo, 'bank': bank_label, 'loads': corner, 'status': state['status']}
        if state['status'] == 'COMPLETE':
            row.update(fd.read(fd.load(fd.attempt_dir(state['run'], NAME) / f'{NAME}.dat')))
        elif state['status'] == 'ABORTED':
            row['abort'] = state.get('abort')
        out[lbl] = row
    complete = [r for r in out.values() if r['status'] == 'COMPLETE']
    failing = sorted(k for k, r in out.items() if r['status'] == 'COMPLETE' and not r['pass'])
    verdict = 'FAIL (SIM)' if failing else ('PASS (SIM)' if len(complete) == len(out) else 'NOT FORMED')
    return {'criteria': CRITERIA, 'reading': verdict, 'decks': len(out), 'complete': len(complete),
            'not_complete': sorted(k for k, s in states.items() if s != 'COMPLETE'), 'failing': failing,
            'failing_by_combo': {c: sum(1 for k in failing if k.startswith(c + '-')) for c in COMBOS},
            'cases': out}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
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
        derive_cases()[args.label]
        print(NAME if status(args.work, args.label)['status'] == 'NOT RUN' else '')
    elif args.command == 'check-run':
        state = status(args.work, args.label)['status']
        if state not in ('COMPLETE', 'ABORTED'):
            print(json.dumps({NAME: state}), file=sys.stderr)
            return 1
    elif args.command == 'analyze':
        out = analyze(args.work)
        Path(args.output).write_text(json.dumps(out, indent=2, default=str) + '\n')
        print(out['reading'], out['failing_by_combo'], out['not_complete'][:10])
    return 0


if __name__ == '__main__':
    sys.exit(main())
