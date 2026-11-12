"""D1 C1 gate-to-threshold gap sensitivity (#235); model sensitivity only, pre-registered in d1-gap-criteria.md.

Eight variant decks derive from the executed baseline decks of the servo extraction. Each moves only the
enabled-state gate resting level of one failed rail (+5 on nom, -12 on adv) at the existing gate-offset
position, adds a disable at 240 ms and one output-only line that saves the internal gate and source nodes.
Amendment 1 (attempt 2): the enabled-state shift is a scheduled PWL value of the existing offset source, so the
deck is exactly baseline before 40 ms; a case that aborts is recorded as ABORTED and stops its rail.
The baseline pair still runs unmodified in the same dispatch and must reproduce first. No claim is made about
any real part, and nothing here is a design change, a tolerance or electrical acceptance.

usage (after extract_reference.py prepare / run / identity):
  gap_sensitivity.py prepare WORK --manifest PATH
  for every LABEL in order: run_ladder.py WORK/gaps/LABEL/tracking $(gap_sensitivity.py pending WORK LABEL) --original-only
  gap_sensitivity.py analyze WORK --output PATH
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

from analysis_inputs import adjacent_slope_screen, load
from analyze_refinement import supplemental
from extract_reference import CASES, attempt_dir, bin_mean, derive_decks, single_run
from servo_criteria import SERVO_VECTORS

SUPPORTED, REFUTED = 'SUPPORTED', 'REFUTED'
BIN_S = 2e-6
VNTOL_V = 1e-5                  # the decks' own .options vntol; differences below it are not resolved
CONDUCTION_A = 5e-3             # same conduction criterion as the servo criteria
REST_WINDOW_S = (110e-3, 115e-3)  # baseline drivers are parked and the reference has not moved yet
SCREEN_WINDOW_S = (40e-3, 234.5e-3)  # the refinement's screened window
DISABLED_WINDOW_S = (2e-3, 40e-3)    # supplies settled, enable not yet latched
ENABLE_WINDOW_S = (40e-3, 110e-3)    # enable edge up to the rest window
DISABLE_AT_S = 240e-3
DISABLE_SETTLE_S = 245e-3
PRE_DISABLE_S = 238e-3
END_S = 250e-3
GATE_ON = '0.5*(1+tanh((2.5-v(enn))*4))'  # attempt 1 only: the decks' own enable shape (B10/B11/B25 use its complement)
# Amendment 1: the shift follows the decks' scheduled EN (VENN 40-40.05 ms) and disable (VDIS 240-240.05 ms) edges.
SHIFT_EDGES = ('40m', '40.05m', '240m', '240.05m')
SCHEDULED = 'scheduled-enable'  # attempt 1 called these 'enabled-gated' (v(enn)-gated behavioural source)
LABEL_ORDER = ('g20', 'g16', 'g12', 'worst')
SOLVER_MARKERS = ('Timestep too small', 'trouble with node', 'doAnalyses', 'simulation(s) aborted')
SOLVER_ABORT = ('simulation(s) aborted', 'Timestep too small')  # ngspice's own abort statements
TIMEOUT_RETURNCODE = 124  # run_ladder.py records a 3000 s solver timeout with this code
# Rule 6 has no contract tolerance of its own; this is the nearest recorded quantity, given only for the manager's
# judgement of significance (execution-20261110.md, canonical OSC interface 433c88b). It is never a pass rule.
RULE6_CONTRACT_REFERENCE = {
    '+5': {'quantity': '+5 V above 0.8 V while an analog rail is below 1.5 V and the other at least 8 V '
                       '(hazard conjunction; 1.5 V is the sufficient analysis threshold)', 'value_v': 0.8},
    '-12': {'quantity': 'none recorded: the retained phase33 records cite no -12 V enable-edge excursion bound from the '
                        'interface; the 0.75 V magnitude is the no-load slope-exception region, not an excursion limit',
            'value_v': None},
}

# Failed rail -> deck, offset element, its baseline line and value, internal gate/source columns in -gap.txt,
# main waveform output column and current column (after time), sign of the output, normal and exception limits.
RAILS = {
    '+5': {'case': 'nom', 'offset': 'VO2', 'line': 'VO2 p5_g p5_gi 0', 'base_v': 0.0, 'gate': 'p5_gi', 'source': 'p5_cs',
           'node_g': 'p5_g', 'output_column': 2, 'current_column': 6, 'sign': 1, 'probe': 2,
           'normal': 0.51, 'exception': (0.45, 0.95, 0.114), 'driver': 'p5_drv', 'driver_rail_v': 0.0},
    '-12': {'case': 'adv', 'offset': 'VO3', 'line': 'VO3 m12_g m12_gi 0.5', 'base_v': 0.5, 'gate': 'm12_gi', 'source': 'm12_cs',
            'node_g': 'm12_g', 'output_column': 3, 'current_column': 7, 'sign': -1, 'probe': 3,
            'normal': 1.22, 'exception': (0.75, 1.47, 0.265), 'driver': 'm12_drv', 'driver_rail_v': -12.142},
}
OTHER_RAILS = {'+12': (1, 1, 1.23, None), '+5': (2, 1, 0.51, (0.45, 0.95, 0.114)), '-12': (3, -1, 1.22, (0.75, 1.47, 0.265))}
# Gap = Vgs at 5 mA conduction onset - resting Vgs, measured on the baseline servo record (run 43099431981):
# +5 rest -0.0000459 V, onset 2.443369 V; -12 rest -0.514498 V, onset 2.352273 V.
BASELINE_GAP_V = {'+5': 2.4434, '-12': 2.8668}
TARGET_GAPS_V = (2.0, 1.6, 1.2)
WORST_EXTRA_V = 0.3
GAP_VECTORS = ('p12_gi', 'p12_cs', 'p5_gi', 'p5_cs', 'm12_gi', 'm12_cs')
DISABLE_LINE = ('VDIS dis 0 0', 'VDIS dis 0 PWL(0 0 240m 0 240.05m 5)')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def labels():
    """label -> {rail: (kind, shift_v)}; a positive shift raises the enabled gate, the worst case raises the threshold."""
    out = {f'g{int(round(g * 10)):02d}': {r: (SCHEDULED, round(BASELINE_GAP_V[r] - g, 4)) for r in RAILS}
           for g in TARGET_GAPS_V}
    out['worst'] = {r: ('constant', -WORST_EXTRA_V) for r in RAILS}
    return out


def offset_line(rail, kind, shift):
    spec = RAILS[rail]
    head = f"{spec['offset']} {spec['node_g']} {spec['gate']}"
    base, on = spec['base_v'], round(spec['base_v'] - shift, 4)
    if kind == 'constant':
        return f"{head} {on:g}"
    a, b, c, d = SHIFT_EDGES
    return f"{head} PWL(0 {base:g} {a} {base:g} {b} {on:g} {c} {on:g} {d} {base:g})"


def gap_line(name):
    return f"wrdata {name}-gap.txt " + ' '.join(f'v({v})' for v in GAP_VECTORS)


def variant(executed, name, rail, kind, shift):
    spec = RAILS[rail]
    text = executed
    for old, new in ((spec['line'], offset_line(rail, kind, shift)), DISABLE_LINE):
        if text.count(old + '\n') != 1:
            raise ValueError(f'{name}: expected exactly one "{old}" line')
        text = text.replace(old + '\n', new + '\n')
    if text.count('.endc') != 1:
        raise ValueError(f'{name}: expected one control block')
    return text.replace('.endc', gap_line(name) + '\n.endc')


def derive_variants():
    decks = derive_decks()
    out = {}
    for label, rails in labels().items():
        out[label] = {}
        for rail, (kind, shift) in rails.items():
            name = RAILS[rail]['case']
            out[label][name] = {'rail': rail, 'kind': kind, 'shift_v': shift,
                                'target_gap_v': round(BASELINE_GAP_V[rail] - shift, 4),
                                'deck': variant(decks[name]['executed'], name, rail, kind, shift),
                                'baseline_executed_sha256': sha(decks[name]['executed'].encode())}
    return out


def prepare(work):
    work = Path(work)
    manifest = {'scope': 'C1 gap sensitivity; model only', 'labels': {}}
    for label, cases in derive_variants().items():
        root = work / 'gaps' / label
        (root / 'tracking').mkdir(parents=True)
        shutil.copytree(work / 'lib', root / 'lib')
        shutil.copyfile(work / 'tracking' / '.spiceinit', root / 'tracking' / '.spiceinit')
        manifest['labels'][label] = {}
        for name, case in cases.items():
            (root / 'tracking' / f'{name}.cir').write_text(case['deck'])
            manifest['labels'][label][name] = {k: v for k, v in case.items() if k != 'deck'}
            manifest['labels'][label][name]['variant_deck_sha256'] = sha(case['deck'].encode())
    return manifest


# ---------------------------------------------------------------- execution status (amendment 1)
def solver_message(log):
    """The solver's own abort lines, for an ABORTED record."""
    if not Path(log).exists():
        return 'no solver log'
    text = Path(log).read_text(errors='replace').replace('Reference value', '\nReference value')
    lines = [x.strip() for x in text.splitlines() if any(m in x for m in SOLVER_MARKERS)]
    return ' | '.join(lines)[:600] or 'no solver abort line found'


