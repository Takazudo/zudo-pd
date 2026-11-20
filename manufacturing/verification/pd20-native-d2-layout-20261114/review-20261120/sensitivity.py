#!/usr/bin/env python3
"""D2 bounded sensitivity of the ADOPTED B20 fast discharge to routed parasitics, tolerances and fitted timing parts.

CALCULATED (ideal-threshold switches, resistive loads at nominal voltage: the d2_sequenced.py calculation
generalised to a two-node rail model). Not simulated, not measured. Independent review for PR #307.

usage: python3 sensitivity.py --repo <repo root> --output sensitivity.json
"""
import argparse, hashlib, itertools, json, math, re, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pcbparse as pp  # noqa: E402

PCB = 'boards/board-b20-draft/board-b20-draft.kicad_pcb'
SPEC = 'scripts/schgen/board_b20_spec.py'
LOOP = 'manufacturing/verification/pd20-native-d2-layout-20261114/loop-resistance.txt'
SIM = 'manufacturing/sim/board-b20-phase33'
SIM_JSON = (f'{SIM}/d2-sequenced-20261114.json', f'{SIM}/d2-sequencer-circuit-20261114.json')

# ---- sourced values (owner skills) -------------------------------------------------------------------
WSL_OHM, WSL_TOL, WSL_TCR = 0.5, 0.01, 75e-6           # C511023 fact-c511023-resistance / -tcr (+/-75 ppm/C)
RDS_4V5_MAX_25C = 15.6e-3                              # C840100 fact-c840100-rdson-4v5-max (25 C only)
VTH_MIN, VTH_TYP, VTH_MAX = 1.5, 2.0, 2.7              # C840100 VGS(th) 25 C guaranteed min/max, typ
CISS_MAX = 1150e-12                                    # C840100 fact-c840100-ciss-max
C44_TOL = 0.05                                         # C5451690 47 nF C0G J +/-5 %
C45_TOL = 0.10                                         # C1729 22 nF X7R K +/-10 %
R61_TOL, R62_TOL, RDG_TOL = 0.01, 0.001, 0.01          # C23162 / C136962 (0.1 %) / C25804
# ---- project assumptions (PA), stated --------------------------------------------------------------------
T_HOT, T_COLD, T_REF_CU = 85.0, 0.0, 20.0              # board temperature corners (PA)
CU_TCR = 0.00393                                       # annealed copper, per K (task-given, standard value)
RHO_CU = 1.72e-8                                       # same resistivity as loop-resistance.py
IN1_T = 17.5e-6                                        # In1.Cu thickness from the PCB stackup (read below)
PLATING_T = 18e-6                                      # via barrel plating (PA, thinner than loop-resistance.py 25 um)
SPREAD_FACTOR = 3.0                                    # PA: x2 half-plane (sources near the board edge) x1.5 antipads
RDS_HOT_FACTOR = 2.0                                   # PA: SLPS633 hot RDS(on) is a typical curve only (not digitised)
X7R_TC = 0.15                                          # EIA X7R class limit -55..125 C (class definition)
X7R_DCBIAS = 0.25                                      # PA: unsourced DC-bias loss at <= 11 V on a 50 V 0805 (bench item)
VTH_HOT_SHIFT = 0.30                                   # PA: typical slope -4.6 mV/C x 60 K; no guaranteed hot bound
DIS_V = (4.4, 4.9, 5.0)                                # PA: hold-up drive DIS_P / DIS_C (sim uses 4.9 V)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cu_hot(r):
    return r * (1 + CU_TCR * (T_HOT - T_REF_CU))


