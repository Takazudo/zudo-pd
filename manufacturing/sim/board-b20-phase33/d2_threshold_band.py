#!/usr/bin/env python3
"""D2 firing-network threshold/tolerance band (d2-threshold-band-criteria.md): decks, runner and reading. SIM only.

The decks are the published d2_sequencer_circuit decks (discrete sequencer, vendor CSD18543Q3A model, generic
small-part corner models) with these edits only:
  * each discharge switch gets a series gate source, which shifts its threshold rigidly (the gate draws no DC
    current), so the guaranteed VGS(th) band is applied to the vendor model itself rather than by rescaling a
    capacitor;
  * the firing parts (RDG12/RDG5, CDG12/CDG5, R61, R62, CDGN) are set per candidate and tolerance corner;
  * the hold-up drive level (DIS_P / DIS_C) is a parameter.
Rows are read by the unchanged d2_fast_discharge.read.

usage:
  d2_threshold_band.py prepare RUNDIR --set NAME     write decks (NAME: a key of SETS)
  d2_threshold_band.py run RUNDIR                    run every deck that has no .dat (pinned KiCad image, 2 CPUs)
  d2_threshold_band.py analyze RUNDIR --output PATH
"""
import argparse
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'tools'))
import analysis_inputs  # noqa: E402
import d2_fast_discharge as fd  # noqa: E402
import d2_sequenced as sq  # noqa: E402
import d2_sequencer_circuit as sc  # noqa: E402

IMAGE = 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
LIB = HERE / 'work' / 'lib'
SPICEINIT = HERE / 'work' / 'char' / '.spiceinit'

# Vendor model VGS at VDS = VGS, ID 250 uA (work/char/vth.cir, ngspice-44.2): 2.2036 V. Shift = corner - model.
MODEL_VTH = 2.2036
VTH = {'min': 1.5, 'typ': 2.0, 'max': 2.7}       # fact-c840100-vgs-th-min / -typ / -max (25 C only)
CISS_MAX_EXTRA = 1150e-12 - 885e-12             # fact-c840100-ciss-max over the typical row, added at the late corner

# Candidates: firing parts (nominal value, tolerance). 'cdgn' is a list of parallel parts.
CAND = {
    'asdrawn': {'rdg': (10e3, 0.01), 'cdg': (22e-9, 0.10), 'r61': (4.7e3, 0.01), 'r62': (47.5e3, 0.001),
                'cdgn': [(47e-9, 0.05), (22e-9, 0.10)]},
}


def corner_values(cand, edge):
    """edge -> {'p': early/nom/late for Q51+Q52 network, 'n': for Q55 network}; returns part values."""
    s = {'early': -1, 'nom': 0, 'late': +1}
    c = CAND[cand]
    kp, kn = s[edge['p']], s[edge['n']]
    out = {'rdg': c['rdg'][0] * (1 + kp * c['rdg'][1]),
           'cdg': c['cdg'][0] * (1 + kp * c['cdg'][1]) + (CISS_MAX_EXTRA if kp > 0 else 0.0),
           'r61': c['r61'][0] * (1 + kn * c['r61'][1]),
           # a larger R62 raises the asymptote (earlier); it barely moves tau
           'r62': c['r62'][0] * (1 - kn * c['r62'][1]),
           'cdgn': sum(v * (1 + kn * t) for v, t in c['cdgn']) + (CISS_MAX_EXTRA if kn > 0 else 0.0)}
    return out