ABORT_LINE = re.compile(r'Timestep too small; time = ([0-9.eE+-]+), timestep = ([0-9.eE+-]+): '
                        r'(?:trouble with node "([^"]+)"|(cause unrecorded))')


def abort_detail(log, dat=None):
    """ngspice's abort line parsed, plus the last saved sample. 'unrecorded' is ngspice's own text: it named no node."""
    text = Path(log).read_text(errors='replace') if Path(log).exists() else ''
    m = ABORT_LINE.search(text)
    out = ({'time_s': float(m.group(1)), 'timestep_s': float(m.group(2)), 'node': m.group(3),
            'cause': 'node named' if m.group(3) else 'unrecorded (ngspice named no node)'} if m else
           {'time_s': None, 'timestep_s': None, 'node': None, 'cause': 'no abort line found'})
    if dat is not None and Path(dat).exists():
        last = None
        with open(dat, errors='replace') as f:
            for line in f:
                if line.strip():
                    last = line
        if last is not None:
            values = [float(x) for x in last.split()]
            out['last_sample'] = {'time_s': values[0], 'values': values[1::2]}
    return out


def case_status(label_root, name):
    """COMPLETE, ABORTED (a solver abort, with its message), RUN FAILED (anything else) or NOT RUN for one case.

    ABORTED needs the solver's own abort statement in the log, a non-timeout nonzero return or an aborted log,
    a clean container cleanup and a finished (not interrupted) runner; everything else fails closed as RUN FAILED.
    """
    runs = sorted(Path(label_root).glob('ladder-*'))
    if not runs:
        return {'status': 'NOT RUN'}
    if len(runs) != 1:
        raise ValueError(f'{label_root}: expected at most one runner directory, found {len(runs)}')
    receipt = json.loads((runs[0] / 'receipt.json').read_text())
    case = receipt.get('cases', {}).get(name)
    if case is None:
        return {'status': 'NOT RUN'}
    if case.get('status') == 'COMPLETE':
        return {'status': 'COMPLETE', 'run': runs[0]}
    last = (case.get('attempts') or [{}])[-1]
    log = attempt_dir(runs[0], name) / f'{name}.log'
    text = log.read_text(errors='replace') if log.exists() else ''
    out = {'run': runs[0], 'returncode': last.get('returncode'), 'runner_reason': last.get('reason'),
           'runner_status': receipt.get('status'), 'solver_message': solver_message(log),
           'abort': abort_detail(log, attempt_dir(runs[0], name) / f'{name}.dat')}
    solver_abort = (receipt.get('status') == 'FAILED' and last.get('status') == 'FAILED'
                    and last.get('cleanup_returncode') == 0 and last.get('returncode') != TIMEOUT_RETURNCODE
                    and last.get('reason') == 'solver failed, timed out, or aborted'
                    and any(m in text for m in SOLVER_ABORT))
    return {'status': 'ABORTED' if solver_abort else 'RUN FAILED', **out}


