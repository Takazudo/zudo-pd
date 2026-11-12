"""D1 T2 peak-hold anti-windup clamp on -12 V, with the four enable-edge threshold corners (#235).

Pre-registered in d1-t2-criteria.md; this module implements exactly those decks and rules. It is a model
evaluation of a candidate, never a design change: no spec, schematic, PCB or calculator value moves here.
T2 on +5 V is rejected by construction (d1-t2-paper-check-20261111.md) and is not built.

Every deck derives from decks already retained in Git:
- the executed nom/adv decks of the reference extraction (extract_reference.derive_decks), and
- the loaded nomR/reR6/reR20 decks under tracking/, with the solver variant each one was accepted with in
  execution-20261110.json (reR6 abstol, reR20 rshunt, nomR original).
The loaded baselines run unmodified first and must reproduce their recorded waveform hashes.

usage (after extract_reference.py prepare / run / identity):
  t2_clamp.py prepare WORK --manifest PATH
  for every LABEL in LABEL_ORDER: run_ladder.py WORK/t2/LABEL/tracking $(t2_clamp.py pending WORK LABEL) --original-only
  t2_clamp.py analyze WORK --output PATH
"""
import argparse
import functools
import json
from pathlib import Path
import shutil
import sys

from analysis_inputs import adjacent_slope_screen, load
from extract_reference import attempt_dir, bin_mean, derive_decks, single_run
import gap_sensitivity as gap

HERE = Path(__file__).resolve().parent
EXECUTION = HERE / 'execution-20261110.json'
SCOPE = 'T2 peak-hold anti-windup clamp on -12 V plus the enable-edge threshold corners; model only, not adopted'

# ---------------------------------------------------------------- candidate values (single values, d1-t2-criteria.md)
VALUES = {
    'C_H': ('100n', 'hold capacitor, C0G, +/-5 %'),
    'R_B': ('10meg', 'hold bleed to M12_PRE, +/-1 %'),
    'R_1': ('1meg', 'difference-stage input resistors, +/-0.1 %'),
    'R_2': ('4.99meg', 'difference-stage feedback and reference resistors, +/-0.1 % (k = 4.99)'),
    'R_C': ('499k', 'clamp injection resistor into TRK12N_FB, +/-1 %'),
    'V_R': ('ref25', 'difference-stage reference: the existing 2.5 V reference node'),
}
CAPTURE_GATE = '0.5*(1+tanh((v(ennd)-1.2)*30))'   # hold follows the driver only early in the RAMP reset window
CLAMP_GATE = '0.5*(1+tanh((v(ennd)-1.0)*8))'      # the deck's own RAMP reset shape (BRST)
RESET_GATE = '0.5*(1+tanh((v(enn)-2.5)*4))'       # the deck's own disable shape (B10/B11/B25): hold reset on EN_N


def switch(name, a, b, gate):
    """The decks' behavioural-switch idiom: 3.5 ohm on, a permanent 100 Mohm term."""
    return f'{name} {a} {b} I=v({a},{b})*(1/3.5)*{gate}+v({a},{b})*1e-8'


def t2_block(inert=False):
    """Element lines of the T2 candidate. inert returns the clamp output to GND instead of the summing node."""
    sink = '0' if inert else 'trk12n_fb'
    return [
        '* T2 peak-hold anti-windup clamp on -12 V: candidate under evaluation, not a board part (d1-t2-criteria.md)'
        + (' [INERT CONTROL: clamp output returned to GND]' if inert else ''),
        'VT2N t2n m12_pre 0',
        'DT2K m12_drv t2k DBODY',
        switch('BT2K', 't2k', 't2h', CAPTURE_GATE),
        f"CT2H t2h m12_pre {VALUES['C_H'][0]}",
        f"RT2B t2h m12_pre {VALUES['R_B'][0]}",
        switch('BT2R', 't2h', 'm12_pre', RESET_GATE),
        'XT2A t2h t2hb p5sup t2n t2hb OPAx187',
        f"RT2P1 m12_drv t2p {VALUES['R_1'][0]}",
        f"RT2P2 t2p {VALUES['V_R'][0]} {VALUES['R_2'][0]}",
        f"RT2M1 t2hb t2m {VALUES['R_1'][0]}",
        f"RT2M2 t2m t2o {VALUES['R_2'][0]}",
        'XT2B t2p t2m p5sup t2n t2o OPAx187',
        'DT2C t2c t2o DBODY',
        f"RT2C t2c t2g {VALUES['R_C'][0]}",
        switch('BT2G', 't2g', sink, CLAMP_GATE),
    ]


