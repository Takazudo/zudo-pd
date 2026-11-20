#!/usr/bin/env python3
"""Targeted D2 re-simulation of the worst corners found by sensitivity.py (SIM, vendor CSD18543Q3A model).

Decks are the pre-registered d2_sequencer_circuit decks (discrete sequencer, generic small-part corner models), with
only these value edits: discharge resistors at their tolerance/hot corners, bank-side copper added in series with the
bank ESR (so the sequencer senses the board node), and CDG12 / CDGN rescaled to place the +12 V / -12 V switch onset at
the computed timing-band edges. Not pre-registered: an exploratory bound for review, not a criterion reading.

usage: python3 resim.py prepare WORK   (WORK/lib from extract_reference.py prepare)
       python3 resim.py analyze WORK --output resim.json
"""
import argparse, hashlib, json, shutil, sys
from pathlib import Path

SIM = Path(__file__).resolve().parents[4] / 'manufacturing/sim/board-b20-phase33'
sys.path.insert(0, str(SIM))
import d2_fast_discharge as fd  # noqa: E402
import d2_sequenced as sq  # noqa: E402
import d2_sequencer_circuit as sc  # noqa: E402

S = json.load(open(Path(__file__).with_name('sensitivity.json')))
R = S['resistance_corners']
J11 = {r: R[r]['bank_side_hot_ohm']['J11'] for r in R}


def rsw(rail, state):
    return {'fast': R[rail]['switch_min_ohm'], 'slow': R[rail]['switch_max_ohm'], 'nom': R[rail]['switch_nom_ohm']}[state]


# t_RC is proportional to C at a fixed threshold; analytic nominal t_fire from sensitivity.json
TP = S['timing']['p12_p5_switches']; TM = S['timing']['m12_switch']
p_nom = TP['t_fire_us_at_vth_typ']; m_nom = TM['fitted_47k5_69n']['t_fire_us_at_vth_typ']
CDG12 = {'nom': 22e-9, 'early_pa': 22e-9 * (p_nom + TP['band_minus_nominal_us'][0]) / p_nom,
         'early_guaranteed': 22e-9 * 72.0 / p_nom,  # VGS(th) 1.5 V, C -10 %, 4.9 V, no PA hot/DC-bias terms
         'late': 22e-9 * (p_nom + TP['band_minus_nominal_us'][1]) / p_nom,
         # VGS(th) 2.7 V, C +10 % + Ciss max, RDG +1 %, 4.9 V: guaranteed terms only
         'late_guaranteed': 22e-9 * (10.1e3 * (24.2e-9 + 1.15e-9) * __import__('math').log(4.9 / 2.2) * 1e6) / p_nom}
CDGN = {'nom': 68e-9, 'late': 69e-9 * (m_nom + TM['band_minus_nominal_us'][1]) / m_nom,
        'early': 69e-9 * (m_nom + TM['band_minus_nominal_us'][0]) / m_nom,
        # VGS(th) 1.5 V, C44 -5 %, C45 -10 %, R61 -1 %, R62 +0.1 %, 4.9 V: guaranteed terms only
        'early_guaranteed': 69e-9 * (4653 * 47547.5 / (4653 + 47547.5) * (47e-9 * 0.95 + 22e-9 * 0.9) * __import__('math').log(15.73 / 14.23) * 1e6) / m_nom}