def check_run(work, label):
    """Workflow gate after a nonzero run_ladder: tolerate only solver aborts of the scheduled cases."""
    bad = {}
    for name in pending(work, label):
        status = case_status(Path(work) / 'gaps' / label, name)['status']
        if status not in ('COMPLETE', 'ABORTED'):
            bad[name] = status
    return bad


def pending(work, label):
    """Cases to run for LABEL: a rail stops after its first ABORTED case and is not retried in the dispatch."""
    out = []
    for rail, spec in RAILS.items():
        name = spec['case']
        earlier = LABEL_ORDER[:LABEL_ORDER.index(label)]
        if all(case_status(Path(work) / 'gaps' / prior, name)['status'] != 'ABORTED' for prior in earlier):
            out.append(name)
    return out


# ---------------------------------------------------------------- measurement helpers
def columns(path, count):
    """wrdata time/value pairs -> (times, [series])."""
    times, series = [], [[] for _ in range(count)]
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        row = [float(x) for x in line.split()]
        if len(row) != 2 * count:
            raise ValueError(f'{path}: expected {2 * count} columns')
        times.append(row[0])
        for k in range(count):
            series[k].append(row[2 * k + 1])
    return times, series


def bins(times, values, start, stop):
    mean = bin_mean(times, values)
    edges, t = [], start
    while t + BIN_S <= stop + 1e-15:
        edges.append(t)
        t += BIN_S
    return [(t0, mean(t0, t0 + BIN_S)) for t0 in edges]