Q6_LINE = ('XQ6 m12_out m12_gi m12_cs csd18543q3a', 'XQ6 t2q6 m12_gi m12_cs csd18543q3a\nVIQ6 m12_out t2q6 0')
T2_VECTORS = ('m12_drv', 't2h', 't2hb', 't2o', 't2c', 't2g', 'trk12n_fb', 'trk12n', 'mabs_n', 'm12_pre')
T2_CURRENTS = ('VIQ6', 'VT2N')


def t2_line(name):
    return (f'wrdata {name}-t2.txt ' + ' '.join(f'v({v})' for v in T2_VECTORS) + ' '
            + ' '.join(f'i({v})' for v in T2_CURRENTS) + ' v(ennd)')


T2_COLUMNS = T2_VECTORS + tuple(f'i_{v}' for v in T2_CURRENTS) + ('ennd',)

# ---------------------------------------------------------------- corners and cases
CORNER_VO_V = {'lo': -0.66, 'hi': 0.54}   # model 250 uA point 2.163 V mapped to guaranteed VGS(th) 1.5 / 2.7 V
OFFSET_LINES = {'+5': 'VO2 p5_g p5_gi 0', '-12': 'VO3 m12_g m12_gi 0'}
LOADED = {'nomR': None, 'reR6': ('abstol=1e-9', 'abstol=1e-8'), 'reR20': ('rshunt=1e10', 'rshunt=1e9')}
LOADED_VARIANT = {'nomR': 'original', 'reR6': 'abstol', 'reR20': 'rshunt'}
LABEL_ORDER = ('base', 'e12lo', 'e12hi', 'e5lo', 'e5hi', 'ctrl', 't2', 't2lo', 't2hi', 't2load')
T2_LABELS = ('t2', 't2lo', 't2hi', 't2load')
# No-load T2 case -> (label, deck) of its comparison baseline; 'run' is the reproduced reference-extraction pair.
NO_LOAD_T2 = {('t2', 'nom'): ('run', 'nom'), ('t2', 'adv'): ('run', 'adv'),
              ('t2lo', 'nom'): ('e12lo', 'nom'), ('t2hi', 'nom'): ('e12hi', 'nom')}
CORNER_CASES = {'e12lo': ('-12', 'lo'), 'e12hi': ('-12', 'hi'), 'e5lo': ('+5', 'lo'), 'e5hi': ('+5', 'hi')}


sha = gap.sha


def replace_once(text, old, new, what):
    if text.count(old + '\n') != 1:
        raise ValueError(f'{what}: expected exactly one "{old}" line')
    return text.replace(old + '\n', new + '\n')


def add_output(text, line, what):
    if text.count('.endc') != 1:
        raise ValueError(f'{what}: expected one control block')
    return text.replace('.endc', line + '\n.endc')


def with_t2(text, name, inert=False, block=None):
    """Insert the T2 block before .options, the Q6 drain ammeter and the T2 output line."""
    if text.count('\n.options') != 1:
        raise ValueError(f'{name}: expected one .options line')
    text = replace_once(text, Q6_LINE[0], Q6_LINE[1], name)
    text = text.replace('\n.options', '\n' + '\n'.join((block or t2_block)(inert)) + '\n.options')
    return add_output(text, t2_line(name), name)


def no_load(text, name):
    """The gap-sensitivity additions for rules 8-9: the 240 ms disable and the internal gate/source output."""
    text = replace_once(text, *gap.DISABLE_LINE, name)
    return add_output(text, gap.gap_line(name), name)


def corner(text, rail, which, name):
    value = CORNER_VO_V[which]
    head = OFFSET_LINES[rail].rsplit(' ', 1)[0]
    return replace_once(text, OFFSET_LINES[rail], f'{head} {value:g}', name)


