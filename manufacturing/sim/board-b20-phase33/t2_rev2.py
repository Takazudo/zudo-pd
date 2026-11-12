"""D1 T2 rev 2 on -12 V: the (a2) output-limiter topology with sourced diodes, under the revised rules.

Attempt 1 (t2_clamp.py, d1-t2-criteria.md) is unchanged and stays FAILED. Rev 2 is option (a2) of
/mnt/project-files/d1/t2-ways-forward-20261112.md, admitted by owner decision for simulation evaluation only, with
the window switch moved to the inverting input (d1-t2-a2-dc-checks-20261112.md). Against attempt 1 it:
- limits t2o to about +VF through R_O and D_L, keeping XT2B's feedback at the op-amp output (t2a);
- connects DT2C and R_C to TRK12N_FB permanently (no BT2G), so no switch sits on the summing node;
- forces XT2B's output high outside the RAMP reset window by pulling t2m toward M12_PRE through R_W;
- uses datasheet-traced .models for DT2C, DT2K and D_L, with each guaranteed reverse leakage as an explicit element;
- judges rules 6 and 9 as revised (rules_revision.py) and keeps a labelled matched-variant track for ABORTED cases;
- adds VF-spread, DT2C leakage-ladder and hot-leakage cases.
The earlier rev 2 form (option 1, delayed connection) was never pre-registered and is in Git history only.

Nothing here is a design change. Decks refuse to build until every diode slot names sourced rows and the hot-case
temperature is recorded (HOT_T_C).

usage (after extract_reference.py prepare / run / identity):
  t2_rev2.py prepare WORK --manifest PATH
  for every LABEL in LABEL_ORDER: run_ladder.py WORK/t2/LABEL/tracking $(t2_rev2.py pending WORK LABEL) --original-only
  t2_rev2.py analyze WORK --output PATH
  for STEP in 1 2: for every 'LABEL NAMES' line of t2_rev2.py variant-plan WORK STEP: run_ladder.py ... --original-only
  t2_rev2.py variant-analyze WORK --output PATH
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

from extract_reference import attempt_dir, derive_decks, single_run
import gap_sensitivity as gap
import rules_revision as rules
import t2_clamp as t1

CRITERIA = 'd1-t2-rev2-criteria.md'
SCOPE = 'T2 rev 2 (a2 output limiter, sourced diodes) on -12 V under the revised rules; model only, not adopted'

# ---------------------------------------------------------------- diodes (every value traced to a datasheet row)
MODEL_PARAMETERS = ('IS', 'N', 'RS', 'CJO', 'VJ', 'M', 'BV', 'IBV')
LEAK_KNEE_V = 0.05             # leakage reaches its guaranteed maximum within 0.05 V of reverse bias (conservative)
VT_25C_V = 0.025693            # kT/q at 25 C, the temperature of every retained row
_N = 0.075 / (VT_25C_V * math.log(10))      # 75 mV per decade between the typical 1 uA and 10 uA VF rows
_IS = 1e-6 / math.exp(0.530 / (_N * VT_25C_V))
FJH1100 = {
    'mpn': 'FJH1100', 'manufacturer': 'onsemi (Fairchild)',
    'source': ('onsemi FJH1100 Rev. B1, sha256 1301249ba54770d82b6a1ec1b7d9d4d832a4fc442ee4f55b99ab6c8835bf4d8e; '
               'staged evidence /mnt/project-files/d1/fjh1100-evidence/fjh1100-evidence.json (STAGED_OUTSIDE_INVENTORY: '
               'no LCSC ID, so no repo owner bundle until the part is a fitted candidate)'),
    'model': {'IS': _IS, 'N': _N, 'RS': (0.995 - _N * VT_25C_V * math.log(50e-3 / _IS)) / 50e-3,
              'CJO': 2.0e-12, 'VJ': 0.7, 'M': 0, 'BV': 30, 'IBV': 5e-6},
    'ir_max_a': 3.0e-12, 'ir_rows': ((5.0, 3.0e-12), (15.0, 10e-12)), 'reverse_rating_v': 15,
    'rows': {'IS': 'fact-fjh1100-vf TYPICAL 530 mV at 1 uA (with N)',
             'N': 'fact-fjh1100-vf TYPICAL 530 mV at 1 uA and 605 mV at 10 uA',
             'RS': 'fact-fjh1100-vf TYPICAL 995 mV at 50 mA (no effect below 1 mA)',
             'CJO': 'fact-fjh1100-ct-0v MAX 2.0 pF at VR 0 V; M = 0 holds it at every bias (worst case)',
             'VJ': 'no effect with M = 0', 'M': 'worst case: constant at the 0 V maximum',
             'BV': 'fact-fjh1100-bv MIN 30 V at 5 uA (a test row, not a rating; the rating is 15 V working)',
             'IBV': 'fact-fjh1100-bv test current 5 uA',
             'ir_max_a': 'fact-fjh1100-ir-5v MAX 3.0 pA at VR 5 V, 25 C, applied below 5 V (PROJECT inference)',
             'ir_rows': 'fact-fjh1100-ir-5v and fact-fjh1100-ir-15v: 3.0 pA up to 5 V, 10 pA from 5 to 15 V',
             'reverse_rating_v': 'fact-fjh1100-wiv working inverse voltage 15 V, absolute maximum'},
}
_KN = 0.100 / (VT_25C_V * math.log(10))     # 100 mV per decade between the 1 mA and 10 mA VF maxima
_KIS = 1e-3 / math.exp(0.900 / (_KN * VT_25C_V))
BAS116L = {
    'mpn': 'BAS116LT1G', 'manufacturer': 'onsemi',
    'source': ('onsemi BAS116LT1/D Rev. 14, sha256 ce1244d979892cbc1b4b1fffc99568f098a5d36c3e4c20a431952b0b066f2db2; '
               'staged evidence /mnt/project-files/d1/dt2k-evidence/dt2k-low-leakage-evidence.json '
               '(STAGED_OUTSIDE_INVENTORY: LCSC ID not established)'),
    'model': {'IS': _KIS, 'N': _KN, 'RS': (1.100 - _KN * VT_25C_V * math.log(50e-3 / _KIS)) / 50e-3,
              'CJO': 2.0e-12, 'VJ': 0.7, 'M': 0, 'BV': 75, 'IBV': 100e-6},
    'ir_max_a': 5.0e-9, 'ir_rows': ((75.0, 5.0e-9),), 'ir_hot_max_a': 80e-9, 'reverse_rating_v': 75,
    'rows': {'IS': 'VF MAX 900 mV at 1 mA (with N); extrapolated to uA (PROJECT inference: no uA row)',
             'N': 'VF MAX 900 mV at 1 mA and 1000 mV at 10 mA',
             'RS': 'VF MAX 1100 mV at 50 mA (no effect below 1 mA)',
             'CJO': 'CD MAX 2 pF at VR 0 V, 1 MHz; M = 0 holds it at every bias',
             'VJ': 'no effect with M = 0', 'M': 'worst case: constant at the 0 V maximum',
             'BV': 'V(BR) MIN 75 V at 100 uA', 'IBV': 'V(BR) test current 100 uA',
             'ir_max_a': 'IR MAX 5.0 nA at VR 75 V, 25 C, applied at <= 1.3 V (PROJECT inference)',
             'ir_rows': 'IR MAX 5.0 nA at VR 75 V, 25 C',
             'ir_hot_max_a': 'IR MAX 80 nA at VR 75 V, TJ 150 C',
             'reverse_rating_v': 'VR continuous reverse voltage 75 V, maximum ratings'},
}
# DT2K needs a stated reverse rating >= 27.5 V (1.5 x the 18.34 V rail-bounded worst case) (owner decision
# 2026-11-12); FJH1100 (15 V) does not qualify. D_L needs no low leakage; FJH1100 stands in for it, with the VF
# spread below because its low-current VF is typical only.
DIODES = {'DT2C': FJH1100, 'DT2K': BAS116L, 'DL': FJH1100}
MODEL_NAME = {'DT2C': 'DT2CX', 'DT2K': 'DT2KX', 'DL': 'DT2LX'}
RATING_MIN_V = {'DT2C': 10.6, 'DT2K': 27.5, 'DL': 12.8}   # d1-t2-a2-dc-checks-20261112.md bounds (DT2K with 1.5x)

# ---------------------------------------------------------------- (a2) values
VALUES = {
    'R_C': ('402k', 'clamp injection resistor into TRK12N_FB, +/-1 %; R_C + R_O = 502k keeps attempt 1 k / R'),
    'R_O': ('100k', 'output limiter resistor, XT2B output to t2o, +/-1 %'),
    'R_W': ('100k', 'window pull of t2m toward M12_PRE, +/-1 %'),
}
R_C_OHM = 402e3
OPERATING_CURRENT_A = {'DL': 45e-6, 'DT2K': 0.5e-6, 'DT2C': 1e-6}   # the points each VF spread is stated at
# D_L: typical 0.654 V at 45 uA; low = typical - 0.2 V (PROJECT, -2 mV/C over 100 K); high = the 50 mA maximum.
# DT2C: typical 0.530 V at 1 uA (the clamp current); same low and high rules.
# DT2K: the model's 0.57 V at 0.5 uA (extrapolated from the 1 mA / 10 mA maxima) -/+ 0.15 V (PROJECT inference).
VF_SPREAD_V = {'vflo': ('DL', 0.46), 'vfhi': ('DL', 1.05), 'cvflo': ('DT2C', 0.33), 'cvfhi': ('DT2C', 1.05),
               'kvflo': ('DT2K', 0.42), 'kvfhi': ('DT2K', 0.72)}
# Outside the RAMP reset window: the complement of the deck's own reset shape (t2_clamp.CLAMP_GATE).
WINDOW_GATE = '0.5*(1-tanh((v(ennd)-1.0)*8))'

# ---------------------------------------------------------------- hot leakage (PROJECT inference)
HOT_DOUBLING_C = 7.0           # FJH1100: IR doubles every 7 C from the 25 C maximum (owner-accepted, conservative)
HOT_T_C = None                 # the board maximum operating temperature: not stated in the repo; owner to supply
IR_LADDER_A = {'ir1n': ('DT2C', 1e-9), 'ir2n': ('DT2C', 2e-9),     # DT2C only: the rule 6(b) crossing
               'k80n': ('DT2K', 80e-9), 'k1u': ('DT2K', 1e-6)}     # DT2K only: 150 C guaranteed row, and beyond


def hot_factor(t_c=None):
    t_c = HOT_T_C if t_c is None else t_c
    if t_c is None:
        raise ValueError('hot case: the board maximum operating temperature is not recorded (HOT_T_C)')
    return 2 ** ((t_c - 25.0) / HOT_DOUBLING_C)


def hot_ir(role, t_c=None):
    """FJH1100: the 7 C doubling. BAS116L: the guaranteed 150 C row, held flat below 150 C (monotonic in T)."""
    return hot_rows(role, t_c)[0][1]


def hot_rows(role, t_c=None):
    d = DIODES[role]
    factor = hot_factor(t_c)      # raises when the board temperature is not recorded, for every role
    if 'ir_hot_max_a' in d:
        return ((d['reverse_rating_v'], d['ir_hot_max_a']),)
    return tuple((v, a * factor) for v, a in d['ir_rows'])


def temperature_for(ir_a, ir25_a=FJH1100['ir_max_a']):
    """The temperature at which the scaled IR reaches ir_a."""
    return 25.0 + HOT_DOUBLING_C * math.log2(ir_a / ir25_a)


def require_diodes():
    for role, d in DIODES.items():
        if d is None:
            raise ValueError(f'rev 2 {role} not sourced: no part with a stated rating covers its requirement')
        missing = [p for p in MODEL_PARAMETERS + ('ir_max_a', 'reverse_rating_v')
                   if p not in d['rows'] or (p not in d['model'] and p not in d)]
        if missing:
            raise ValueError(f'rev 2 {role}: untraced parameters {missing}')
        if d['reverse_rating_v'] < RATING_MIN_V[role]:
            raise ValueError(f'rev 2 {role}: {d["mpn"]} rated {d["reverse_rating_v"]} V < {RATING_MIN_V[role]} V')
        if 'ir_rows' not in d or 'ir_rows' not in d['rows']:
            raise ValueError(f'rev 2 {role}: untraced parameters [\'ir_rows\']')
    return DIODES


def model_line(role, vf=None):
    """vf moves the VF at the role's operating current by IS alone (a spread case); every other parameter is traced."""
    d = DIODES[role]
    params = dict(d['model'])
    note = ''
    if vf is not None:
        i = OPERATING_CURRENT_A[role]
        params['IS'] = i / math.exp(vf / (params['N'] * VT_25C_V))
        note = f', VF {vf:g} V at {i:g} A (spread case)'
    return (f'.model {MODEL_NAME[role]} D(' + ' '.join(f'{p}={params[p]:g}' for p in MODEL_PARAMETERS) + ')'
            + f'  ; {d["mpn"]}{note}')