def extremes(times, values, start, stop):
    b = [v for _, v in bins(times, values, start, stop)]
    return min(b), max(b)


def largest_drop(times, values, sign, start, stop):
    b = [sign * v for _, v in bins(times, values, start, stop)]
    return min([0.0] + [b1 - b0 for b0, b1 in zip(b, b[1:])])


def overshoot(times, values, sign, start, stop):
    b = [sign * v for _, v in bins(times, values, start, stop)]
    return max(b) - b[-1]


def mean_between(times, values, start, stop):
    return bin_mean(times, values)(start, stop)


def onset(times, current, start, stop):
    for t0, v in bins(times, current, start, stop):
        if abs(v) >= CONDUCTION_A:
            return t0
    return None


# ---------------------------------------------------------------- per-case evaluation
def case_record(run, name):
    work = attempt_dir(run, name)
    rows = load(work / f'{name}.dat')
    times = [r[0] for r in rows]
    side = supplemental(work / f'{name}-osc-cap.txt', rows)
    gap = (work / f'{name}-gap.txt')
    record = {'rows': rows, 'times': times, 'side': side, 'gap': columns(gap, len(GAP_VECTORS)) if gap.exists() else None}
    servo = work / f'{name}-servo.txt'
    if record['gap'] is None and servo.exists():
        # Baseline decks save no internal gate: rebuild it from the main gate column and the deck's constant offset.
        st, ss = columns(servo, len(SERVO_VECTORS))
        gates = {'p12_g': 8, 'p5_g': 9, 'm12_g': 10}
        offsets = {'nom': {'+5': 0.0, '-12': 0.0}, 'adv': {'+5': -0.5, '-12': 0.5}}[name]
        cols = {'p5_gi': [r[gates['p5_g']] - offsets['+5'] for r in rows], 'p5_cs': ss[SERVO_VECTORS.index('p5_cs')],
                'm12_gi': [r[gates['m12_g']] - offsets['-12'] for r in rows], 'm12_cs': ss[SERVO_VECTORS.index('m12_cs')]}
        record['gap'] = (st, [cols.get(v, [0.0] * len(st)) for v in GAP_VECTORS])
    return record