def loaded_deck(name):
    """A loaded deck exactly as it was accepted in execution-20261110.json (deck hash checked)."""
    text = (HERE / 'tracking' / f'{name}.cir').read_text()
    if LOADED[name]:
        if text.count(LOADED[name][0]) != 1:
            raise ValueError(f'{name}: expected one {LOADED[name][0]}')
        text = text.replace(*LOADED[name])
    recorded = executed_attempt(name)
    if sha(text.encode()) != recorded['deck_sha256']:
        raise ValueError(f'{name}: deck does not reproduce its accepted {LOADED_VARIANT[name]} hash')
    return text


@functools.lru_cache(maxsize=None)
def execution_cases():
    return json.loads(EXECUTION.read_text())['cases']


def executed_attempt(name):
    case = execution_cases()[name]['receipt']['cases'][name]
    attempt = case['attempts'][case['selected_variant']]
    if attempt['variant'] != LOADED_VARIANT[name] or attempt['status'] != 'COMPLETE':
        raise ValueError(f'{name}: accepted attempt is not {LOADED_VARIANT[name]}')
    return attempt


def derive_cases(block=None):
    """label -> {deck name: deck text}. block replaces the attempt 1 candidate (a later revision)."""
    executed = {k: v['executed'] for k, v in derive_decks().items()}
    nom, adv = executed['nom'], executed['adv']
    out = {'base': {n: loaded_deck(n) for n in LOADED}}
    for label, (rail, which) in CORNER_CASES.items():
        out[label] = {'nom': no_load(corner(nom, rail, which, label), 'nom')}
    out['ctrl'] = {'adv': with_t2(no_load(adv, 'adv'), 'adv', inert=True, block=block)}
    out['t2'] = {'nom': with_t2(no_load(nom, 'nom'), 'nom', block=block),
                 'adv': with_t2(no_load(adv, 'adv'), 'adv', block=block)}
    for label, which in (('t2lo', 'lo'), ('t2hi', 'hi')):
        out[label] = {'nom': with_t2(no_load(corner(nom, '-12', which, label), 'nom'), 'nom', block=block)}
    out['t2load'] = {n: with_t2(loaded_deck(n), n, block=block) for n in LOADED}
    return out


def prepare(work, block=None, scope=SCOPE, criteria='d1-t2-criteria.md'):
    work = Path(work)
    manifest = {'scope': scope, 'criteria': criteria, 'labels': {}}
    for label, decks in derive_cases(block).items():
        root = work / 't2' / label
        (root / 'tracking').mkdir(parents=True)
        shutil.copytree(work / 'lib', root / 'lib')
        shutil.copyfile(work / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        manifest['labels'][label] = {}
        for name, text in decks.items():
            (root / 'tracking' / f'{name}.cir').write_text(text)
            manifest['labels'][label][name] = {'deck_sha256': sha(text.encode())}
    return manifest


# ---------------------------------------------------------------- execution order and gating
def status(work, label, name):
    return gap.case_status(Path(work) / 't2' / label, name)


def control_gate(work):
    """The control verdict, computed once after the ctrl label ran and kept beside the runs."""
    path = Path(work) / 't2' / 'control-gate.json'
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(control(work), indent=2, default=str) + '\n')
    return json.loads(path.read_text())


def pending(work, label):
    """Cases to run for LABEL. T2 runs only after the inert control is COMPLETE and reproduces the D1 failure."""
    names = list(derive_case_names()[label])
    if label in T2_LABELS and control_gate(work)['verdict'] != 'REPRODUCED':
        return []
    return names


def derive_case_names():
    names = {'base': list(LOADED), 'ctrl': ['adv'], 't2': ['nom', 'adv'], 't2load': list(LOADED)}
    for label in ('e12lo', 'e12hi', 'e5lo', 'e5hi', 't2lo', 't2hi'):
        names[label] = ['nom']
    return names


def check_run(work, label):
    """Workflow gate after a nonzero run_ladder: tolerate only solver aborts (ABORTED is recorded, not retried)."""
    bad = {}
    for name in pending(work, label):
        state = status(work, label, name)['status']
        if state not in ('COMPLETE', 'ABORTED'):
            bad[name] = state
    return bad