def leak(name, cathode, anode, rows):
    """The guaranteed maximum reverse leakage, cathode to anode: each row's maximum from the previous row's voltage
    up to its own (the first row from 0 V), so a bias above a row's test voltage takes the next row."""
    if isinstance(rows, (int, float)):
        rows = ((float('inf'), rows),)
    vr = f'v({cathode},{anode})'
    terms = [f'{rows[0][1]:g}*tanh(max({vr},0)/{LEAK_KNEE_V})']
    for (v_prev, a_prev), (_, a) in zip(rows, rows[1:]):
        terms.append(f'{a - a_prev:g}*0.5*(1+tanh(({vr}-{v_prev:g})/{LEAK_KNEE_V}))')
    return f'{name} {cathode} {anode} I=' + '+'.join(terms)


def t2_block(inert=False, ir=None, vf=None):
    """The (a2) candidate. inert returns R_C to GND instead of TRK12N_FB; everything else is identical.
    ir overrides a role's leakage ({role: A}); vf is (role, V) for one VF-spread case."""
    require_diodes()
    v = t1.VALUES
    ir = {**{role: d['ir_rows'] for role, d in DIODES.items()}, **(ir or {})}
    vf = dict([vf]) if vf else {}
    ir = {role: ((d['reverse_rating_v'], ir[role]),) if isinstance(ir[role], float) else ir[role]
          for role, d in DIODES.items()}
    return [
        f'* T2 rev 2 (a2) output limiter on -12 V: candidate under evaluation, not a board part ({CRITERIA})'
        + (' [INERT CONTROL: R_C returned to GND]' if inert else ''),
        'VT2N t2n m12_pre 0',
        'DT2K m12_drv t2k DT2KX',
        t1.switch('BT2K', 't2k', 't2h', t1.CAPTURE_GATE),
        f"CT2H t2h m12_pre {v['C_H'][0]}",
        f"RT2B t2h m12_pre {v['R_B'][0]}",
        t1.switch('BT2R', 't2h', 'm12_pre', t1.RESET_GATE),
        'XT2A t2h t2hb p5sup t2n t2hb OPAx187',
        f"RT2P1 m12_drv t2p {v['R_1'][0]}",
        f"RT2P2 t2p {v['V_R'][0]} {v['R_2'][0]}",
        f"RT2M1 t2hb t2m {v['R_1'][0]}",
        f"RT2M2 t2m t2a {v['R_2'][0]}",
        'XT2B t2p t2m p5sup t2n t2a OPAx187',
        f"RT2O t2a t2o {VALUES['R_O'][0]}",
        'DT2L t2o t2l DT2LX',
        'VT2L t2l 0 0',
        'DT2C t2c t2o DT2CX',
        f"RT2C t2c t2g {VALUES['R_C'][0]}",
        'VT2G t2g 0 0' if inert else 'VT2G t2g trk12n_fb 0',
        f"RT2W t2m t2w {VALUES['R_W'][0]}",
        t1.switch('BT2W', 't2w', 'm12_pre', WINDOW_GATE),
        model_line('DT2C', vf.get('DT2C')), model_line('DT2K', vf.get('DT2K')), model_line('DL', vf.get('DL')),
        leak('BT2CL', 't2o', 't2c', ir['DT2C']),
        leak('BT2KL', 't2k', 'm12_drv', ir['DT2K']),
        leak('BT2LL', 't2l', 't2o', ir['DL']),
    ]