def rep(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def deck(combo, bank, loads, vals, vth, dis, label):
    """vals: firing part values; vth: {'12','5','n'} threshold in volts at 250 uA; dis: hold-up drive volts."""
    text = sc.deck(f'{bank}-{loads}', fd.banks()[bank], sq.load_corners()[loads], combo)
    first = text.splitlines(True)[0]
    text = text.replace(first, f'* d2tb {label}: threshold/tolerance band (d2-threshold-band-criteria.md)\n', 1)
    text = rep(text, 'BDIS dis 0 V=4.9*0.5', f'BDIS dis 0 V={dis:.6g}*0.5')
    text = rep(text, 'VDISC disc 0 4.9', f'VDISC disc 0 {dis:.6g}')
    text = rep(text, 'RDG12 dis dg12 10k', f"RDG12 dis dg12 {vals['rdg']:.6g}")
    text = rep(text, 'RDG5 dis dg5 10k', f"RDG5 dis dg5 {vals.get('rdg5', vals['rdg']):.6g}")
    text = rep(text, 'CDG12 dg12 0 22n', f"CDG12 dg12 0 {vals['cdg']:.6g}")
    text = rep(text, 'CDG5 dg5 0 22n', f"CDG5 dg5 0 {vals.get('cdg5', vals['cdg']):.6g}")
    text = rep(text, 'R61 dgx dgn 4.7k', f"R61 dgx dgn {vals['r61']:.6g}")
    text = rep(text, 'R62 dgn m12_out 47k', f"R62 dgn m12_out {vals['r62']:.6g}")
    text = rep(text, 'CDGN dgn m12_out 68n', f"CDGN dgn m12_out {vals['cdgn']:.6g}")
    text = rep(text, 'XQD12 d12b dg12 0 csd18543q3a',
               f"VTS12 dg12 dg12x {vth['12'] - MODEL_VTH:.6g}\nXQD12 d12b dg12x 0 csd18543q3a")
    text = rep(text, 'XQD5 d5b dg5 0 csd18543q3a',
               f"VTS5 dg5 dg5x {vth['5'] - MODEL_VTH:.6g}\nXQD5 d5b dg5x 0 csd18543q3a")
    text = rep(text, 'XQDN dnb dgn m12_out csd18543q3a',
               f"VTSN dgn dgnx {vth['n'] - MODEL_VTH:.6g}\nXQDN dnb dgnx m12_out csd18543q3a")
    return text


# ---------------------------------------------------------------------------------------------------------------
# Deck sets. Each entry: label -> dict(combo, bank, loads, cand, edge, vth, dis)
EDGES = {  # firing-network corner: (Q51/Q52 network, Q55 network). Thresholds follow the same direction.
    'pl-ne': {'p': 'late', 'n': 'early'}, 'pe-nl': {'p': 'early', 'n': 'late'},
    'pl-nl': {'p': 'late', 'n': 'late'}, 'pe-ne': {'p': 'early', 'n': 'early'}, 'nom': {'p': 'nom', 'n': 'nom'}}
VTH_OF = {'early': 'min', 'nom': 'typ', 'late': 'max'}
SETS = {}


def register(name):
    def wrap(fn):
        SETS[name] = fn
        return fn
    return wrap


X7R_CDGN = (22e-9, 0.10)   # C45 (CDGNB), the only X7R part left in a firing network


def case(cand, combo, bank, loads, edge, dis, vth_shift=0.0, x7r=None, tag=''):
    """x7r = (factor at the early Q55 corner, factor at the late Q55 corner) on C45's capacitance (PA band only)."""
    e = EDGES[edge]
    vals = corner_values(cand, e)
    if x7r and e['n'] != 'nom':
        assert X7R_CDGN in CAND[cand]['cdgn']
        k = -1 if e['n'] == 'early' else 1
        part = X7R_CDGN[0] * (1 + k * X7R_CDGN[1])
        vals['cdgn'] += part * ((x7r[0] if k < 0 else x7r[1]) - 1)
    vth = {'12': VTH[VTH_OF[e['p']]] + vth_shift, '5': VTH[VTH_OF[e['p']]] + vth_shift,
           'n': VTH[VTH_OF[e['n']]] + vth_shift}
    d = dis[{'late': 0, 'early': 1, 'nom': 2 if len(dis) > 2 else 1}[e['p']]] if isinstance(dis, tuple) else dis
    label = f'{cand}-{combo}-{bank}-{loads}-{edge}{tag}'
    return label, {'cand': cand, 'combo': combo, 'bank': bank, 'loads': loads, 'edge': edge, 'vals': vals,
                   'vth': vth, 'dis': d}


def prepare(rundir, name):
    rundir = Path(rundir)
    cases = SETS[name]()
    (rundir / 'home').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SPICEINIT, rundir / 'home' / '.spiceinit')
    if not (rundir / 'lib').exists():
        shutil.copytree(LIB, rundir / 'lib')
    manifest = {'set': name, 'model_vth_v': MODEL_VTH, 'labels': {}}
    for label, c in cases.items():
        root = rundir / label
        root.mkdir(exist_ok=True)
        text = deck(c['combo'], c['bank'], c['loads'], c['vals'], c['vth'], c['dis'], label)
        (root / 'nomR.cir').write_text(text)
        manifest['labels'][label] = dict(c, deck_sha256=hashlib.sha256(text.encode()).hexdigest())
    (rundir / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(len(cases), 'decks')


def run(rundir):
    rundir = Path(rundir).resolve()
    script = ('cd /w && ls -d */ | grep -v -e "^lib/" -e "^home/" | sed "s,/,," | '
              'xargs -P 2 -I{} sh -c "cd /w/{} && [ -f nomR.dat ] || ngspice -b nomR.cir > run.log 2>&1 || true"')
    cmd = ['flock', '/tmp/kicad-native.lock', 'docker', 'run', '--rm', '--pull=never', '--cpus', '2', '--user', '0',
           '-e', 'HOME=/w/home', '-v', f'{rundir}:/w', IMAGE, 'sh', '-c', script]
    return subprocess.run(cmd).returncode


def status(root):
    dat, log = root / 'nomR.dat', root / 'run.log'
    if not log.exists():
        return 'NOT RUN', None
    if not dat.exists():
        return 'ABORTED', None
    try:
        rows = analysis_inputs.load(dat)
    except ValueError as error:
        return f'ABORTED ({error})'[:120], None
    if rows[-1][0] < fd.STOP_S - 2e-6:
        return 'ABORTED', None
    return 'COMPLETE', rows


def analyze(rundir):
    rundir = Path(rundir)
    manifest = json.loads((rundir / 'manifest.json').read_text())
    out = {}
    for label, c in manifest['labels'].items():
        state, rows = status(rundir / label)
        row = {k: c[k] for k in ('cand', 'combo', 'bank', 'loads', 'edge', 'vth', 'dis', 'vals', 'deck_sha256')}
        row['status'] = state
        if rows:
            r = fd.read(rows)
            t0 = next(x[0] for x in rows if x[4] > 2.5)
            after = [x for x in rows if x[0] >= t0]
            r['min_abs_m12_while_p12_present'] = min((abs(x[3]) for x in after if x[1] > fd.LEVEL_V['+12']), default=None)
            r['max_abs_m12_once_p12_absent'] = max((abs(x[3]) for x in after if abs(x[1]) <= fd.LEVEL_V['+12']), default=None)
            r['onset_by_rail_ms'] = {rail: next((round((x[0] - t0) * 1e3, 6) for x in after if abs(x[c]) > 0.01), None)
                                     for rail, c in (('+12', 8), ('+5', 9), ('-12', 10))}
            row.update(r)
        out[label] = row
    complete = {k: r for k, r in out.items() if r['status'] == 'COMPLETE'}
    failing = sorted(k for k, r in complete.items() if not r['pass'])
    verdict = 'FAIL (SIM)' if failing else ('PASS (SIM)' if len(complete) == len(out) else 'NOT FORMED')
    lo = min(complete.items(), key=lambda kv: kv[1]['min_abs_m12_while_p12_present'] or 99, default=(None, {}))
    hi = max(complete.items(), key=lambda kv: kv[1]['max_abs_m12_once_p12_absent'] or 0, default=(None, {}))
    onsets = [r['discharge_onset_ms'] for r in complete.values() if r['discharge_onset_ms'] is not None]
    return {'set': manifest['set'], 'reading': verdict, 'decks': len(out), 'complete': len(complete),
            'not_complete': sorted(k for k, r in out.items() if r['status'] != 'COMPLETE'), 'failing': failing,
            'failing_rows': {k: [n for n, v in complete[k]['rows'].items() if not v] for k in failing},
            'smallest_abs_m12_while_p12_present': [lo[0], lo[1].get('min_abs_m12_while_p12_present')],
            'largest_abs_m12_once_p12_absent': [hi[0], hi[1].get('max_abs_m12_once_p12_absent')],
            'earliest_discharge_onset_ms': min(onsets, default=None),
            'slowest_level_ms': max((max(r['level_reached_ms'].values()) for r in complete.values()
                                     if all(v is not None for v in r['level_reached_ms'].values())), default=None),
            'largest_peak_discharge_current_a': {rail: max(r['peak_discharge_current_a'][rail] for r in complete.values())
                                                 for rail in fd.RESISTORS} if complete else {},
            'largest_resistor_energy_j': {rail: max(r['discharge_resistor_energy_j'][rail] for r in complete.values())
                                          for rail in fd.RESISTORS} if complete else {},
            'cases': out}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prepare'); p.add_argument('rundir'); p.add_argument('--set', required=True)
    p = sub.add_parser('run'); p.add_argument('rundir')
    p = sub.add_parser('analyze'); p.add_argument('rundir'); p.add_argument('--output', required=True)
    a = ap.parse_args(argv)
    if a.cmd == 'prepare':
        prepare(a.rundir, a.set)
    elif a.cmd == 'run':
        return run(a.rundir)
    else:
        out = analyze(a.rundir)
        Path(a.output).write_text(json.dumps(out, indent=1, default=str) + '\n')
        print(out['reading'], len(out['failing']), 'failing of', out['decks'], '| not complete', len(out['not_complete']),
              '| low', out['smallest_abs_m12_while_p12_present'], '| high', out['largest_abs_m12_once_p12_absent'],
              '| earliest onset ms', out['earliest_discharge_onset_ms'])
    return 0


if __name__ == '__main__':
    import d2_threshold_band as tb
    import d2_threshold_sets  # noqa: F401  (registers SETS and CAND)
    sys.exit(tb.main())