# ---------------------------------------------------------------- measurement
IDLE_WINDOW_S = (95e-3, 115e-3)       # clamp engaged, RAMP not yet moving (reference starts about 117 ms)
ENGAGED_WINDOW_S = (110e-3, 115e-3)
DISABLED_HOLD_WINDOW_S = (30e-3, 40e-3)
AFTER_DISABLE_HOLD_WINDOW_S = (245e-3, 250e-3)
CHANNEL_FRACTION_MAX = 0.5            # idle channel current at most half the output drain
LIMIT_CYCLE_PP_MAX_V = 10e-3          # detrended driver peak-to-peak while idle
RELEASE_STEP_MAX_V = 50e-3            # driver step when the clamp current disappears
RELEASE_FRACTION = 0.1                # release = first bin after 110 ms below 10 % of the engaged clamp current
RELEASE_HALF_WINDOW_S = 50e-6
ENGAGED_MIN_A = 0.1e-6                # the clamp is engaged when its mean current is at least 0.1 uA
HOLD_RESET_MAX_V = 10e-3              # held value within 10 mV of M12_PRE while disabled
RELTOL = 1e-3                         # the decks' own .options reltol
RECORDED_D1 = {'slope_v_per_ms': 1.4747780001127768, 'current_a': 0.26525933220897024}  # adv -12 V, run 43109786353
DRAIN = {'RMA1': 100e3, 'RT12NB': 750e3}
R_C_OHM = 499e3


def t2_record(run, name):
    path = attempt_dir(run, name) / f'{name}-t2.txt'
    times, series = gap.columns(path, len(T2_COLUMNS))
    return times, dict(zip(T2_COLUMNS, series))


def plain_record(run, name):
    """Main waveform only: the loaded decks save no OSC-capacitor, servo or gate output."""
    rows = load(attempt_dir(run, name) / f'{name}.dat')
    return {'rows': rows, 'times': [r[0] for r in rows], 'side': None, 'gap': None}


def case_record(run, name, t2=False, loaded=False):
    """gap_sensitivity's record; for a T2 deck the -12 supply current excludes the candidate's own op-amp supply."""
    record = plain_record(run, name) if loaded else gap.case_record(run, name)
    if t2:
        times, s = t2_record(run, name)
        if len(times) != len(record['rows']) or any(abs(a - b[0]) > 1e-12 for a, b in zip(times, record['rows'])):
            raise ValueError(f'{name}: T2 output and main waveform time grids differ')
        # load() returns tuples; the rows are rebuilt with the candidate's own supply current removed.
        record['rows'] = [(*row[:7], row[7] - extra, *row[8:]) for row, extra in zip(record['rows'], s['i_VT2N'])]
        record['t2'] = (times, s)
    return record


def detrended_pp(times, values, start, stop):
    b = gap.bins(times, values, start, stop)
    n = len(b)
    tm = sum(t for t, _ in b) / n
    vm = sum(v for _, v in b) / n
    slope = sum((t - tm) * (v - vm) for t, v in b) / sum((t - tm) ** 2 for t, _ in b)
    resid = [v - (vm + slope * (t - tm)) for t, v in b]
    return max(resid) - min(resid)