def geometry(repo):
    g = pp.load(repo / PCB)
    txt = (repo / PCB).read_text()
    m = re.search(r'\(layer "In1\.Cu"\s*\(type "copper"\)\s*\(thickness ([0-9.]+)\)', txt)
    in1_t = float(m.group(1)) * 1e-3
    assert abs(in1_t - IN1_T) < 1e-9, in1_t
    F = {f['ref']: f for f in g['fps']}
    out = {'in1_thickness_mm': in1_t * 1e3}
    # series pulse-net copper (every segment summed in series: an upper bound)
    out['pulse_nets'] = {}
    for net in ('P12_DX', 'P5_DX', 'M12_DX', 'M12_DXA', 'M12_DXB'):
        segs = [s for s in g['segs'] if s['net'] == net]
        r = sum(RHO_CU * math.dist(s['a'], s['b']) * 1e-3 / (s['w'] * 1e-3 * 35e-6) for s in segs)
        out['pulse_nets'][net] = {'segments': len(segs), 'vias': sum(v['net'] == net for v in g['vias']),
                                  'r_20c_ohm': r}
    # GND source vias and In1 spreading to connector GND pins
    rs = RHO_CU / IN1_T
    src = {'+12': ('Q51', ('1', '2', '3')), '+5': ('Q52', ('1', '2', '3')), '-12': ('R76', ('1',))}
    conns = {'near': {'+12': [('J6', '1')], '+5': [('J6', '1')], '-12': [('J6', '1')]},
             'J10': [('J10', n) for n in '345678'], 'J11': [('J11', n) for n in '345678']}
    out['gnd'] = {}
    for rail, (ref, pads) in src.items():
        pts = [p['xy'] for p in F[ref]['pads'] if p['num'] in pads]
        vias = [v for v in g['vias'] if v['net'] == 'GND' and min(math.dist(v['xy'], q) for q in pts) < 2.6]
        barrel = RHO_CU * 1.6e-3 / (math.pi * 0.3e-3 * PLATING_T)
        r_vias = barrel / len(vias)
        cx = sum(v['xy'][0] for v in vias) / len(vias); cy = sum(v['xy'][1] for v in vias) / len(vias)
        per = {}
        for cname in ('near', 'J10', 'J11'):
            pins = conns[cname][rail] if cname == 'near' else conns[cname]
            best = None
            for cref, num in pins:
                p = next(pp_ for pp_ in F[cref]['pads'] if pp_['num'] == num)
                d = math.dist((cx, cy), p['xy'])
                a, b = 0.15, p['drill'] / 2
                r = SPREAD_FACTOR * rs / math.pi * math.log(d / math.sqrt(a * b))
                best = min(best or (9, 0, 0), (r, d, cref + '.' + num))
            per[cname] = {'r_20c_ohm': best[0], 'distance_mm': best[1], 'pin': best[2]}
        out['gnd'][rail] = {'source': ref, 'vias': len(vias), 'via_xy': [v['xy'] for v in vias],
                            'r_vias_20c_ohm': r_vias, 'in1_spreading': per}
    return out


def loop_copper(repo):
    """Parse loop-resistance.txt: rail copper from the discharge part to each connector (mOhm, 20 C)."""
    out = {}
    for line in (repo / LOOP).read_text().splitlines():
        net = line.split()[0]
        rail = {'P12_OUT': '+12', 'P5_OUT': '+5', 'M12_OUT': '-12'}[net]
        vals = re.findall(r"\(([0-9.]+), '(J\d+)'", line)
        per = {}
        for v, j in vals:
            per.setdefault(j, float(v) * 1e-3)
        out[rail] = {'near': per['J7'] if rail != '-12' else per['J6'], 'J10': per['J10'], 'J11': per['J11']}
    return out


def resistances(geo, loop):
    """Per rail: switch-path resistance (WSL + RDS(on) + pulse-net copper) min/max and bank-side copper per connector."""
    n_wsl = {'+12': 1, '+5': 1, '-12': 3}
    pulse = {'+12': ['P12_DX'], '+5': ['P5_DX'], '-12': ['M12_DX', 'M12_DXA', 'M12_DXB']}
    out = {}
    for rail in ('+12', '+5', '-12'):
        wsl_max = n_wsl[rail] * WSL_OHM * (1 + WSL_TOL + WSL_TCR * (T_HOT - 25))
        wsl_min = n_wsl[rail] * WSL_OHM * (1 - WSL_TOL - WSL_TCR * (25 - T_COLD))
        rds_hot = RDS_4V5_MAX_25C * RDS_HOT_FACTOR
        pcu = sum(geo['pulse_nets'][n]['r_20c_ohm'] for n in pulse[rail])
        gnd = geo['gnd'][rail]
        bank = {c: cu_hot(loop[rail][c] + gnd['in1_spreading'][c]['r_20c_ohm'] + gnd['r_vias_20c_ohm'])
                for c in ('near', 'J10', 'J11')}
        out[rail] = {'switch_min_ohm': wsl_min, 'switch_nom_ohm': n_wsl[rail] * WSL_OHM,
                     'switch_max_ohm': wsl_max + rds_hot + cu_hot(pcu),
                     'parts': {'wsl_max': wsl_max, 'wsl_min': wsl_min, 'rds_hot': rds_hot, 'pulse_cu_hot': cu_hot(pcu)},
                     'bank_side_hot_ohm': bank}
        out[rail]['worst_total_ohm'] = out[rail]['switch_max_ohm'] + max(bank.values())
        out[rail]['worst_increase_pct'] = 100 * (out[rail]['worst_total_ohm'] / out[rail]['switch_nom_ohm'] - 1)
        out[rail]['best_decrease_pct'] = 100 * (1 - wsl_min / out[rail]['switch_nom_ohm'])
    return out