A2_VECTORS = ('t2a', 't2o', 't2p', 't2m', 't2k', 'm12_drv', 'p5sup', 'm12_pre')
A2_CURRENTS = ('VT2L', 'VT2G')
A2_COLUMNS = A2_VECTORS + tuple(f'i_{c}' for c in A2_CURRENTS)


def a2_line(name):
    return (f'wrdata {name}-a2.txt ' + ' '.join(f'v({x})' for x in A2_VECTORS) + ' '
            + ' '.join(f'i({c})' for c in A2_CURRENTS))


# ---------------------------------------------------------------- cases
# label -> (block keyword arguments, deck names); every extra case compares against the pinned reference pair.
EXTRA = {
    **{label: ({'vf': spread}, ('nom', 'adv')) for label, spread in VF_SPREAD_V.items()},
    **{label: ({'ir': dict([point])}, ('adv',)) for label, point in IR_LADDER_A.items()},
    'hot': ({'ir': None}, ('nom', 'adv')),     # every role at hot_ir(), filled when the decks are built
}
LABEL_ORDER = t1.LABEL_ORDER + tuple(EXTRA)
INFORMATIONAL = ('ir1n', 'ir2n', 'k1u')   # locating only: reported, never part of the candidate verdict
REQUIRED = tuple(label for label in EXTRA if label not in INFORMATIONAL + ('hot',))