def t2_metrics(record, rest_vgs_window=IDLE_WINDOW_S):
    """Idle point, channel current against the output drain, limit cycle, release step, hold reset."""
    times, s = record['t2']
    drain = [(a - o) / DRAIN['RMA1'] + (b - o) / DRAIN['RT12NB'] for a, b, o in
             zip(s['mabs_n'], s['trk12n'], [r[3] for r in record['rows']])]
    clamp = [(g - c) / R_C_OHM for g, c in zip(s['t2g'], s['t2c'])]
    hold = [h - p for h, p in zip(s['t2h'], s['m12_pre'])]
    m = {}
    ch_bins = [v for _, v in gap.bins(times, s['i_VIQ6'], *IDLE_WINDOW_S)]
    dr_bins = [v for _, v in gap.bins(times, drain, *IDLE_WINDOW_S)]
    m['idle_channel_current_max_a'] = max(ch_bins)
    m['idle_channel_current_mean_a'] = sum(ch_bins) / len(ch_bins)
    m['idle_output_drain_min_a'] = min(dr_bins)
    m['idle_output_drain_mean_a'] = sum(dr_bins) / len(dr_bins)
    m['idle_driver_v'] = gap.mean_between(times, s['m12_drv'], *IDLE_WINDOW_S)
    m['idle_hold_v'] = gap.mean_between(times, s['t2h'], *IDLE_WINDOW_S)
    peak_t, peak = max(((t, v) for t, v in gap.bins(times, s['m12_drv'], *gap.ENABLE_WINDOW_S)), key=lambda x: x[1])
    m['driver_peak_v'], m['driver_peak_ms'] = peak, round(peak_t * 1e3, 3)
    m['idle_driver_below_peak_v'] = peak - m['idle_driver_v']
    if record['gap'] is not None:
        gt, series = record['gap']
        vgs = [g - c for g, c in zip(series[gap.GAP_VECTORS.index('m12_gi')], series[gap.GAP_VECTORS.index('m12_cs')])]
        m['idle_internal_vgs_v'] = gap.mean_between(gt, vgs, *rest_vgs_window)
    m['limit_cycle_driver_pp_v'] = detrended_pp(times, s['m12_drv'], *IDLE_WINDOW_S)
    m['engaged_clamp_current_a'] = gap.mean_between(times, clamp, *ENGAGED_WINDOW_S)
    m['clamp_engaged'] = m['engaged_clamp_current_a'] >= ENGAGED_MIN_A
    m['release_ms'] = m['release_step_v'] = None
    if m['clamp_engaged']:
        for t0, v in gap.bins(times, clamp, ENGAGED_WINDOW_S[0], times[-1] - RELEASE_HALF_WINDOW_S):
            if v < RELEASE_FRACTION * m['engaged_clamp_current_a']:
                mean = bin_mean(times, s['m12_drv'])
                m['release_ms'] = round(t0 * 1e3, 6)
                m['release_step_v'] = mean(t0, t0 + RELEASE_HALF_WINDOW_S) - mean(t0 - RELEASE_HALF_WINDOW_S, t0)
                break
    m['hold_while_disabled_max_v'] = gap.extremes(times, hold, *DISABLED_HOLD_WINDOW_S)[1]
    if times[-1] >= AFTER_DISABLE_HOLD_WINDOW_S[1] - 1e-9 and record['gap'] is not None:
        m['hold_after_disable_max_v'] = gap.extremes(times, hold, AFTER_DISABLE_HOLD_WINDOW_S[0],
                                                     AFTER_DISABLE_HOLD_WINDOW_S[1] - gap.BIN_S)[1]
    return m


def t2_rules(m):
    released = m['release_step_v'] is not None
    return {
        '10 idle channel current at most half the output drain':
            m['idle_channel_current_max_a'] <= CHANNEL_FRACTION_MAX * m['idle_output_drain_min_a'],
        '11 no limit cycle while idle': m['limit_cycle_driver_pp_v'] <= LIMIT_CYCLE_PP_MAX_V,
        '12 release step bound': released and abs(m['release_step_v']) <= RELEASE_STEP_MAX_V,
        '13 clamp engaged while idle': m['clamp_engaged'],
        '14 hold reset while disabled': (m['hold_while_disabled_max_v'] <= HOLD_RESET_MAX_V
                                         and m.get('hold_after_disable_max_v', float('inf')) <= HOLD_RESET_MAX_V),
    }