# ---- firing timing ---------------------------------------------------------------------------------------
def t_fire(vinf, tau, vth):
    return math.inf if vth >= vinf else tau * math.log(vinf / (vinf - vth))


def timing():
    v_m12 = 12.37
    def m12(r61, r62, c, vdis, vth):
        vinf = (vdis + v_m12) * r62 / (r61 + r62)
        return t_fire(vinf, r61 * r62 / (r61 + r62) * c, vth), vinf, r61 * r62 / (r61 + r62) * c
    def pos(rdg, c, vdis, vth):
        return t_fire(vdis, rdg * c, vth)
    sim = m12(4.7e3, 47e3, 68e-9 + 885e-12, 4.9, VTH_TYP)
    fit = m12(4.7e3, 47.5e3, 69e-9 + 885e-12, 4.9, VTH_TYP)
    c_lo = 47e-9 * (1 - C44_TOL) + 22e-9 * (1 - C45_TOL) * (1 - X7R_TC) * (1 - X7R_DCBIAS)
    c_hi = 47e-9 * (1 + C44_TOL) + 22e-9 * (1 + C45_TOL) + CISS_MAX
    early = m12(4.7e3 * (1 - R61_TOL), 47.5e3 * (1 + R62_TOL), c_lo, max(DIS_V), VTH_MIN - VTH_HOT_SHIFT)
    late = m12(4.7e3 * (1 + R61_TOL), 47.5e3 * (1 - R62_TOL), c_hi, min(DIS_V), VTH_MAX)
    p_nom = pos(10e3, 22e-9 + 885e-12, 4.9, VTH_TYP)
    cp_lo = 22e-9 * (1 - C45_TOL) * (1 - X7R_TC) * (1 - X7R_DCBIAS * 0.5)
    cp_hi = 22e-9 * (1 + C45_TOL) + CISS_MAX
    p_early = pos(10e3 * (1 - RDG_TOL), cp_lo, max(DIS_V), VTH_MIN - VTH_HOT_SHIFT)
    p_late = pos(10e3 * (1 + RDG_TOL), cp_hi, min(DIS_V), VTH_MAX)
    return {
        'm12_switch': {
            'sets': 'Q55 firing delay (R61 4.7k from DIS_C via Q54, R62 to M12_OUT, CDGN = C44 47 nF C0G + C45 22 nF X7R across gate-source)',
            'sim_47k_68n': {'vinf_v': sim[1], 'tau_us': sim[2] * 1e6, 't_fire_us_at_vth_typ': sim[0] * 1e6},
            'fitted_47k5_69n': {'vinf_v': fit[1], 'tau_us': fit[2] * 1e6, 't_fire_us_at_vth_typ': fit[0] * 1e6},
            'fitted_minus_sim_us': (fit[0] - sim[0]) * 1e6,
            'band_us': [early[0] * 1e6, late[0] * 1e6],
            'band_minus_nominal_us': [(early[0] - fit[0]) * 1e6, (late[0] - fit[0]) * 1e6]},
        'p12_p5_switches': {
            'sets': 'Q51/Q52 firing delay (RDG12/RDG5 10k from DIS_P, CDG12/CDG5 22 nF X7R to GND); unchanged from the sim',
            't_fire_us_at_vth_typ': p_nom * 1e6, 'band_us': [p_early * 1e6, p_late * 1e6],
            'band_minus_nominal_us': [(p_early - p_nom) * 1e6, (p_late - p_nom) * 1e6]}}


