#!/usr/bin/env python3
"""D2 fast matched discharge (d2-fast-discharge-criteria.md): calculation, deck generation and reading.

The owner's D2 route (2026-11-14 JST): disconnect first, then switch 0.5 / 1.5 / 0.5 ohm onto +12 / -12 / +5 V at once,
so that no OSC per-rail load can reorder the decay. A candidate evaluation: no schematic, BOM or contract change.

usage:
  d2_fast_discharge.py calc --output PATH                      closed-form decay over banks x load corners
  d2_fast_discharge.py prepare WORK --manifest PATH            (after extract_reference.py prepare)
  for LABEL in $(d2_fast_discharge.py labels): run_ladder.py WORK/d2fd/LABEL/tracking nomR --original-only
  d2_fast_discharge.py analyze WORK --output PATH
"""

import argparse
import itertools
import json
from pathlib import Path
import shutil
import sys

from extract_reference import attempt_dir
from analysis_inputs import load
import d2_load_corners as d2
import gap_sensitivity as gap
import interface_diagnostics as idg

CRITERIA = 'd2-fast-discharge-criteria.md'
NAME = 'nomR'
RESISTORS = {'+12': 0.5, '-12': 1.5, '+5': 0.5}
FITTED_BANK = {'+12': 49.9e-6, '+5': 24.5e-6, '-12': 42.2e-6}   # OSC owner-reported fitted bank (osc-bank-criteria.md)
CEILING_BANK = {'+12': 180e-6, '+5': 120e-6, '-12': 180e-6}
START_V = {'+12': 12.48, '+5': 5.2, '-12': -12.37}               # load-band maxima
DISABLE_S = 1e-3
STOP_S = 6e-3
LEVEL_V = {'+12': 0.5, '-12': 0.6, '+5': 0.6}
CURRENT_THRESHOLD_A = 0.010
SKEW_MAX_S = 1e-3
VECTORS = ('v(p12_out)', 'v(p5_out)', 'v(m12_out)', 'v(enn)', 'i(VP12)', 'i(VP5)', 'i(VM12)',
           'i(VD12)', 'i(VD5)', 'i(VDN)', 'v(dg12)')


def banks():
    """label -> {rail: farads}: the contract ceiling and the 8 corners of the fitted bank at +/-20 %."""
    out = {'ceil': dict(CEILING_BANK)}
    for a, b, c in itertools.product(('l', 'h'), repeat=3):
        scale = {'l': 0.8, 'h': 1.2}
        out[f'p{a}n{b}f{c}'] = {'+12': FITTED_BANK['+12'] * scale[a], '-12': FITTED_BANK['-12'] * scale[b],
                                '+5': FITTED_BANK['+5'] * scale[c]}
    return out


def load_corners():
    """label -> {rail: corner name}, the d2_load_corners grid (18)."""
    short = {'0': 'z', 'planning': 'p', 'maximum': 'm'}
    return {f'{short[a]}{short[b]}{short[c]}': {'+12': a, '-12': b, '+5': c}
            for a, b, c in itertools.product(d2.CORNERS['+12'], d2.CORNERS['-12'], d2.CORNERS['+5'])}


def calc():
    """Closed-form decay with ideal simultaneous switching, every bank x every load corner."""
    base = idg.calculator()

    class Bank:
        def __init__(self, caps):
            self.C_LOAD_MAX = caps

        def __getattr__(self, key):
            return getattr(base, key)

    rows = {}
    for label, caps in banks().items():
        out = d2.corners(Bank(caps), resistors=RESISTORS, step_s=0.5e-6, stop_s=3e-3)
        rows[label] = {'bank_uf': {r: round(c * 1e6, 3) for r, c in caps.items()},
                       'corners_failing': out['corners_failing'],
                       'slowest_to_level_s': max(max(c['time_to_discharge_level_s'].values()) for c in out['corners'])}
    return {'record': 'D2 fast matched discharge, closed-form decay (CALCULATED; ideal simultaneous switches; '
                      'resistive-load ASSUMPTION)',
            'resistors_ohm': RESISTORS, 'banks': rows,
            'banks_failing': [k for k, v in rows.items() if v['corners_failing']]}