def control(work):
    """Inert control: the adv deck with the candidate present but its output returned to GND."""
    work = Path(work)
    state = status(work, 'ctrl', 'adv')
    out = {'status': state['status']}
    if state['status'] != 'COMPLETE':
        out['verdict'] = 'NOT EVALUATED'
        out.update({k: v for k, v in state.items() if k not in ('run', 'status')})
        return out
    try:
        record = case_record(state['run'], 'adv', t2=True)
        screen = gap.screens(record)['-12']
        ex = screen['exception']
        slope, current = ex['maximum_slope_in_voltage_region_v_per_ms'], ex['maximum_current_in_voltage_region_a']
        reproduced = (not gap.screen_passes(screen) and slope > ex['slope_ceiling_v_per_ms']
                      and current > ex['capacitive_current_ceiling_a'])
        try:
            adv = gap.case_record(single_run(work), 'adv')
            out['rule6_loading_reference'] = gap.rule6_detail('-12', gap.rail_metrics(record, '-12'),
                                                              gap.rail_metrics(adv, '-12'))
        except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
            out['rule6_loading_reference'] = f'NOT EVALUATED: {type(error).__name__}: {error}'
        out.update({'slope_v_per_ms': slope, 'current_a': current,
                    'slope_minus_recorded_v_per_ms': slope - RECORDED_D1['slope_v_per_ms'],
                    'current_minus_recorded_a': current - RECORDED_D1['current_a'],
                    'verdict': 'REPRODUCED' if reproduced else 'NOT REPRODUCED'})
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        out.update({'verdict': 'NOT EVALUATED', 'reason': f'{type(error).__name__}: {error}'})
    return out


def baseline_record(work, base_run, label, name):
    if label == 'run':
        return gap.case_record(base_run, name)
    state = status(work, label, name)
    if state['status'] != 'COMPLETE':
        raise ValueError(f'baseline {label}/{name} is {state["status"]}')
    return gap.case_record(state['run'], name)


def no_load_case(work, base_run, label, name, judge=None):
    state = status(work, label, name)
    row = {'status': state['status']}
    if state['status'] != 'COMPLETE':
        row.update({k: v for k, v in state.items() if k not in ('run', 'status')})
        row['passes'] = None
        return row
    base_label, base_name = NO_LOAD_T2[(label, name)]
    if base_label != 'run' and status(work, base_label, base_name)['status'] != 'COMPLETE':
        row.update({'status': 'NOT EVALUATED', 'passes': None,
                    'reason': f'baseline {base_label}/{base_name} is {status(work, base_label, base_name)["status"]}'})
        return row
    try:
        base = baseline_record(work, base_run, base_label, base_name)
        record = case_record(state['run'], name, t2=True)
        bs, vs = gap.screens(base), gap.screens(record)
        b, v = gap.rail_metrics(base, '-12'), gap.rail_metrics(record, '-12')
        judged = judge('-12', vs, bs, v, b, record) if judge else gap.judge('-12', vs, bs, v, b)
        rules = {f'{k + 1} {r}': ok for k, (r, ok) in enumerate(judged.items())}
        m = t2_metrics(record)
        rules.update(t2_rules(m))
        row.update({'baseline': f'{base_label}/{base_name}', **gap.summary(v, vs['-12']), 't2': m, 'rules': rules,
                    'passes': all(rules.values()), 'rule6_detail': gap.rule6_detail('-12', v, b),
                    'other_rails': {r: vs[r]['disposition'] for r in ('+12', '+5')}})
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        # A completed case whose evaluation fails is neither a pass nor an electrical fail (verdict NOT EVALUATED).
        row.update({'status': 'NOT EVALUATED', 'reason': f'{type(error).__name__}: {error}', 'passes': None})
    return row


# ---------------------------------------------------------------- loaded cases
def loaded_screens(record, start, stop):
    rows = [r for r in record['rows'] if start <= r[0] < stop]
    return {rail: adjacent_slope_screen(rows, index, sign, normal, False, None)
            for rail, (index, sign, normal, _) in gap.OTHER_RAILS.items()}


def peak_current(record, start, stop):
    return max(abs(v) for _, v in gap.bins(record['times'], [r[7] for r in record['rows']], start, stop))


def tracking_difference(base, record, start, stop):
    """Largest 2 us bin difference of each output, against the decks' own reltol * |v| + vntol."""
    out = {}
    for rail, (index, _, _, _) in gap.OTHER_RAILS.items():
        b = gap.bins(base['times'], [r[index] for r in base['rows']], start, stop)
        v = gap.bins(record['times'], [r[index] for r in record['rows']], start, stop)
        worst = max(((abs(x - y) - (RELTOL * abs(x) + gap.VNTOL_V)), abs(x - y), t) for (t, x), (_, y) in zip(b, v))
        out[rail] = {'max_abs_difference_v': max(abs(x - y) for (_, x), (_, y) in zip(b, v)),
                     'worst_excess_over_tolerance_v': worst[0], 'at_ms': round(worst[2] * 1e3, 6),
                     'within_tolerance': worst[0] <= 0}
    return out


