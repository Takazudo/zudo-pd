"""D2 sequenced -12 V discharge (owner-chosen route, 2026-11-14 JST): calculation across banks, loads and firing spread.

The -12 V discharge switch is held off while |-12 V| <= HOLD_V and +12 V > RELEASE_V, then released. All three
switches otherwise fire as in the fast matched discharge candidate (d2_fast_discharge.py). CALCULATED, ideal switches,
resistive loads at nominal voltage (ASSUMPTION). Switch-on times are swept
from the disconnect to stand in for part-to-part timing spread.
"""
import argparse
import itertools
import json
import math
import shutil
import sys
from pathlib import Path

import d2_fast_discharge as fd
import d2_load_corners as d2
import gap_sensitivity as gap

CRITERIA = 'd2-sequenced-criteria.md'
NAME = fd.NAME
CDGN = '68n'   # PROPOSED: fires the -12 V switch near 50 us, ahead of +12 V (180n fired at 131 us in attempt 2)
HOLD_V = 3.0
RELEASE_V = 0.3
PLANNING_A = {'+12': 1.5348, '-12': 1.4356, '+5': 0.2243}   # OSC E22 canonical planning loads
CORNERS = ('0', 'planning', 'maximum')
# Switch-on times from the disconnect (t = 0). Attempt 2 measured +12 V at 155 us and +5 V at 163 us after the EN_N
# crossing; the -12 V switch is to be designed to fire near 50 us. Each is spread to cover part-to-part timing.
FIRE_S = {'+12': (120e-6, 155e-6, 190e-6), '+5': (120e-6, 163e-6, 210e-6), '-12': (0.0, 25e-6, 50e-6, 75e-6, 100e-6)}


def load_ohm(rail, corner):
    amps = {'0': None, 'planning': PLANNING_A[rail], 'maximum': d2.MAXIMUM_A[rail]}[corner]
    return None if amps is None else d2.NOMINAL_V[rail] / amps


def load_corners():
    short = {'0': 'z', 'planning': 'p', 'maximum': 'm'}
    return {f'{short[a]}{short[b]}{short[c]}': {'+12': a, '-12': b, '+5': c}
            for a, b, c in itertools.product(CORNERS, repeat=3)}


def simulate(caps, corner, fire, resistors=fd.RESISTORS, sequenced=True, dt=1e-6, stop=0.1):
    """Exact per-step exponential decay from the load-band maxima; fire = {rail: switch-on time}. Returns the row results."""
    v = {r: abs(fd.START_V[r]) for r in caps}
    g_load = {r: (1 / x if (x := load_ohm(r, corner[r])) else 0.0) for r in caps}
    level = {r: None for r in caps}
    rvee = hazard = None
    t = 0.0
    while t < stop:
        absent = {r: v[r] <= fd.LEVEL_V[r] for r in v}
        held = sequenced and v['-12'] <= HOLD_V and v['+12'] > RELEASE_V
        for r in v:
            on = t >= fire[r] and not (r == '-12' and held)
            v[r] *= math.exp(-(g_load[r] + (1 / resistors[r] if on else 0.0)) / caps[r] * dt)
            if level[r] is None and v[r] <= fd.LEVEL_V[r]:
                level[r] = t
        if rvee is None and ((absent['-12'] and v['+12'] > 0.5) or (absent['+12'] and v['-12'] > 6.0)):
            rvee = t
        if hazard is None and v['+5'] > 0.8 and ((absent['+12'] and v['-12'] >= 8) or (absent['-12'] and v['+12'] >= 8)):
            hazard = t
        if all(level.values()):
            break
        t += dt
    ok_level = all(x is not None and x <= 0.1 for x in level.values())
    return {'rvee': rvee is None, 'direct_hazard': hazard is None, 'level_within_100ms': ok_level,
            'pass': rvee is None and hazard is None and ok_level,
            'level_s': {r: (None if x is None else round(x, 7)) for r, x in level.items()}}


def calc(sequenced=True):
    failing, slowest = [], 0.0
    for bank, caps in fd.banks().items():
        for lbl, corner in load_corners().items():
            for t12, tn, t5 in itertools.product(FIRE_S['+12'], FIRE_S['-12'], FIRE_S['+5']):
                fire = {'+12': t12, '-12': tn, '+5': t5}
                out = simulate(caps, corner, fire, sequenced=sequenced)
                if not out['pass']:
                    failing.append({'bank': bank, 'loads': lbl, 'fire_us': {r: round(x * 1e6) for r, x in fire.items()},
                                    'rows': {k: out[k] for k in ('rvee', 'direct_hazard', 'level_within_100ms')}})
                else:
                    slowest = max(slowest, max(out['level_s'].values()))
    return {'record': 'D2 sequenced -12 V discharge (CALCULATED; ideal switches; resistive-load ASSUMPTION)',
            'sequenced': sequenced, 'hold_v': HOLD_V, 'release_v': RELEASE_V, 'resistors_ohm': fd.RESISTORS,
            'banks': len(fd.banks()), 'load_corners': len(load_corners()),
            'fire_us': {r: [round(x * 1e6) for x in v] for r, v in FIRE_S.items()},
            'cases': len(fd.banks()) * len(load_corners()) * len(FIRE_S['+12']) * len(FIRE_S['-12']) * len(FIRE_S['+5']),
            'failing': len(failing), 'failing_examples': failing[:10], 'slowest_to_level_s': round(slowest, 7)}