def deck(label, caps, corner):
    loads = {r: d2.load_ohm(r, k) for r, k in corner.items() if d2.load_ohm(r, k)}
    load_lines = ''.join(f'{ref} {node} {val:.6g}\n' for r, ref, node in (('+12', 'RL12', 'p12_out 0'),
                         ('-12', 'RLN', '0 m12_out'), ('+5', 'RL5', 'p5_out 0')) if (val := loads.get(r)))
    v12, v5, vn = START_V['+12'], START_V['+5'], START_V['-12']
    td = DISABLE_S
    return f"""* d2fd {label}: B20 fast matched discharge candidate (d2-fast-discharge-criteria.md); compact shutdown deck
.include ../lib/opax187.lib
.include ../lib/csd18543q3a_ngspice.lib
.model DZ11 D(BV=10.8 IBV=1m RS=20 N=1.5)
.model SWQ54 SW(VT=2.5 VH=0.1 RON=5 ROFF=1e9)
VIN vin 0 20
VSUP p5sup 0 4.98
* converters as stiff sources at the load-band maxima behind 20 mOhm (PA), shunts as drawn
VP12 p12_src 0 {v12}
RP12S p12_src p12_pre 20m
CP12 p12_pre 0 57u
RSH12 p12_pre p12_sh 10m
VP5 p5_src 0 {v5}
RP5S p5_src p5_pre 20m
CP5 p5_pre 0 57u
RSH5 p5_pre p5_sh 20m
VM12 m12_src 0 {vn}
RM12S m12_src m12_pre 20m
CM12 0 m12_pre 57u
RSHN m12_sh m12_pre 10m
* shutdown decision: EN_N rises at {td * 1e3:g} ms
VENN enn 0 PWL(0 0 {td:.6g} 0 {td + 1e-6:.6g} 5)
* pass pairs held fully on from the amplifier supply (slowest turn-off), drawn pulldowns on EN_N
RG1 vin p12_g 10k
RG1P p12_g p12_cs 100k
DZ1 p12_cs p12_g DZ11
B10 p12_g 0 I=v(p12_g,0)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(p12_g,0)*1e-8
XQ1 p12_sh p12_g p12_cs csd18543q3a
XQ2 p12_out p12_g p12_cs csd18543q3a
RG2 vin p5_g 10k
RG2P p5_g p5_cs 100k
DZ2 p5_cs p5_g DZ11
B11 p5_g 0 I=v(p5_g,0)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(p5_g,0)*1e-8
XQ3 p5_sh p5_g p5_cs csd18543q3a
XQ4 p5_out p5_g p5_cs csd18543q3a
RG3 p5sup m12_g 10k
RG3P m12_g m12_cs 100k
DZ3 m12_cs m12_g DZ11
B25 m12_g m12_pre I=v(m12_g,m12_pre)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(m12_g,m12_pre)*1e-8
XQ5 m12_sh m12_g m12_cs csd18543q3a
RCV1 m12_cs m12_sh 100meg
XQ6 m12_out m12_g m12_cs csd18543q3a
* hold-up drive: DIS_P / DIS_C at 4.9 V once EN_N is high (Q56 / Q54 from CDH)
BDIS dis 0 V=4.9*0.5*(1+tanh((v(enn)-2.5)*4))
* candidate fast discharge: 0.5 / 1.5 / 0.5 ohm switched by CSD18543Q3A, gate delay networks (PROPOSED)
RDG12 dis dg12 10k
CDG12 dg12 0 22n
VD12 p12_out d12a 0
RXD12 d12a d12b {RESISTORS['+12']}
XQD12 d12b dg12 0 csd18543q3a
RDG5 dis dg5 10k
CDG5 dg5 0 22n
VD5 p5_out d5a 0
RXD5 d5a d5b {RESISTORS['+5']}
XQD5 d5b dg5 0 csd18543q3a
* Q54 as a switch from DIS_C: M12_DGX floats while enabled, so the -12 V gate sits at M12_OUT
VDISC disc 0 4.9
SQ54 disc dgx enn 0 SWQ54
R61 dgx dgn 4.7k
R62 dgn m12_out 47k
CDGN dgn m12_out 180n
DZN m12_out dgn DZ11
VDN 0 dna 0
RXDN dna dnb {RESISTORS['-12']}
XQDN dnb dgn m12_out csd18543q3a
* OSC side: bank with 50 mOhm ESR, resistive loads at nominal voltage (ASSUMPTION)
CL12 p12_out cl12 {caps['+12']:.6g}
RCL12 cl12 0 50m
CL5 p5_out cl5 {caps['+5']:.6g}
RCL5 cl5 0 50m
CLN 0 cln {caps['-12']:.6g}
RCLN cln m12_out 50m
{load_lines}.options method=gear reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=200 rshunt=1e10
.tran 1u {STOP_S * 1e3:g}m 0 1u
.control
run
option numdgt=15
wrdata {NAME}.dat {' '.join(VECTORS)}
.endc
.end
"""


def derive_cases():
    """label -> (bank label, load corner, deck text)."""
    out = {}
    for bank_label, caps in banks().items():
        for load_label, corner in load_corners().items():
            label = f'{bank_label}-{load_label}'
            out[label] = (bank_label, corner, deck(label, caps, corner))
    return out


def tree(work, lbl):
    return Path(work) / 'd2fd' / lbl


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


def pending(work, lbl):
    derive_cases()[lbl]
    return [NAME] if status(work, lbl)['status'] == 'NOT RUN' else []


def check_run(work, lbl):
    state = status(work, lbl)['status']
    return {} if state in ('COMPLETE', 'ABORTED') else {NAME: state}


def first_time(rows, start, predicate):
    return next((r[0] for r in rows if r[0] >= start and predicate(r)), None)