combine = t1.combine_rows


def block_for(label):
    kw = dict(EXTRA[label][0])
    if label == 'hot':
        kw['ir'] = {role: hot_rows(role) for role in DIODES}
    return lambda inert=False: t2_block(inert, **kw)


def derive_cases():
    executed = {k: v['executed'] for k, v in derive_decks().items()}
    cases = t1.derive_cases(t2_block, output=a2_line)
    for label, (_, names) in EXTRA.items():
        block = block_for(label)
        cases[label] = {n: t1.with_t2(t1.no_load(executed[n], n), n, block=block, output=a2_line) for n in names}
    return cases


def prepare(work):
    return t1.prepare(work, scope=SCOPE, criteria=CRITERIA, cases=derive_cases())


def pending(work, label):
    if label in t1.LABEL_ORDER:
        return t1.pending(work, label)
    return list(EXTRA[label][1]) if t1.control_gate(work)['verdict'] == 'REPRODUCED' else []


# ---------------------------------------------------------------- (a2) measurements (reported beside the rules)
VCM_LOW_BELOW_V = 0.1          # fact-c2863562-vcm: (V-) - 0.1 V (retained only for VS 4.5 to < 8 V)
VCM_HIGH_BELOW_V = 2.0         # fact-c2863562-vcm: (V+) - 2 V
INPUT_ABSMAX_V = 0.5           # fact-c2863562-supply-absmax: inputs within the rails +/- 0.5 V
RUNNING_WINDOW_S = (200e-3, 235e-3)
INPUT_WINDOW_S = (20e-3, 235e-3)   # rails settled (P5_SUP ramps to 2 ms) and before the 240 ms disable


