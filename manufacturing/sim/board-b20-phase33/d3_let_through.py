"""D3 let-through envelope (d3-let-through-criteria.md): fault into one rail, the drawn trip chain, the pass pairs opening.

Compact deck: converters as 20 mOhm sources with a smooth saturation at the TPS54560 current-limit maximum
(8.3 A, SLVSBN0C), 57 uF PRE capacitors, the drawn shunts and vendor CSD18543Q3A pass pairs, the drawn FAULT_N /
latch / enable network with generic corner FETs, and the fault applied at the terminal at FAULT_S. Delivered current is
measured between the pass pair and the terminal. SIMULATED with stated ASSUMPTIONS; not a measurement.
"""
import argparse
import itertools
import json
import shutil
import sys
from pathlib import Path

from analysis_inputs import load
from extract_reference import attempt_dir
import d2_fast_discharge as fd
import d2_load_corners as d2
import gap_sensitivity as gap

CRITERIA = 'd3-let-through-criteria.md'
NAME = fd.NAME
FAULT_S = 0.5e-3
STOP_S = 1.5e-3
PRE_CHECK_S = 10e-6                                # enabled state checked this long before the fault
ARM_S = 50e-6                                      # latches released and alert armed (modelling initial condition)
ILIM_A = 8.3                                       # TPS54560 SLVSBN0C current limit threshold maximum (VIN 12 V row)
TRIP_A = {'+12': 2.085, '+5': 0.461, '-12': 1.996}  # limiter design trip points (osc-reply-20261114.md)
ALERT_R = 100.0                                    # INA301 VOL 300 mV max at IOL 3 mA -> 100 ohm (PA extrapolation)
ALERT_DELAY_S = {'+12': 1e-6, '+5': 1e-6, '-12': 10e-6}   # INA301 tp max; U9A OPA2187 recovery+slew (typical, PA)
CORNERS = {'q31': {'f': -1.0, 's': -2.5}, 'q39': {'f': 0.5, 's': 1.5}}
FAULTS = ('x12', 'x20', 'sht')                     # 1.2 x max, 2 x max, short via 20 mOhm / 100 nH (ASSUMPTION)
RAILS = {'+12': 'p12', '+5': 'p5', '-12': 'n12'}
OTHER_LOAD_A = {'+12': d2.PLANNING_A['+12'], '-12': d2.PLANNING_A['-12'], '+5': 0.2243}   # +5 V: d2_sequenced RL5 planning
VECTORS = ('i(VT12)', 'i(VT5)', 'i(VTN)', 'v(enn)', 'v(faultn)', 'v(flt_l)', 'v(p12_out)', 'v(p5_out)', 'v(m12_out)',
           'v(en_e)', 'v(alert)')


def fault_lines(rail, fault):
    node = {'+12': 'p12_out', '+5': 'p5_out', '-12': 'm12_out'}[rail]
    gate = f'0.5*(1+tanh((time-{FAULT_S:g})*2e7))'
    if fault == 'sht':
        return (f'LFLT {node} fx 100n\nBFLT fx 0 I=v(fx)/20m*{gate}\n')
    r = d2.NOMINAL_V[rail] / (d2.MAXIMUM_A[rail] * {'x12': 1.2, 'x20': 2.0}[fault])
    return f'BFLT {node} 0 I=v({node})/{r:.6g}*{gate}\n'