def last_above(rows, start, column, threshold):
    """Time after which |column| stays at or below threshold (None if it never falls)."""
    t = None
    for r in rows:
        if r[0] >= start and abs(r[column]) > threshold:
            t = r[0]
    return t


def read(rows):
    """Apply the pre-registered rows to one waveform (columns as VECTORS, time first)."""
    p12, p5, m12, enn, ip12, ip5, ipn, id12, id5, idn, _ = range(1, 12)
    t0 = first_time(rows, 0, lambda r: r[enn] > 2.5)
    after = [r for r in rows if r[0] >= t0]
    disconnect = {rail: last_above(rows, t0, col, CURRENT_THRESHOLD_A) or t0
                  for rail, col in (('+12', ip12), ('+5', ip5), ('-12', ipn))}
    onset = first_time(rows, t0, lambda r: max(abs(r[id12]), abs(r[id5]), abs(r[idn])) > CURRENT_THRESHOLD_A)
    level = {rail: first_time(rows, t0, lambda r, c=col, v=LEVEL_V[rail]: abs(r[c]) <= v)
             for rail, col in (('+12', p12), ('+5', p5), ('-12', m12))}
    rvee = next((r[0] for r in after if (abs(r[m12]) <= LEVEL_V['-12'] and r[p12] > idg.P12_WHILE_M12_ABSENT_MAX)
                 or (abs(r[p12]) <= LEVEL_V['+12'] and abs(r[m12]) > idg.M12_WHILE_P12_ABSENT_MAX)), None)
    hazard = next((r[0] for r in after
                   if ((abs(r[p12]) <= LEVEL_V['+12'] and abs(r[m12]) >= idg.ADG_OTHER_RAIL_MIN)
                       or (abs(r[m12]) <= LEVEL_V['-12'] and abs(r[p12]) >= idg.ADG_OTHER_RAIL_MIN))
                   and r[p5] > idg.P5_HOLD_MAX), None)
    energy = {}
    for rail, col in (('+12', id12), ('+5', id5), ('-12', idn)):
        e = sum(RESISTORS[rail] * (a[col] ** 2 + b[col] ** 2) / 2 * (b[0] - a[0]) for a, b in zip(after, after[1:]))
        energy[rail] = e
    rows_out = {
        'disconnect_before_discharge': onset is None or onset > max(disconnect.values()),
        'disconnect_skew': max(disconnect.values()) - min(disconnect.values()) <= SKEW_MAX_S,
        'discharge_level_within_100ms': all(v is not None and v - t0 <= 0.1 for v in level.values()),
        'rvee': rvee is None,
        'direct_hazard': hazard is None}
    ms = lambda t: None if t is None else round((t - t0) * 1e3, 6)
    return {'rows': rows_out, 'pass': all(rows_out.values()),
            'disconnect_ms': {k: ms(v) for k, v in disconnect.items()}, 'discharge_onset_ms': ms(onset),
            'level_reached_ms': {k: ms(v) for k, v in level.items()},
            'first_rvee_ms': ms(rvee), 'first_hazard_ms': ms(hazard),
            'peak_discharge_current_a': {rail: max(abs(r[col]) for r in after)
                                         for rail, col in (('+12', id12), ('+5', id5), ('-12', idn))},
            'discharge_resistor_energy_j': energy}


def analyze(work):
    cases = derive_cases()
    out, states = {}, {}
    for lbl, (bank_label, corner, _) in cases.items():
        state = status(work, lbl)
        states[lbl] = state['status']
        row = {'bank': bank_label, 'loads': corner, 'status': state['status']}
        if state['status'] == 'COMPLETE':
            row.update(read(load(attempt_dir(state['run'], NAME) / f'{NAME}.dat')))
        elif state['status'] == 'ABORTED':
            row['abort'] = state.get('abort')
        out[lbl] = row
    complete = [r for r in out.values() if r['status'] == 'COMPLETE']
    failing = sorted(k for k, r in out.items() if r['status'] == 'COMPLETE' and not r['pass'])
    verdict = 'FAIL (SIM)' if failing else ('PASS (SIM)' if len(complete) == len(out) else 'NOT FORMED')
    peaks = {rail: max(r['peak_discharge_current_a'][rail] for r in complete) for rail in RESISTORS} if complete else {}
    energy = {rail: max(r['discharge_resistor_energy_j'][rail] for r in complete) for rail in RESISTORS} if complete else {}
    return {'criteria': CRITERIA, 'reading': verdict, 'decks': len(out), 'complete': len(complete),
            'not_complete': sorted(k for k, s in states.items() if s != 'COMPLETE'), 'failing': failing,
            'largest_peak_discharge_current_a': peaks, 'largest_resistor_energy_j': energy, 'cases': out}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('calc')
    p.add_argument('--output', required=True)
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
        out = calc()
        Path(args.output).write_text(json.dumps(out, indent=2) + '\n')
        print(json.dumps(out['banks_failing']))
    elif args.command == 'labels':
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
        print(out['reading'], out['failing'], out['not_complete'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