SMOOTH_Q54 = 'BQ54 disc dgx I=v(disc,dgx)*(1/5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(disc,dgx)*1e-9\n'
# Behavioural sequencer (PROPOSED function, discrete circuit not yet drawn): clamps the -12 V switch gate to its
# source through 100 ohm while |-12 V| <= HOLD_V and +12 V > RELEASE_V.
HOLD = (f'BHOLD dgn m12_out I=v(dgn,m12_out)*(1/100)*0.5*(1+tanh((v(p12_out)-{RELEASE_V})*40))'
        f'*0.5*(1-tanh((abs(v(m12_out))-{HOLD_V})*10))\n')


def deck(label, caps, corner):
    """The fast-discharge deck with the sequencer, the earlier -12 V firing, a smooth Q54 and the E22 +5 V planning load."""
    base = dict(corner, **({'+5': '0'} if corner['+5'] == 'planning' else {}))
    text = fd.deck(label, caps, base)
    swaps = [
        (text.splitlines(True)[0], f'* d2sq {label}: B20 sequenced -12 V discharge candidate ({CRITERIA}); compact shutdown deck\n'),
        ('.model SWQ54 SW(VT=2.5 VH=0.1 RON=5 ROFF=1e9)\n', ''),
        ('SQ54 disc dgx enn 0 SWQ54\n', SMOOTH_Q54),
        ('CDGN dgn m12_out 180n\n', f'CDGN dgn m12_out {CDGN}\n' + HOLD),
    ]
    for old, new in swaps:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    if corner['+5'] == 'planning':
        text = text.replace('.options ', f'RL5 p5_out 0 {load_ohm("+5", "planning"):.6g}\n.options ', 1)
    return text


def derive_cases():
    return {f'{b}-{l}': (b, corner, deck(f'{b}-{l}', caps, corner))
            for b, caps in fd.banks().items() for l, corner in load_corners().items()}


def tree(work, lbl):
    return Path(work) / 'd2sq' / lbl


def prepare(work):
    manifest = {'criteria': CRITERIA, 'labels': {}}
    for lbl, (bank_label, corner, text) in derive_cases().items():
        root = tree(work, lbl)
        (root / 'tracking').mkdir(parents=True, exist_ok=True)
        if not (root / 'lib').exists():
            shutil.copytree(Path(work) / 'lib', root / 'lib')
            shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        (root / 'tracking' / f'{NAME}.cir').write_text(text)
        manifest['labels'][lbl] = {'bank': bank_label, 'loads': corner, 'deck_sha256': gap.sha(text.encode())}
    return manifest


def status(work, lbl):
    return gap.case_status(tree(work, lbl), NAME)


def analyze(work):
    out, states = {}, {}
    for lbl, (bank_label, corner, _) in derive_cases().items():
        state = status(work, lbl)
        states[lbl] = state['status']
        row = {'bank': bank_label, 'loads': corner, 'status': state['status']}
        if state['status'] == 'COMPLETE':
            row.update(fd.read(fd.load(fd.attempt_dir(state['run'], NAME) / f'{NAME}.dat')))
        elif state['status'] == 'ABORTED':
            row['abort'] = state.get('abort')
        out[lbl] = row
    complete = [r for r in out.values() if r['status'] == 'COMPLETE']
    failing = sorted(k for k, r in out.items() if r['status'] == 'COMPLETE' and not r['pass'])
    verdict = 'FAIL (SIM)' if failing else ('PASS (SIM)' if len(complete) == len(out) else 'NOT FORMED')
    peaks = {r: max(c['peak_discharge_current_a'][r] for c in complete) for r in fd.RESISTORS} if complete else {}
    energy = {r: max(c['discharge_resistor_energy_j'][r] for c in complete) for r in fd.RESISTORS} if complete else {}
    return {'criteria': CRITERIA, 'reading': verdict, 'decks': len(out), 'complete': len(complete),
            'not_complete': sorted(k for k, s in states.items() if s != 'COMPLETE'), 'failing': failing,
            'largest_peak_discharge_current_a': peaks, 'largest_resistor_energy_j': energy, 'cases': out}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('calc')
    p.add_argument('--output', required=True)
    p.add_argument('--unsequenced', action='store_true', help='control: the same grid without the hold')
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
    if args.command == 'calc':
        out = calc(sequenced=not args.unsequenced)
        Path(args.output).write_text(json.dumps(out, indent=2) + '\n')
        print(out['cases'], 'cases,', out['failing'], 'failing')
    elif args.command == 'labels':
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
        print(out['reading'], out['failing'], out['not_complete'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