def screens(record):
    rows, side = record['rows'], record['side']
    on = [r for r in rows if SCREEN_WINDOW_S[0] <= r[0] < SCREEN_WINDOW_S[1]]
    caps = [(r[0], p[1] / .05, p[2] / .05, (p[3] - r[3]) / .05) for r, p in zip(rows, side)
            if SCREEN_WINDOW_S[0] <= r[0] < SCREEN_WINDOW_S[1]]
    out = {}
    for label, (index, sign, normal, exception) in OTHER_RAILS.items():
        screen = adjacent_slope_screen(on, index, sign, normal, True, exception)
        screen['maximum_osc_capacitor_charging_current_a'] = max(x[index] for x in caps)
        if exception:
            region = [c[index] for r, c in zip(on, caps) if 0 <= sign * r[index] <= exception[0]]
            screen['exception']['maximum_current_in_voltage_region_a'] = max(region)
            screen['exception']['current_ceiling_exceeded_in_saved_samples'] = max(region) > exception[2]
            screen['exception']['maximum_slope_in_voltage_region_v_per_ms'] = max(
                abs(b[index] - a[index]) / (b[0] - a[0]) / 1000 for a, b in zip(on, on[1:])
                if max(sign * a[index], sign * b[index]) <= exception[0])
        out[label] = screen
    return out


def screen_passes(screen):
    current_ok = screen['exception'] is None or not screen['exception']['current_ceiling_exceeded_in_saved_samples']
    return screen['recorded_bound_exceeding_segments'] == 0 and screen['voltage_boundary_straddling_segments'] == 0 and current_ok


def rail_metrics(record, rail, offset_v=None):
    spec = RAILS[rail]
    times, rows = record['times'], record['rows']
    out = [r[spec['output_column']] for r in rows]
    cur = [r[spec['current_column']] for r in rows]
    sign = spec['sign']
    metrics = {
        'floor_v': mean_between(times, out, *REST_WINDOW_S),
        'overshoot_v': overshoot(times, out, sign, *SCREEN_WINDOW_S),
        'largest_drop_v': largest_drop(times, out, sign, *SCREEN_WINDOW_S),
        'disabled_extremes_v': extremes(times, out, *DISABLED_WINDOW_S),
        'enable_edge_extremes_v': extremes(times, out, *ENABLE_WINDOW_S),
        'conduction_onset_ms': None,
    }
    enable_currents = [v for _, v in bins(times, cur, *ENABLE_WINDOW_S)]
    metrics['enable_peak_current_a'] = max(abs(v) for v in enable_currents)
    metrics['enable_conduction'] = metrics['enable_peak_current_a'] >= CONDUCTION_A
    t_on = onset(times, cur, REST_WINDOW_S[0], SCREEN_WINDOW_S[1])
    metrics['conduction_onset_ms'] = None if t_on is None else round(t_on * 1e3, 6)
    if record['gap'] is not None:
        gt, series = record['gap']
        g = series[GAP_VECTORS.index(spec['gate'])]
        s = series[GAP_VECTORS.index(spec['source'])]
        vgs = [a - b for a, b in zip(g, s)]
        rest = mean_between(gt, vgs, *REST_WINDOW_S)
        metrics['rest_vgs_v'] = rest
        if t_on is not None:
            at_on = mean_between(gt, vgs, t_on, t_on + BIN_S)
            metrics['onset_vgs_v'] = at_on
            metrics['realized_gap_v'] = at_on - rest
        metrics['disabled_vgs_max_v'] = extremes(gt, vgs, *DISABLED_WINDOW_S)[1]
        metrics['enable_vgs_max_v'] = extremes(gt, vgs, *ENABLE_WINDOW_S)[1]
        if 'onset_vgs_v' in metrics:
            metrics['enable_min_distance_to_conduction_v'] = metrics['onset_vgs_v'] - metrics['enable_vgs_max_v']
        if gt[-1] >= END_S - 1e-9:
            metrics['after_disable_vgs_max_v'] = extremes(gt, vgs, DISABLE_SETTLE_S, END_S - BIN_S)[1]
            metrics['after_disable_extremes_v'] = extremes(times, out, DISABLE_AT_S, END_S - BIN_S)
            metrics['pre_disable_extremes_v'] = extremes(times, out, PRE_DISABLE_S, DISABLE_AT_S)
    return metrics


def within(variant_extremes, baseline_extremes):
    return variant_extremes[0] >= baseline_extremes[0] - VNTOL_V and variant_extremes[1] <= baseline_extremes[1] + VNTOL_V