def deck(label, rail, fault, q31, q39):
    trip = TRIP_A[rail]
    sense = {'+12': 'i(VT12)', '+5': 'i(VT5)', '-12': '-i(VTN)'}[rail]
    tau = ALERT_DELAY_S[rail]
    loads = ''.join(f'{ref} {nodes} {d2.NOMINAL_V[r] / OTHER_LOAD_A[r]:.6g}\n'
                    for r, ref, nodes in (('+12', 'RL12', 'p12_out 0'), ('-12', 'RLN', '0 m12_out'), ('+5', 'RL5', 'p5_out 0'))
                    if r != rail)
    caps = fd.FITTED_BANK
    clamp = lambda n, src, v: f'B{n} {src} 0 I={-ILIM_A:g}*tanh(({v}-v({src}))/{0.02 * ILIM_A:.6g})\n'
    return f"""* d3lt {label}: B20 let-through, fault on {rail} ({CRITERIA}); compact deck, SIMULATED with ASSUMPTIONS
.include ../lib/opax187.lib
.include ../lib/csd18543q3a_ngspice.lib
.model DZ11 D(BV=10.8 IBV=1m RS=20 N=1.5)
.model NQ39 NMOS(LEVEL=1 VTO={q39} KP=0.1 LAMBDA=0.01)
.model NLOG NMOS(LEVEL=1 VTO=1.0 KP=0.1 LAMBDA=0.01)
.model PQ31 PMOS(LEVEL=1 VTO={q31} KP=0.1 LAMBDA=0.01)
.model PLOG PMOS(LEVEL=1 VTO=-2.0 KP=0.1 LAMBDA=0.01)
VIN vin 0 20
VSUP p5sup 0 4.98
* converters: 20 mOhm sources, smooth saturation at the TPS54560 current-limit maximum (ASSUMPTION: limit = output current)
{clamp('C12', 'p12_pre', 12.48)}CP12 p12_pre 0 57u
RSH12 p12_pre p12_sh 10m
{clamp('C5', 'p5_pre', 5.2)}CP5 p5_pre 0 57u
RSH5 p5_pre p5_sh 20m
{clamp('CN', 'm12_pre', -12.37)}CM12 0 m12_pre 57u
RSHN m12_sh m12_pre 10m
* pass pairs held on from the amplifier supply, drawn pulldowns keyed on EN_N
RG1 vin p12_g 10k
RG1P p12_g p12_cs 100k
DZ1 p12_cs p12_g DZ11
B10 p12_g 0 I=v(p12_g,0)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(p12_g,0)*1e-8
XQ1 p12_sh p12_g p12_cs csd18543q3a
XQ2 p12_q p12_g p12_cs csd18543q3a
VT12 p12_q p12_out 0
RG2 vin p5_g 10k
RG2P p5_g p5_cs 100k
DZ2 p5_cs p5_g DZ11
B11 p5_g 0 I=v(p5_g,0)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(p5_g,0)*1e-8
XQ3 p5_sh p5_g p5_cs csd18543q3a
XQ4 p5_q p5_g p5_cs csd18543q3a
VT5 p5_q p5_out 0
RG3 p5sup m12_g 10k
RG3P m12_g m12_cs 100k
DZ3 m12_cs m12_g DZ11
B25 m12_g m12_pre I=v(m12_g,m12_pre)*(1/3.5)*0.5*(1+tanh((v(enn)-2.5)*4))+v(m12_g,m12_pre)*1e-8
XQ5 m12_sh m12_g m12_cs csd18543q3a
RCV1 m12_cs m12_sh 100meg
XQ6 m12_q m12_g m12_cs csd18543q3a
VTN m12_q m12_out 0
* limiter alert for the faulted rail: comparator on the delivered current, {tau * 1e6:g} us delay, open drain, armed at {ARM_S * 1e6:g} us
BCMP cmp 0 V=5*0.5*(1+tanh(({sense}-{trip})*200))
RCMP cmp alert 1k
CCMP alert 0 {tau / 1e3:.6g}
BAL faultn 0 I=v(faultn)/{ALERT_R:g}*0.5*(1+tanh((v(alert)-2.5)*4))*0.5*(1+tanh((time-{ARM_S:g})*1e7))
* drawn FAULT_N, fault latch and enable latch (board_b20_spec.py); generic FETs, Q31 / Q39 at corners
RF1 p5sup faultn 10k
CF1 p5sup faultn 100n
MQ30 faultn flt_l 0 0 NLOG
MQ31 flt_lx faultn p5sup p5sup PQ31
RF2 flt_lx flt_l 4.7k
RF3 flt_l 0 100k
CF3 flt_l 0 100n
MQ39 en_e flt_l 0 0 NQ39
MQ34 en_ex enn p5sup p5sup PLOG
RE1 en_ex en_e 4.7k
RE2 en_e 0 100k
MQ33 enn en_e 0 0 NLOG
REN p5sup enn 10k
CEN enn 0 1n
* initial condition only (not a drawn part): both latches held in the enabled state until {ARM_S * 1e6:g} us
BRSF flt_l 0 I=v(flt_l)/100*0.5*(1-tanh((time-{ARM_S:g})*1e7))
BRSE enn 0 I=v(enn)/100*0.5*(1-tanh((time-{ARM_S:g})*1e7))
.nodeset v(enn)=0 v(en_e)=4.7 v(faultn)=4.98 v(flt_l)=0
.nodeset v(p12_pre)=12.48 v(p5_pre)=5.2 v(m12_pre)=-12.37 v(p12_out)=12.48 v(p5_out)=5.2 v(m12_out)=-12.37
* OSC side: fitted bank with 50 mOhm ESR; the other rails at planning load (ASSUMPTION)
CL12 p12_out cl12 {caps['+12']:.6g}
RCL12 cl12 0 50m
CL5 p5_out cl5 {caps['+5']:.6g}
RCL5 cl5 0 50m
CLN 0 cln {caps['-12']:.6g}
RCLN cln m12_out 50m
{loads}{fault_lines(rail, fault)}.options method=gear reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=200 rshunt=1e10
.tran 0.1u {STOP_S * 1e3:g}m 0 0.1u
.control
run
option numdgt=15
wrdata {NAME}.dat {' '.join(VECTORS)}
.endc
.end
"""