def a2_record(run, name):
    times, series = gap.columns(attempt_dir(run, name) / f'{name}-a2.txt', len(A2_COLUMNS))
    return times, dict(zip(A2_COLUMNS, series))


def a2_metrics(times, s, t2=None, input_window=INPUT_WINDOW_S, running=RUNNING_WINDOW_S):
    """Limiter current, XT2B input range against the retained OPA2187 rows, and each diode's reverse-voltage peak."""
    m = {'limiter_current_disabled_a': gap.mean_between(times, s['i_VT2L'], *t1.DISABLED_HOLD_WINDOW_S),
         't2o_enable_window_max_v': gap.extremes(times, s['t2o'], *gap.ENABLE_WINDOW_S)[1]}
    if running and times[-1] >= running[1]:
        m['limiter_current_running_a'] = gap.mean_between(times, s['i_VT2L'], *running)
    span = [i for i, t in enumerate(times) if input_window[0] <= t <= input_window[1]]
    low = min(s[x][i] - s['m12_pre'][i] for x in ('t2p', 't2m') for i in span)
    high = max(s[x][i] - s['p5sup'][i] for x in ('t2p', 't2m') for i in span)
    m['xt2b_input_above_v_minus_min_v'] = low
    m['xt2b_input_relative_to_v_plus_max_v'] = high
    m['xt2b_inputs_within_retained_vcm'] = low >= -VCM_LOW_BELOW_V and high <= -VCM_HIGH_BELOW_V
    m['xt2b_inputs_within_absmax'] = low >= -INPUT_ABSMAX_V and high <= INPUT_ABSMAX_V
    m['dt2k_reverse_max_v'] = max(k - d for k, d in zip(s['t2k'], s['m12_drv']))
    m['dl_reverse_max_v'] = -min(s['t2o'])
    if t2 is not None:
        m['dt2c_reverse_max_v'] = max(o - c for o, c in zip(t2['t2o'], t2['t2c']))
    m['reverse_within_leakage_rows'] = {
        role: m[key] <= DIODES[role]['ir_rows'][-1][0]
        for role, key in (('DT2C', 'dt2c_reverse_max_v'), ('DT2K', 'dt2k_reverse_max_v'), ('DL', 'dl_reverse_max_v'))
        if key in m}
    m['reverse_within_rating'] = {
        role: m[key] <= DIODES[role]['reverse_rating_v']
        for role, key in (('DT2C', 'dt2c_reverse_max_v'), ('DT2K', 'dt2k_reverse_max_v'), ('DL', 'dl_reverse_max_v'))
        if key in m and DIODES[role] is not None}
    return m