CASES = {
    # mechanism 1: +12 V fires early and fast, -12 V fires late and slow (R-VEE: |-12| > 6 V once +12 absent)
    'm1-hhrl-plnhfh-mzm-pa': ('hhrl', 'plnhfh', 'mzm', {'+12': 'fast', '-12': 'slow', '+5': 'fast'}, 'early_pa', 'late'),
    'm1-hhrl-plnhfl-mzz-pa': ('hhrl', 'plnhfl', 'mzz', {'+12': 'fast', '-12': 'slow', '+5': 'fast'}, 'early_pa', 'late'),
    'm1-hhrl-plnhfh-mzm-gtd': ('hhrl', 'plnhfh', 'mzm', {'+12': 'fast', '-12': 'slow', '+5': 'fast'}, 'early_guaranteed', 'late'),
    'm1-hlrl-plnhfh-mzm-pa': ('hlrl', 'plnhfh', 'mzm', {'+12': 'fast', '-12': 'slow', '+5': 'fast'}, 'early_pa', 'late'),
    # mechanism 2: +12 V late and slow, -12 V early and fast (R-VEE: |-12| <= 0.6 V while +12 present)
    'm2-hlrh-phnlfl-zmz': ('hlrh', 'phnlfl', 'zmz', {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'late', 'early'),
    'm2-hhrh-phnlfl-zmz': ('hhrh', 'phnlfl', 'zmz', {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'late', 'early'),
    # attribution: the same timing with nominal resistors and no bank copper, and guaranteed-only timing
    'm1-hhrl-plnhfh-mzm-pa-nomR': ('hhrl', 'plnhfh', 'mzm', None, 'early_pa', 'late'),
    'm2-hlrh-phnlfl-zmz-nomR': ('hlrh', 'phnlfl', 'zmz', None, 'late', 'early'),
    'm2-hlrh-phnlfl-zmz-gtd': ('hlrh', 'phnlfl', 'zmz', {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'late_guaranteed', 'early_guaranteed'),
    'm2-hhrh-phnlfl-zmz-gtd': ('hhrh', 'phnlfl', 'zmz', {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'late_guaranteed', 'early_guaranteed'),
    'm2-hlrh-phnlfl-zmz-gtd-nomR': ('hlrh', 'phnlfl', 'zmz', None, 'late_guaranteed', 'early_guaranteed'),
    # parasitics and tolerances only, at the simulated (pre-registered) timing
    'p-hhrl-plnhfh-mzm': ('hhrl', 'plnhfh', 'mzm', {'+12': 'fast', '-12': 'slow', '+5': 'fast'}, 'nom', 'nom'),
    'p-hhrl-ceil-mzp': ('hhrl', 'ceil', 'mzp', {'+12': 'fast', '-12': 'slow', '+5': 'fast'}, 'nom', 'nom'),
    'p-hlrh-phnlfl-zmz': ('hlrh', 'phnlfl', 'zmz', {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'nom', 'nom'),
    'p-hlrl-phnlfl-zmz': ('hlrl', 'phnlfl', 'zmz', {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'nom', 'nom'),
    # controls: the published decks unchanged
    'ctl-hhrl-plnhfh-mzm': ('hhrl', 'plnhfh', 'mzm', None, 'nom', 'nom'),
    'ctl-hlrh-phnlfl-zmz': ('hlrh', 'phnlfl', 'zmz', None, 'nom', 'nom'),
}


def rep(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def deck(combo, bank, loads, rstate, t12, tn):
    text = sc.deck(f'{bank}-{loads}', fd.banks()[bank], sq.load_corners()[loads], combo)
    text = rep(text, 'wrdata nomR.dat v(p12_out) v(p5_out) v(m12_out) v(enn) i(VP12) i(VP5) i(VM12) i(VD12) i(VD5) i(VDN) v(dg12)',
               'wrdata nomR.dat v(p12_out) v(p5_out) v(m12_out) v(enn) i(VP12) i(VP5) i(VM12) i(VD12) i(VD5) i(VDN) v(dg12) v(cl12) v(cl5) v(cln) v(dgn,m12_out)')
    if rstate:
        for rail, rx, rcl in (('+12', 'RXD12 d12a d12b 0.5', 'RCL12 cl12 0 50m'), ('+5', 'RXD5 d5a d5b 0.5', 'RCL5 cl5 0 50m'),
                              ('-12', 'RXDN dna dnb 1.5', 'RCLN cln m12_out 50m')):
            text = rep(text, rx, rx.rsplit(' ', 1)[0] + f' {rsw(rail, rstate[rail]):.6g}')
            if rstate[rail] == 'slow':
                text = rep(text, rcl, rcl.rsplit(' ', 1)[0] + f' {0.05 + J11[rail]:.6g}')
    text = rep(text, 'CDG12 dg12 0 22n', f'CDG12 dg12 0 {CDG12[t12]:.6g}')
    text = rep(text, 'CDGN dgn m12_out 68n', f'CDGN dgn m12_out {CDGN[tn]:.6g}')
    return text


def prepare(work):
    work = Path(work)
    out = {}
    for name, args in CASES.items():
        root = work / 'resim' / name
        (root / 'tracking').mkdir(parents=True, exist_ok=True)
        if not (root / 'lib').exists():
            shutil.copytree(work / 'lib', root / 'lib')
        shutil.copyfile(work / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        text = deck(*args)
        (root / 'tracking' / 'nomR.cir').write_text(text)
        out[name] = hashlib.sha256(text.encode()).hexdigest()
    print(json.dumps({'decks_sha256': out, 'CDG12_F': CDG12, 'CDGN_F': CDGN}, indent=1))


def analyze(work, output):
    res = {}
    for name in CASES:
        dat = Path(work) / 'resim' / name / 'tracking' / 'nomR.dat'
        if not dat.exists():
            res[name] = {'status': 'NOT COMPLETE'}
            continue
        rows = [[float(x) for x in line.split()[1::2]] for line in dat.read_text().splitlines() if line.strip()]
        t = [float(line.split()[0]) for line in dat.read_text().splitlines() if line.strip()]
        rows = [[ti] + r[:11] for ti, r in zip(t, rows)]
        raw = [[float(x) for x in line.split()] for line in dat.read_text().splitlines() if line.strip()]
        r = fd.read(rows)
        t0 = next(x[0] for x in rows if x[4] > 2.5)
        # bank (capacitor) voltages: +rails V(out) - V(cl); -12: |V(cln)|
        bank = []
        for line in raw:
            vals = line[1::2]
            bank.append((line[0], vals[0] - vals[11], vals[1] - vals[12], abs(vals[13])))
        after = [b for b in bank if b[0] >= t0]
        board = [(x[0], x[1], abs(x[3])) for x in rows if x[0] >= t0]
        res[name] = {
            'status': 'COMPLETE' if t[-1] >= 5.99e-3 else f'ENDED {t[-1]}',
            'rows_board_node': r['rows'], 'pass_board_node': r['pass'], 'discharge_onset_ms': r['discharge_onset_ms'],
            'disconnect_ms': r['disconnect_ms'], 'level_reached_ms': r['level_reached_ms'],
            'board_max_abs_m12_once_p12_le_0v5': max((b[2] for b in board if b[1] <= 0.5), default=None),
            'board_min_abs_m12_while_p12_gt_0v5': min((b[2] for b in board if b[1] > 0.5), default=None),
            'bank_max_abs_m12_once_p12_le_0v5': max((b[3] for b in after if b[1] <= 0.5), default=None),
            'bank_min_abs_m12_while_p12_gt_0v5': min((b[3] for b in after if b[1] > 0.5), default=None),
            'onset_by_rail_ms': {rail: next(((x[0] - t0) * 1e3 for x in rows if x[0] >= t0 and abs(x[c]) > 0.01), None)
                                 for rail, c in (('+12', 8), ('+5', 9), ('-12', 10))}}
    Path(output).write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prepare'); p.add_argument('work')
    p = sub.add_parser('analyze'); p.add_argument('work'); p.add_argument('--output', required=True)
    a = ap.parse_args()
    prepare(a.work) if a.cmd == 'prepare' else analyze(a.work, a.output)