def derive_cases():
    out = {}
    for rail, fault, a, b in itertools.product(RAILS, FAULTS, CORNERS['q31'], CORNERS['q39']):
        label = f'{RAILS[rail]}-{fault}-{a}{b}'
        out[label] = (rail, fault, a + b, deck(label, rail, fault, CORNERS['q31'][a], CORNERS['q39'][b]))
    return out


def read(rows, rail):
    col = {'+12': 1, '+5': 2, '-12': 3}[rail]
    sign = -1 if rail == '-12' else 1
    imax, trip = d2.MAXIMUM_A[rail], TRIP_A[rail]
    before = [r for r in rows if r[0] <= FAULT_S - PRE_CHECK_S][-1]
    enabled = before[4] < 0.5 and sign * before[col] < trip
    after = [(r[0], sign * r[col]) for r in rows if r[0] >= FAULT_S]
    peak = max(i for _, i in after)
    above = sum(b[0] - a[0] for a, b in zip(after, after[1:]) if a[1] > imax)
    i2t = sum((a[1] ** 2 + b[1] ** 2) / 2 * (b[0] - a[0]) for a, b in zip(after, after[1:]))
    excess_i2t = sum((max(a[1] - imax, 0) ** 2 + max(b[1] - imax, 0) ** 2) / 2 * (b[0] - a[0])
                     for a, b in zip(after, after[1:]))
    detect = next((t for t, i in after if i > trip), None)
    off = None
    for t, i in after:
        if abs(i) > fd.CURRENT_THRESHOLD_A:
            off = None
        elif off is None:
            off = t
    ms = lambda t: None if t is None else round((t - FAULT_S) * 1e3, 6)
    return {'peak_a': peak, 'duration_above_max_ms': round(above * 1e3, 6), 'i2t_a2s': i2t,
            'excess_i2t_a2s': excess_i2t, 'detect_ms': ms(detect), 'off_ms': ms(off),
            'detection_to_off_ms': None if detect is None or off is None else round((off - detect) * 1e3, 6),
            'enabled_before_fault': enabled, 'opened': off is not None}


def tree(work, lbl):
    return Path(work) / 'd3lt' / lbl


def prepare(work):
    manifest = {'criteria': CRITERIA, 'labels': {}}
    for lbl, (rail, fault, corner, text) in derive_cases().items():
        root = tree(work, lbl)
        (root / 'tracking').mkdir(parents=True, exist_ok=True)
        if not (root / 'lib').exists():
            shutil.copytree(Path(work) / 'lib', root / 'lib')
            shutil.copyfile(Path(work) / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        (root / 'tracking' / f'{NAME}.cir').write_text(text)
        manifest['labels'][lbl] = {'rail': rail, 'fault': fault, 'corner': corner, 'deck_sha256': gap.sha(text.encode())}
    return manifest


def status(work, lbl):
    return gap.case_status(tree(work, lbl), NAME)


def analyze(work):
    out, states = {}, {}
    for lbl, (rail, fault, corner, _) in derive_cases().items():
        state = status(work, lbl)
        states[lbl] = state['status']
        row = {'rail': rail, 'fault': fault, 'corner': corner, 'status': state['status']}
        if state['status'] == 'COMPLETE':
            row.update(read(load(attempt_dir(state['run'], NAME) / f'{NAME}.dat'), rail))
        elif state['status'] == 'ABORTED':
            row['abort'] = state.get('abort')
        out[lbl] = row
    complete = [r for r in out.values() if r['status'] == 'COMPLETE']
    envelope = {}
    for rail in RAILS:
        for fault in FAULTS:
            rs = [r for r in complete if r['rail'] == rail and r['fault'] == fault]
            if rs:
                envelope[f'{rail} {fault}'] = {
                    'decks': len(rs), 'all_opened': all(r['opened'] for r in rs),
                    'peak_a': max(r['peak_a'] for r in rs),
                    'duration_above_max_ms': max(r['duration_above_max_ms'] for r in rs),
                    'i2t_a2s': max(r['i2t_a2s'] for r in rs),
                    'excess_i2t_a2s': max(r['excess_i2t_a2s'] for r in rs),
                    'detection_to_off_ms': max((r['detection_to_off_ms'] for r in rs
                                                if r['detection_to_off_ms'] is not None), default=None)}
    formed = (len(complete) == len(out) and all(e['all_opened'] for e in envelope.values())
              and all(r['enabled_before_fault'] for r in complete))
    return {'criteria': CRITERIA, 'reading': 'ENVELOPE FORMED (SIM)' if formed else 'NOT FORMED',
            'decks': len(out), 'complete': len(complete),
            'not_complete': sorted(k for k, s in states.items() if s != 'COMPLETE'),
            'envelope': envelope, 'cases': out}


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
        print(out['reading'], out['not_complete'][:10])
    return 0


if __name__ == '__main__':
    sys.exit(main())