def rule6b_margin(detail):
    """Distance to the revised rule 6(b) bound; negative means the bound is exceeded."""
    tol = detail['enable_edge_tolerance_v']
    return min(tol['minimum'] - detail['below_baseline_minimum_v'], tol['maximum'] - detail['above_baseline_maximum_v'])


def failure_ir(points):
    """DT2C IR where the rule 6(b) margin reaches zero: a straight line through the DT2C-only adv points."""
    pts = sorted(points)
    if len(pts) < 2:
        return None
    n = len(pts)
    xm, ym = sum(x for x, _ in pts) / n, sum(y for _, y in pts) / n
    sxx = sum((x - xm) ** 2 for x, _ in pts)
    slope = sum((x - xm) * (y - ym) for x, y in pts) / sxx if sxx else 0.0
    if slope >= 0:
        return None
    return xm - ym / slope


def sourced_dt2c_ir(a2):
    """The DT2C leakage the sourced deck applied: the row covering its measured reverse peak (3 pA up to 5 V)."""
    peak = a2.get('dt2c_reverse_max_v') if isinstance(a2, dict) else None
    rows = DIODES['DT2C']['ir_rows']
    if peak is None:
        return rows[-1][1]            # unknown bias: the larger row, so the crossing temperature is not overstated
    return next((a for v, a in rows if peak <= v), rows[-1][1])


def a2_case(work, base_run, label, name):
    row = t1.no_load_case(work, base_run, label, name, rules.judge, baseline=t1.NO_LOAD_T2.get((label, name),
                          ('run', name)), r_c_ohm=R_C_OHM, detail=rules.detail)
    if row.get('status') == 'COMPLETE':
        try:
            run = t1.status(work, label, name)['run']
            times, s = a2_record(run, name)
            _, t2 = t1.t2_record(run, name)
            row['a2'] = a2_metrics(times, s, t2)
            row['rule6b_margin_v'] = rule6b_margin(row['rule_detail'])
        except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
            # Reported quantities only: an unreadable a2 output never changes the judged verdict.
            row['a2'] = f'NOT EVALUATED: {type(error).__name__}: {error}'
    return row