# ---- vectorised two-node discharge calculation -----------------------------------------------------------
def run_grid(fd, sq, cases, dt=1e-6, stop=0.1):
    """cases: dict of arrays. Mirrors d2_sequenced.simulate (exact per-step exponential decay, same row logic) with a
    bank-side resistance r_cu between the OSC bank and the board node; the sequencer senses the board node, rows are
    read on the bank (OSC) voltage and, separately, on the board node."""
    N = len(cases['c12'])
    rails = ('+12', '-12', '+5')
    key = {'+12': '12', '-12': 'n', '+5': '5'}
    v = {r: np.full(N, abs(fd.START_V[r])) for r in rails}
    C = {r: cases['c' + key[r]] for r in rails}
    gl = {r: cases['gl' + key[r]] for r in rails}
    rsw = {r: cases['rsw' + key[r]] for r in rails}
    rcu = {r: cases['rcu' + key[r]] for r in rails}
    fire = {r: cases['f' + key[r]] for r in rails}
    H, REL = cases['hold'], cases['release']
    lvl = {r: np.full(N, np.nan) for r in rails}
    rvee = np.zeros(N, bool); haz = np.zeros(N, bool)
    rvee_b = np.zeros(N, bool)
    max_n_after12 = np.zeros(N)            # largest |-12| (bank) once +12 (bank) <= 0.5
    min_n_with12 = np.full(N, np.inf)      # smallest |-12| (bank) while +12 (bank) > 0.5
    prev_onn = np.zeros(N, bool)
    t = 0.0
    while t < stop:
        on12 = t >= fire['+12']; on5 = t >= fire['+5']
        b12 = np.where(on12, v['+12'] * rsw['+12'] / (rsw['+12'] + rcu['+12']), v['+12'])
        # the sequencer senses the -12 board node, which sits below the bank by the switch current x r_cu while the
        # switch conducted in the previous step (ideal thresholds make this chatter about H, a time-averaged hold)
        bn = np.where(prev_onn, v['-12'] * rsw['-12'] / (rsw['-12'] + rcu['-12']), v['-12'])
        absent = {r: v[r] <= fd.LEVEL_V[r] for r in rails}
        held = (bn <= H) & (b12 > REL)
        onn = (t >= fire['-12']) & ~held
        prev_onn = onn
        bn_on = np.where(onn, v['-12'] * rsw['-12'] / (rsw['-12'] + rcu['-12']), v['-12'])
        b5 = np.where(on5, v['+5'] * rsw['+5'] / (rsw['+5'] + rcu['+5']), v['+5'])
        on = {'+12': on12, '-12': onn, '+5': on5}
        for r in rails:
            g = gl[r] + np.where(on[r], 1 / (rsw[r] + rcu[r]), 0.0)
            v[r] = v[r] * np.exp(-g / C[r] * dt)
            hit = np.isnan(lvl[r]) & (v[r] <= fd.LEVEL_V[r])
            lvl[r][hit] = t
        rvee |= (absent['-12'] & (v['+12'] > 0.5)) | (absent['+12'] & (v['-12'] > 6.0))
        rvee_b |= ((bn_on <= 0.6) & (b12 > 0.5)) | ((b12 <= 0.5) & (bn_on > 6.0))
        haz |= (v['+5'] > 0.8) & ((absent['+12'] & (v['-12'] >= 8)) | (absent['-12'] & (v['+12'] >= 8)))
        max_n_after12 = np.where(v['+12'] <= 0.5, np.maximum(max_n_after12, v['-12']), max_n_after12)
        min_n_with12 = np.where(v['+12'] > 0.5, np.minimum(min_n_with12, v['-12']), min_n_with12)
        if not any(np.isnan(lvl[r]).any() for r in rails):
            break
        t += dt
    slow = np.nanmax(np.stack([lvl[r] for r in rails]), axis=0)
    level_ok = ~np.isnan(np.stack([lvl[r] for r in rails])).any(axis=0) & (slow <= 0.1)
    return {'pass': ~rvee & ~haz & level_ok, 'rvee': rvee, 'rvee_board': rvee_b, 'hazard': haz,
            'level_ok': level_ok, 'slowest_s': slow, 'max_n_after12': max_n_after12, 'min_n_with12': min_n_with12,
            'level': lvl}