def reenable_time(record, after):
    """The first EN_N fall below 2.5 V that follows its rise above 2.5 V after the disable request."""
    disabled = False
    for row in record['rows']:
        if row[0] <= after:
            continue
        if not disabled:
            disabled = row[11] > 2.5
        elif row[11] < 2.5:
            return row[0]
    return None


LOADED_WINDOWS = {'nomR': ((40e-3, 245e-3),), 'reR6': ((40e-3, 150e-3), (150e-3, 315e-3)),
                  'reR20': ((40e-3, 150e-3), (150e-3, 315e-3))}
DISABLE_REQUEST_S = 150e-3


def loaded_case(work, name, base_ok):
    """base_ok is this case's own loaded-baseline identity."""
    state = status(work, 't2load', name)
    row = {'status': state['status']}
    if state['status'] != 'COMPLETE':
        row.update({k: v for k, v in state.items() if k not in ('run', 'status')})
        row['passes'] = None
        return row
    if not base_ok:
        row.update({'status': 'NOT EVALUATED', 'reason': 'loaded baseline not reproduced', 'passes': None})
        return row
    try:
        base = plain_record(status(work, 'base', name)['run'], name)
        record = case_record(state['run'], name, t2=True, loaded=True)
        rules, detail = {}, {}
        for k, (start, stop) in enumerate(LOADED_WINDOWS[name]):
            tag = 'startup' if k == 0 else 're-enable'
            bs, vs = loaded_screens(base, start, stop), loaded_screens(record, start, stop)
            rules[f'L1 {tag}: every rail screen no worse than baseline'] = all(
                gap.screen_passes(vs[r]) or not gap.screen_passes(bs[r]) for r in vs)
            diff = tracking_difference(base, record, start, stop)
            rules[f'L2 {tag}: outputs within reltol of baseline'] = all(d['within_tolerance'] for d in diff.values())
            pb, pv = peak_current(base, start, stop), peak_current(record, start, stop)
            rules[f'L3 {tag}: -12 V peak supply current not above baseline'] = pv <= pb * (1 + RELTOL)
            detail[tag] = {'screens': {r: vs[r]['maximum']['slope_v_per_ms'] for r in vs}, 'differences': diff,
                           'peak_current_a': {'baseline': pb, 't2': pv}}
        times, s = record['t2']
        hold = [h - p for h, p in zip(s['t2h'], s['m12_pre'])]
        clamp = [(g - c) / R_C_OHM for g, c in zip(s['t2g'], s['t2c'])]
        if name != 'nomR':
            t_re = reenable_time(record, DISABLE_REQUEST_S)
            if t_re is None:
                raise ValueError(f'{name}: no re-enable found')
            before = gap.extremes(times, hold, t_re - 1e-3, t_re)[1]
            rules['L4 hold reset at re-enable'] = before <= HOLD_RESET_MAX_V
            detail['re-enable'].update({'reenable_ms': round(t_re * 1e3, 3), 'hold_before_reenable_max_v': before,
                                        'clamp_current_after_reenable_max_a':
                                            gap.extremes(times, clamp, t_re, min(t_re + 80e-3, times[-1] - 1e-4))[1]})
        detail['clamp_current_startup_max_a'] = gap.extremes(times, clamp, 40e-3, 140e-3)[1]
        row.update({'rules': rules, 'passes': all(rules.values()), 'detail': detail})
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        # A completed case whose evaluation fails is neither a pass nor an electrical fail (verdict NOT EVALUATED).
        row.update({'status': 'NOT EVALUATED', 'reason': f'{type(error).__name__}: {error}', 'passes': None})
    return row


def loaded_identity(work):
    out = {}
    for name in LOADED:
        state = status(work, 'base', name)
        if state['status'] != 'COMPLETE':
            out[name] = {'status': state['status'], 'reproduced': False}
            continue
        receipt = json.loads((state['run'] / 'receipt.json').read_text())
        got = receipt['cases'][name]['attempts'][-1].get('waveform_sha256')
        want = executed_attempt(name)['waveform_sha256']
        out[name] = {'status': 'COMPLETE', 'waveform_sha256': got, 'recorded': want, 'reproduced': got == want}
    return out