def loaded_a2(work, name):
    state = t1.status(work, 't2load', name)
    if state['status'] != 'COMPLETE':
        return None
    try:
        times, s = a2_record(state['run'], name)
        _, t2 = t1.t2_record(state['run'], name)
        startup = t1.LOADED_WINDOWS[name][0]       # the loaded decks disable at 150 ms (reR6, reR20)
        return a2_metrics(times, s, t2, input_window=(INPUT_WINDOW_S[0], startup[1]),
                          running=RUNNING_WINDOW_S if name == 'nomR' else None)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        return f'NOT EVALUATED: {type(error).__name__}: {error}'


def analyze(work):
    work = Path(work)
    out = t1.analyze(work, judge=rules.judge, scope=SCOPE, criteria=CRITERIA, r_c_ohm=R_C_OHM, detail=rules.detail,
                     row=a2_case)
    out['rules'] = 'rules 1-9 as revised (d1-rules-revision-20261112.md); 10-14 and L1-L4 unchanged'
    if out['t2'].get('verdict') == 'NOT EVALUATED' and 'no_load' not in out['t2']:
        return out
    base_run = single_run(work)
    for name, row in out['t2']['loaded'].items():
        row['a2'] = loaded_a2(work, name)
    extra = {f'{label}/{n}': a2_case(work, base_run, label, n) for label, (_, names) in EXTRA.items() for n in names}
    sourced = out['t2']['no_load'].get('t2/adv', {})
    ladder = [(sourced_dt2c_ir(sourced.get('a2')), sourced.get('rule6b_margin_v'))]
    ladder += [(ir, extra[f'{label}/adv'].get('rule6b_margin_v'))
               for label, (role, ir) in IR_LADDER_A.items() if role == 'DT2C']
    points = [(x, y) for x, y in ladder if y is not None]
    crossing = failure_ir(points)
    sourced = out['t2']['verdict']
    required = [extra[f'{label}/{n}'] for label in REQUIRED for n in EXTRA[label][1]]
    out['candidate'] = {
        'verdict': combine([{'passes': {'PASS': True, 'FAIL': False}.get(sourced)}] + required),
        'basis': ('sourced 25 C cases (t2 verdict) plus the VF-spread and DT2K 80 nA cases; the hot DT2C case is '
                  'judged separately; ir1n / ir2n / k1u are informational'),
        'required': {f'{label}/{n}': extra[f'{label}/{n}'].get('passes') for label in REQUIRED for n in EXTRA[label][1]}}
    out['extra'] = {
        'cases': extra, 'informational': list(INFORMATIONAL),
        'hot': {'temperature_c': HOT_T_C, 'ir_a': {role: hot_ir(role) for role in DIODES} if HOT_T_C is not None else None,
                'basis': (f'FJH1100: IR doubling every {HOT_DOUBLING_C:g} C (PROJECT inference, no hot row); '
                          'BAS116L: the guaranteed 80 nA TJ 150 C row held flat below 150 C (monotonic, inference)'),
                'verdict': combine([extra[f'hot/{n}'] for n in EXTRA['hot'][1]])},
        'dt2c_failure_ir': {'points': points, 'crossing_a': crossing,
                            'crossing_temperature_c': (temperature_for(crossing, ladder[0][0])
                                                       if crossing and crossing > 0 else None),
                            'note': (None if crossing is None or crossing > 0 else
                                     'non-positive crossing: the sourced case already sits at or beyond the bound'),
                            'basis': 'linear fit of the rule 6(b) margin over the DT2C-only adv cases'},
        'dt2k_ladder': {f'{label}/adv': {'ir_a': ir, 'passes': extra[f'{label}/adv'].get('passes'),
                                         'role': 'informational' if label in INFORMATIONAL else 'required'}
                        for label, (role, ir) in IR_LADDER_A.items() if role == 'DT2K'},
        'limitations': [
            'FJH1100 (DT2C, D_L) over-temperature IR is UNSOURCED; this blocks adoption until sourced or bench-measured',
            'BAS116L (DT2K): IR assumed monotonic in temperature, so the 150 C row bounds lower temperatures (inference)',
            'BAS116L (DT2K): the 75 V IR rows applied at <= 1.3 V reverse bias (inference)',
            'VF below 1 mA is typical (FJH1100) or extrapolated from maxima (BAS116L); each role has a VF-spread pair',
            'neither diode has an LCSC ID; both are staged outside the inventory, not owner bundles'],
    }
    return out