def rule6_detail(rail, v, b):
    """Absolute enable-edge differences from baseline beside the rule 6 verdict; reported, never a rule."""
    below = b['enable_edge_extremes_v'][0] - v['enable_edge_extremes_v'][0]
    above = v['enable_edge_extremes_v'][1] - b['enable_edge_extremes_v'][1]
    ref = RULE6_CONTRACT_REFERENCE[rail]
    out = {'below_baseline_minimum_v': below, 'above_baseline_maximum_v': above,
           'largest_excursion_beyond_baseline_v': max(0.0, below, above), 'resolution_v': VNTOL_V,
           'contract_reference': ref['quantity'], 'contract_reference_value_v': ref['value_v']}
    if ref['value_v'] is not None:
        out['variant_enable_edge_maximum_v'] = v['enable_edge_extremes_v'][1]
        out['distance_to_contract_reference_v'] = ref['value_v'] - v['enable_edge_extremes_v'][1]
    return out


def pre_enable_difference(base_record, record, kind):
    """Main-waveform difference before enable; amendment 1 makes the deck exactly baseline there."""
    a = [r for r in base_record['rows'] if r[0] < ENABLE_WINDOW_S[0]]
    b = [r for r in record['rows'] if r[0] < ENABLE_WINDOW_S[0]]
    same_grid = len(a) == len(b) and all(x[0] == y[0] for x, y in zip(a, b))
    diff = max((abs(x[k] - y[k]) for x, y in zip(a, b) for k in (1, 2, 3)), default=None) if same_grid else None
    return {'rows_before_40ms': [len(a), len(b)], 'same_time_grid': same_grid, 'max_output_difference_v': diff,
            'identical': same_grid and diff == 0.0,
            'identity_expected': kind == SCHEDULED}  # the constant worst case changes the deck before 40 ms by design


def judge(rail, variant_screens, baseline_screens, v, b):
    """Pre-registered pass rules (d1-gap-criteria.md); every rule must hold."""
    spec = RAILS[rail]
    rules = {
        'failed-rail slope, current and voltage-region ceilings': screen_passes(variant_screens[rail]),
        'other rails no worse than baseline': all(
            screen_passes(variant_screens[r]) or not screen_passes(baseline_screens[r]) for r in OTHER_RAILS if r != rail),
        'no new overshoot beyond baseline': v['overshoot_v'] <= b['overshoot_v'] + VNTOL_V,
        'no non-monotonic step beyond baseline': v['largest_drop_v'] >= b['largest_drop_v'] - VNTOL_V,
        'disabled state unchanged': within(v['disabled_extremes_v'], b['disabled_extremes_v']),
        'enable edge no excursion beyond baseline': within(v['enable_edge_extremes_v'], b['enable_edge_extremes_v']),
        'no conduction during the enable transient': not v['enable_conduction'],
    }
    if 'after_disable_vgs_max_v' in v:
        disabled_vgs = v['disabled_vgs_max_v']
        sign = spec['sign']
        floor = sign * b['disabled_extremes_v'][0 if sign > 0 else 1]
        after = [sign * x for x in v['after_disable_extremes_v']]
        before = [sign * x for x in v['pre_disable_extremes_v']]
        rules['disable edge: gate held off'] = v['after_disable_vgs_max_v'] <= disabled_vgs + VNTOL_V
        rules['disable edge: no excursion of either polarity'] = (max(after) <= max(before) + VNTOL_V
                                                                  and min(after) >= floor - VNTOL_V)
    else:
        rules['disable edge: gate held off'] = False
        rules['disable edge: no excursion of either polarity'] = False
    return rules