# ---------------------------------------------------------------- enable-edge corners
# +5 V: the recorded 0.8 V hazard-conjunction quantity; -12 V has no recorded enable-edge bound (gap_sensitivity).
CONTRACT_REFERENCE_V = {rail: ref['value_v'] for rail, ref in gap.RULE6_CONTRACT_REFERENCE.items()}


def corner_case(work, label):
    rail, which = CORNER_CASES[label]
    state = status(work, label, 'nom')
    row = {'rail': rail, 'vo_v': CORNER_VO_V[which], 'status': state['status']}
    if state['status'] != 'COMPLETE':
        row.update({k: v for k, v in state.items() if k not in ('run', 'status')})
        return row
    try:
        m = gap.rail_metrics(gap.case_record(state['run'], 'nom'), rail)
        reach = max(abs(x) for x in m['enable_edge_extremes_v'])
        limit = CONTRACT_REFERENCE_V[rail]
        row.update({k: m.get(k) for k in ('enable_vgs_max_v', 'onset_vgs_v', 'enable_min_distance_to_conduction_v',
                                            'enable_peak_current_a', 'enable_edge_extremes_v', 'floor_v')})
        row['contract_reference_v'] = limit
        row['verdict'] = ('CONFIRMS the recorded negative' if not m['enable_conduction'] and (limit is None or reach < limit)
                          else 'CONTRADICTS the recorded negative')
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
        row.update({'status': 'NOT EVALUATED', 'reason': f'{type(error).__name__}: {error}'})
    return row


def analyze(work, judge=None, scope=SCOPE, criteria='d1-t2-criteria.md'):
    work = Path(work)
    base_run = single_run(work)
    identity = loaded_identity(work)
    result = {'scope': scope, 'criteria': criteria, 'electrical_acceptance': 'NOT ESTABLISHED',
              'd1': 'HELD (a -12 V only result does not close D1)', 'loaded_baseline_identity': identity,
              'corners': {label: corner_case(work, label) for label in CORNER_CASES},
              'control': control(work)}
    if result['control']['verdict'] != 'REPRODUCED':
        result['t2'] = {'verdict': 'NOT EVALUATED',
                        'reason': 'inert control did not reproduce the recorded D1 failure; the realization is the finding'}
        return result
    no_load_rows = {f'{label}/{name}': no_load_case(work, base_run, label, name, judge) for label, name in NO_LOAD_T2}
    loaded_rows = {name: loaded_case(work, name, identity[name]['reproduced']) for name in LOADED}
    rows = list(no_load_rows.values()) + list(loaded_rows.values())
    if all(r.get('passes') is True for r in rows):
        verdict = 'PASS'
    elif any(r.get('passes') is False for r in rows):
        verdict = 'FAIL'
    else:
        verdict = 'NOT EVALUATED'
    result['t2'] = {'verdict': verdict, 'no_load': no_load_rows, 'loaded': loaded_rows}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('work', type=Path); p.add_argument('--manifest', type=Path, required=True)
    a = sub.add_parser('analyze'); a.add_argument('work', type=Path); a.add_argument('--output', type=Path, required=True)
    n = sub.add_parser('pending'); n.add_argument('work', type=Path); n.add_argument('label', choices=LABEL_ORDER)
    c = sub.add_parser('check-run'); c.add_argument('work', type=Path); c.add_argument('label', choices=LABEL_ORDER)
    args = parser.parse_args(argv)
    if args.command == 'pending':
        print(' '.join(pending(args.work, args.label)))
        return 0
    if args.command == 'check-run':
        bad = check_run(args.work, args.label)
        for name, state in bad.items():
            print(f'{args.label} {name}: {state}; not a solver abort, failing the step', file=sys.stderr)
        return 1 if bad else 0
    if args.command == 'prepare':
        args.manifest.write_text(json.dumps(prepare(args.work), indent=2) + '\n')
        return 0
    result = analyze(args.work)
    text = json.dumps(result, indent=2) + '\n'
    args.output.write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