# ---------------------------------------------------------------- matched-variant track (labelled, never PASS/FAIL)
VARIANTS = (('abstol', ('abstol=1e-9', 'abstol=1e-8')), ('rshunt', ('rshunt=1e10', 'rshunt=1e9')))
VARIANT_VERDICT = 'VARIANT-EVALUATED'
CROSS_CHECK = ('t2', 'adv')    # a case that completes pinned, rerun under each variant used
# case -> its comparison baseline; 'run' is the pinned identity pair, 'base' the loaded baselines
BASELINE = {**{(lbl, n): b for (lbl, n), b in t1.NO_LOAD_T2.items()},
            **{(lbl, 'nom'): ('run', 'nom') for lbl in t1.CORNER_CASES},
            **{('t2load', n): ('base', n) for n in t1.LOADED},
            **{(lbl, n): ('run', n) for lbl, (_, names) in EXTRA.items() for n in names}}


def apply_variant(text, variant):
    old, new = dict(VARIANTS)[variant]
    return text.replace(old, new) if text.count(old) == 1 else None


def pinned_decks():
    executed = {k: v['executed'] for k, v in derive_decks().items()}
    decks = {('run', 'nom'): executed['nom'], ('run', 'adv'): executed['adv']}
    for label, names in derive_cases().items():
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
    """Candidate cases whose own pinned run, or any pinned run in their baseline chain, ABORTED."""
    return [case for case in BASELINE if any(pinned_status(work, *c)['status'] == 'ABORTED' for c in unit(case))]


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
            row['rules'], row['detail'] = t1.judge_loaded(t1.plain_record(brun, name),
                                                          t1.case_record(run, name, t2=True, loaded=True), name, R_C_OHM)
        else:
            # The pinned judging itself, against the variant baseline; its PASS/FAIL key is renamed, never a verdict.
            judged = t1.no_load_case(work, None, vlabel(variant, label), name, rules.judge,
                                     baseline=(vlabel(variant, base[0]), base[1]), r_c_ohm=R_C_OHM,
                                     detail=rules.detail)
            if judged.get('status') != 'COMPLETE':
                return {**row, 'verdict': 'NOT EVALUATED', 'reason': judged.get('reason', judged.get('status'))}
            judged['all_rules_hold'] = judged.pop('passes')
            row.update({k: v for k, v in judged.items() if k != 'status'})
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        return {**row, 'verdict': 'NOT EVALUATED', 'reason': f'{type(error).__name__}: {error}'}
    return row


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
    n = sub.add_parser('pending'); n.add_argument('work', type=Path); n.add_argument('label', choices=LABEL_ORDER)
    c = sub.add_parser('check-run'); c.add_argument('work', type=Path); c.add_argument('label')
    sub.add_parser('labels')
    v = sub.add_parser('variant-plan'); v.add_argument('work', type=Path); v.add_argument('step', type=int, choices=(1, 2))
    args = parser.parse_args(argv)
    if args.command == 'labels':
        print(' '.join(LABEL_ORDER))
        return 0
    if args.command == 'pending':
        print(' '.join(pending(args.work, args.label)))
        return 0
    if args.command == 'check-run' and args.label in t1.LABEL_ORDER:
        bad = t1.check_run(args.work, args.label)
        for name, state in bad.items():
            print(f'{args.label} {name}: {state}; not a solver abort, failing the step', file=sys.stderr)
        return 1 if bad else 0
    if args.command == 'check-run':
        names = (pending(args.work, args.label) if args.label in EXTRA else
                 sorted(p.stem for p in (args.work / 't2' / args.label / 'tracking').glob('*.cir')))
        bad = t1.check_run(args.work, args.label, names)
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