def analyze(work):
    work = Path(work)
    base_run = single_run(work)
    baseline = {name: case_record(base_run, name) for name in CASES}
    base_screens = {name: screens(baseline[name]) for name in CASES}
    result = {'scope': 'C1 gate-to-threshold gap sensitivity; model only, no claim about any real part',
              'electrical_acceptance': 'NOT ESTABLISHED', 'criteria': 'd1-gap-criteria.md', 'rails': {}}
    for rail, spec in RAILS.items():
        name = spec['case']
        b = rail_metrics(baseline[name], rail)
        b['screen'] = base_screens[name][rail]
        rows = {'baseline': {'target_gap_v': BASELINE_GAP_V[rail], **summary(b, base_screens[name][rail])}}
        for label in LABEL_ORDER:
            kind, shift = labels()[label][rail]
            try:
                status = case_status(work / 'gaps' / label, name)
            except (ValueError, OSError) as error:
                status = {'status': 'RUN FAILED', 'reason': f'{type(error).__name__}: {error}'}
            if status['status'] != 'COMPLETE':
                # Never a pass or a fail of the electrical rules (amendment 1); RUN FAILED is not a solver abort.
                aborted = [x for x in rows if rows[x].get('status') == 'ABORTED']
                if status['status'] == 'NOT RUN':
                    status['reason'] = (f'rail stopped after ABORTED {aborted[0]}; not retried in this dispatch' if aborted
                                        else 'no runner record for this case')
                rows[label] = {'kind': kind, 'shift_v': shift, 'target_gap_v': round(BASELINE_GAP_V[rail] - shift, 4),
                               **{k: x for k, x in status.items() if k != 'run'}, 'passes': None}
                continue
            try:
                record = case_record(status['run'], name)
                vs = screens(record)
                v = rail_metrics(record, rail)
                rules = judge(rail, vs, base_screens[name], v, b)
                rows[label] = {'kind': kind, 'shift_v': shift, 'target_gap_v': round(BASELINE_GAP_V[rail] - shift, 4),
                               'status': 'COMPLETE', **summary(v, vs[rail]), 'rules': rules, 'passes': all(rules.values()),
                               'edge_excursion_vs_baseline_v': {
                                   w: {'below': b[k][0] - v[k][0], 'above': v[k][1] - b[k][1]}
                                   for w, k in (('disabled', 'disabled_extremes_v'), ('enable', 'enable_edge_extremes_v'))},
                               'other_rails': {r: vs[r]['disposition'] for r in OTHER_RAILS if r != rail},
                               'rule6_detail': rule6_detail(rail, v, b),
                               'pre_enable_vs_baseline': pre_enable_difference(baseline[name], record, kind)}
            except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error:
                # A completed case whose evaluation fails is not a pass (fails closed).
                rows[label] = {'kind': kind, 'shift_v': shift, 'status': 'NOT EVALUATED',
                               'reason': f'{type(error).__name__}: {error}', 'passes': False}
        passing = [(r['target_gap_v'], r) for k, r in rows.items() if k != 'baseline' and r.get('passes')]
        best = max(passing, key=lambda x: x[0], default=None)
        result['rails'][rail] = {'case': name, 'rows': rows,
                                 'largest_passing_target_gap_v': None if best is None else best[0],
                                 'margin_at_largest_passing_gap': None if best is None else best[1]['margins']}
    return result


def summary(m, screen):
    ex = screen['exception']
    worst = ex['maximum_slope_in_voltage_region_v_per_ms'] if ex else screen['maximum']['slope_v_per_ms']
    out = {k: m.get(k) for k in ('floor_v', 'overshoot_v', 'largest_drop_v', 'conduction_onset_ms', 'rest_vgs_v',
                                 'onset_vgs_v', 'realized_gap_v', 'enable_vgs_max_v', 'enable_min_distance_to_conduction_v',
                                 'enable_peak_current_a', 'enable_conduction', 'disabled_extremes_v', 'enable_edge_extremes_v',
                                 'pre_disable_extremes_v', 'after_disable_extremes_v', 'after_disable_vgs_max_v')}
    out.update({'peak_slope_in_exception_region_v_per_ms': worst, 'peak_slope_v_per_ms': screen['maximum']['slope_v_per_ms'],
                'disposition': screen['disposition'],
                'capacitor_current_in_region_a': ex['maximum_current_in_voltage_region_a'] if ex else None})
    if ex:
        out['margins'] = {'slope_v_per_ms': round(ex['slope_ceiling_v_per_ms'] - worst, 6),
                          'current_a': round(ex['capacitive_current_ceiling_a'] - ex['maximum_current_in_voltage_region_a'], 6)}
    return out


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
        for name, status in bad.items():
            print(f'{args.label} {name}: {status}; not a solver abort, failing the step', file=sys.stderr)
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