def build(fd, sq, rcombo, seq, fires, R):
    rows = []
    for bank, caps in fd.banks().items():
        for lbl, corner in sq.load_corners().items():
            for f12, fn, f5 in itertools.product(fires['+12'], fires['-12'], fires['+5']):
                rows.append((caps, corner, f12, fn, f5))
    N = len(rows)
    a = {k: np.empty(N) for k in ('c12', 'cn', 'c5', 'gl12', 'gln', 'gl5', 'f12', 'fn', 'f5')}
    for i, (caps, corner, f12, fn, f5) in enumerate(rows):
        a['c12'][i], a['cn'][i], a['c5'][i] = caps['+12'], caps['-12'], caps['+5']
        for r, k in (('+12', 'gl12'), ('-12', 'gln'), ('+5', 'gl5')):
            x = sq.load_ohm(r, corner[r]); a[k][i] = 1 / x if x else 0.0
        a['f12'][i], a['fn'][i], a['f5'][i] = f12, fn, f5
    for r, k in (('+12', '12'), ('-12', 'n'), ('+5', '5')):
        state = rcombo[r]
        if state == 'nom':
            a['rsw' + k] = np.full(N, R[r]['switch_nom_ohm']); a['rcu' + k] = np.zeros(N)
        elif state == 'fast':
            a['rsw' + k] = np.full(N, R[r]['switch_min_ohm']); a['rcu' + k] = np.zeros(N)
        else:  # slow: hot maxima and the far (J11) bank-side copper
            a['rsw' + k] = np.full(N, R[r]['switch_max_ohm']); a['rcu' + k] = np.full(N, R[r]['bank_side_hot_ohm']['J11'])
    a['hold'] = np.full(N, seq[0]); a['release'] = np.full(N, seq[1])
    return a, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
    ap.add_argument('--output', type=Path, default=HERE / 'sensitivity.json')
    args = ap.parse_args()
    repo = args.repo
    sys.path.insert(0, str(repo / SIM))
    import d2_fast_discharge as fd
    import d2_sequenced as sq

    inputs = {p: sha(repo / p) for p in (PCB, SPEC, LOOP, f'{SIM}/d2_sequenced.py', f'{SIM}/d2_fast_discharge.py',
                                         f'{SIM}/d2-sequenced-criteria.md', f'{SIM}/d2-sequencer-design.md', *SIM_JSON)}
    spec = (repo / SPEC).read_text()
    for needle in ("rprop('R62', '47.5k 0.1%', 'M12_DG', 'M12_OUT')", "cprop('CDGNA', '47nF C0G', 'M12_DG', 'M12_OUT')",
                   "two('CDGNB', 'C22N', 'M12_DG', 'M12_OUT')", "two('R61', 'R4K7', 'M12_DGX', 'M12_DG')",
                   "two('RXN2', 'WSL', 'M12_DXA', 'M12_DXB')", "rprop('RDG12', '10k 1%', 'DIS_P', 'P12_DG')"):
        assert needle in spec, needle
    geo = geometry(repo)
    loop = loop_copper(repo)
    R = resistances(geo, loop)
    tim = timing()

    # validation against the published calc (nominal R, no copper, behavioural thresholds, original fire grid)
    base_seq = (sq.HOLD_V, sq.RELEASE_V)
    a, rows = build(fd, sq, {'+12': 'nom', '-12': 'nom', '+5': 'nom'}, base_seq, sq.FIRE_S, R)
    res = run_grid(fd, sq, a)
    validation = {'cases': len(rows), 'failing': int((~res['pass']).sum()),
                  'slowest_s': float(res['slowest_s'].max()), 'published_failing': 0, 'published_slowest_s': 0.000961}
    rng = np.random.default_rng(0)
    mism = 0
    for i in rng.choice(len(rows), 60, replace=False):
        caps, corner, f12, fn, f5 = rows[i]
        ref = sq.simulate(caps, corner, {'+12': f12, '-12': fn, '+5': f5})
        mism += int(ref['pass'] != bool(res['pass'][i]) or any(
            abs((ref['level_s'][r] or 0) - res['level'][r][i]) > 2e-6 for r in ('+12', '-12', '+5')))
    validation['spot_check_vs_d2_sequenced_simulate'] = {'samples': 60, 'mismatches': mism}

    # fire grid widened by the computed tolerance bands (additive shift about the calc's central values)
    dm = tim['m12_switch']['band_minus_nominal_us']; dp = tim['p12_p5_switches']['band_minus_nominal_us']
    on = [min(c['discharge_onset_ms'] for c in json.load(open(repo / f)).get('cases', {}).values() if c.get('status') == 'COMPLETE') for f in SIM_JSON]
    on_hi = [max(c['discharge_onset_ms'] for c in json.load(open(repo / f)).get('cases', {}).values() if c.get('status') == 'COMPLETE') for f in SIM_JSON]
    sim_onset_us = (min(on) * 1e3, max(on_hi) * 1e3)
    grids = {
        'pre-registered (d2_sequenced.FIRE_S)': sq.FIRE_S,
        'tolerance band (guaranteed VGS(th), C/R tolerance, PA X7R loss)': {
            '+12': tuple(max(0, (155 + d) * 1e-6) for d in (dp[0], 0, dp[1])),
            '+5': tuple(max(0, (163 + d) * 1e-6) for d in (dp[0], 0, dp[1])),
            '-12': tuple(x * 1e-6 for x in (sim_onset_us[0] + dm[0], sim_onset_us[0], sim_onset_us[1] + tim['m12_switch']['fitted_minus_sim_us'], sim_onset_us[1] + dm[1])) }}
    seqs = {'behavioural (3.0, 0.3)': (3.0, 0.3), 'hlrl (3.5, 0.5)': (3.5, 0.5), 'hlrh (3.5, 1.5)': (3.5, 1.5),
            'hhrl (5.6, 0.5)': (5.6, 0.5), 'hhrh (5.6, 1.5)': (5.6, 1.5)}
    rcombos = {'nominal': {'+12': 'nom', '-12': 'nom', '+5': 'nom'}}
    for s12, sn, s5 in itertools.product(('fast', 'slow'), repeat=3):
        rcombos[f'+12 {s12} / -12 {sn} / +5 {s5}'] = {'+12': s12, '-12': sn, '+5': s5}
    table = {}
    for gname, fires in grids.items():
     table[gname] = {'fire_grid_us': {k: [round(x * 1e6, 2) for x in v] for k, v in fires.items()}}
     for sname, seq in seqs.items():
        table[gname][sname] = {}
        for cname, rc in rcombos.items():
            a, rows = build(fd, sq, rc, seq, fires, R)
            r = run_grid(fd, sq, a)
            fail = ~r['pass']
            table[gname][sname][cname] = {
                'cases': len(rows), 'failing': int(fail.sum()), 'rvee_fail': int(r['rvee'].sum()),
                'rvee_board_node_fail': int(r['rvee_board'].sum()), 'hazard_fail': int(r['hazard'].sum()),
                'level_fail': int((~r['level_ok']).sum()), 'slowest_level_ms': float(np.nanmax(r['slowest_s']) * 1e3),
                'max_abs_m12_once_p12_absent_v': float(r['max_n_after12'].max()),
                'min_abs_m12_while_p12_present_v': float(r['min_n_with12'].min())}
            print(gname[:8], sname, cname, table[gname][sname][cname]['failing'], file=sys.stderr)
    out = {'record': 'D2 bounded sensitivity (CALCULATED; ideal-threshold switches; resistive-load ASSUMPTION; '
                     'two-node rail model with bank-side copper; independent review for PR #307)',
           'inputs_sha256': inputs,
           'assumptions': {'board_hot_c': T_HOT, 'board_cold_c': T_COLD, 'cu_tcr_per_k': CU_TCR, 'via_plating_m': PLATING_T,
                           'in1_spreading_factor_PA': SPREAD_FACTOR, 'rds_on_hot_factor_PA': RDS_HOT_FACTOR,
                           'x7r_tc_class': X7R_TC, 'x7r_dc_bias_PA': X7R_DCBIAS, 'vth_hot_shift_PA_v': VTH_HOT_SHIFT,
                           'hold_up_drive_v_PA': DIS_V},
           'geometry': geo, 'loop_copper_20c_ohm': loop, 'resistance_corners': R, 'timing': tim,
           'sim_discharge_onset_us': sim_onset_us,
           'validation': validation, 'results': table}
    args.output.write_text(json.dumps(out, indent=1, default=float) + '\n')
    print(json.dumps(validation))


if __name__ == '__main__':
    main()
