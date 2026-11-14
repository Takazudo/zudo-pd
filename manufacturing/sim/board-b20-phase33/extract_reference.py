"""D1 per-rail reference extraction (#235, wave 2 task W2-D).

Rebuilds the 2 us refined nom/adv inputs from Git plus the hash-recorded TI model archives,
appends one output-only wrdata line that saves the RAMP reference nodes, and after the
pinned runner has executed them checks that the primary and supplemental waveforms are
byte-identical to the retained 2026-11-09 refinement. Only then are the reference nodes
analysed against the D1 hypotheses.

Diagnostic only: electrical_acceptance stays NOT ESTABLISHED and the recorded 2 us ceiling
exceedances stay recorded failures. Vendor model bytes are never written to the output
evidence; only their hashes are.

usage:
  extract_reference.py prepare WORK --manifest PATH [--archives DIR]
  (run_ladder.py WORK/tracking nom adv --original-only)
  extract_reference.py identity WORK --manifest PATH --output PATH
  extract_reference.py analyze WORK --output PATH
  extract_reference.py collect WORK --evidence DIR [--extra-dir DIR]
  extract_reference.py record ARTIFACT_DIR --run-id N --artifact-id N --artifact-zip ZIP [--servo]
  extract_reference.py check-record

The work directory is not a Git checkout, so the runner receipt's source_revision is None and
its source_dirty means "not a repository"; the source is bound by GITHUB_SHA in the manifest.
"""
import argparse
import bisect
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
import zipfile

from analysis_inputs import load
from c12_compensation import INIT
from prepare_refinement import transform
import time

from run_ladder import IMAGE, VARIANTS, verify_executed_inputs
import servo_criteria

HERE = Path(__file__).resolve().parent
EXECUTION = HERE / 'execution-20261110.json'
REFINEMENT = HERE / 'startup-refinement-20261109.json'
CASES = ('nom', 'adv')
# Accepted executed variant of each case in the 2026-11-09 baseline (execution-20261110.json)
BASELINE_VARIANT = {'nom': 'original', 'adv': 'rshunt'}
REFERENCE_VECTORS = ('ramp', 'ramp_p12', 'ramp_p5', 'ramp_m12', 'clp12', 'clp5', 'clpm12')
ARCHIVES = {'sbomab6': {'OPAx187.LIB': 'lib/opax187.lib'},
            'slpm286': {'CSD18543Q3A.LIB': 'lib/csd18543q3a_ngspice.lib'}}
DOWNLOAD_TIMEOUT_S = 120
DOWNLOAD_MAX_BYTES = 64 * 1024 * 1024
# Excursion rail -> (case, main waveform column after time, reference node, clamp output node,
# sign of the output excursion relative to a rising reference: +5 tracks, -12 inverts)
FAILED = {'+5': ('nom', 2, 'ramp_p5', 'clp5', 1), '-12': ('adv', 3, 'ramp_m12', 'clpm12', -1)}
NEIGHBOURHOOD_S = 100e-6
# Reference slopes are compared between bin averages at the refined maximum step, so a sub-microsecond
# solver-timestep ring (adjacent-sample dV over a nanosecond dt) cannot fire the rule; see D1-H7.
GRID_S = 2e-6
# Reporting band for classification only; it is not a tolerance on any contract value.
IDEAL_BAND = 1.05
SUPPORTED, REFUTED, UNRESOLVED, NOT_RUN = 'SUPPORTED', 'REFUTED', 'UNRESOLVED', 'NOT RUN'


class NotRun(Exception):
    """A required external input is unavailable or differs from its recorded hash."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records():
    execution = json.loads(EXECUTION.read_text())
    refinement = json.loads(REFINEMENT.read_text())
    return execution['model_recovery'], refinement


def reference_line(name):
    return f"wrdata {name}-ref.txt " + ' '.join(f'v({v})' for v in REFERENCE_VECTORS)


def servo_line(name):
    return f"wrdata {name}-servo.txt " + ' '.join(f'v({v})' for v in servo_criteria.SERVO_VECTORS)


def convert_param(data):
    """Documented syntax-only conversion: exactly five '.PARAM name value' lines become 'name=value'."""
    pattern = re.compile(rb'^(\.PARAM[ \t]+[A-Za-z_][A-Za-z0-9_]*)[ \t]+([^ \t\r\n=]+)([ \t]*\r?)$', re.M | re.I)
    converted, count = pattern.subn(rb'\1=\2\3', data)
    if count != 5:
        raise ValueError(f'expected exactly five .PARAM name value lines, found {count}')
    return converted


def derive_decks():
    """Rebuild the refined decks from Git and add the one output-only reference line."""
    _, refinement = records()
    expected = refinement['preparation']['inputs']
    rshunt = dict(VARIANTS)['rshunt']
    decks = {}
    for name in CASES:
        text = (HERE / 'tracking' / f'{name}.cir').read_text()
        if BASELINE_VARIANT[name] == 'rshunt':
            if text.count(rshunt[0]) != 1:
                raise ValueError(f'{name}: expected one {rshunt[0]} for the accepted rshunt variant')
            text = text.replace(*rshunt)
        refined = transform(text, name)
        if sha(refined.encode()) != expected[f'tracking/{name}.cir']:
            raise ValueError(f'{name}: refined deck does not reproduce the recorded hash')
        if refined.count('.endc') != 1:
            raise ValueError(f'{name}: expected one control block')
        lines = [reference_line(name), servo_line(name)]
        decks[name] = {'refined': refined, 'executed': refined.replace('.endc', '\n'.join(lines) + '\n.endc'),
                       'added_lines': lines}
    return decks


def fetch(url, digest):
    """One bounded attempt; any failure or hash difference is NOT RUN, never retried here."""
    deadline = time.monotonic() + DOWNLOAD_TIMEOUT_S
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'phase33-reference-extraction'})
        chunks, size = [], 0
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_S) as response:
            while chunk := response.read(1 << 20):
                size += len(chunk)
                if size > DOWNLOAD_MAX_BYTES or time.monotonic() > deadline:
                    raise TimeoutError(f'exceeded {DOWNLOAD_MAX_BYTES} bytes or {DOWNLOAD_TIMEOUT_S} s')
                chunks.append(chunk)
        data = b''.join(chunks)
    except Exception as error:  # noqa: BLE001 - every transport failure is recorded verbatim
        raise NotRun(f'{url}: {type(error).__name__}: {error}') from error
    if sha(data) != digest:
        raise NotRun(f'{url}: sha256 {sha(data)} differs from recorded {digest}')
    return data


def build_models(archives, expected):
    """Return {lib path: bytes} from archives keyed by name, verifying members and outputs."""
    recovery, _ = records()
    built, hashes = {}, {}
    for name, members in ARCHIVES.items():
        data = archives[name]
        if sha(data) != recovery['files'][f'{name}.zip']:
            raise NotRun(f'{name}.zip differs from its recorded hash')
        hashes[f'{name}.zip'] = sha(data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member, target in members.items():
                found = [i for i in archive.namelist() if Path(i).name == member]
                if len(found) != 1:
                    raise NotRun(f'{name}.zip: expected one {member}, found {found}')
                raw = archive.read(found[0])
                if sha(raw) != recovery['files'][f'{name}/{member}']:
                    raise NotRun(f'{name}/{member} differs from its recorded hash')
                hashes[f'{name}/{member}'] = sha(raw)
                built[target] = convert_param(raw) if target.endswith('_ngspice.lib') else raw
    for target, data in built.items():
        if sha(data) != expected[target]:
            raise ValueError(f'{target}: built model {sha(data)} does not reproduce recorded {expected[target]}')
        hashes[target] = sha(data)
    return built, hashes


def prepare(work, archive_dir=None):
    recovery, refinement = records()
    expected = refinement['preparation']['inputs']
    if sha(INIT.encode()) != expected['tracking/.spiceinit']:
        raise ValueError('.spiceinit does not reproduce the recorded hash')
    decks = derive_decks()
    archives = {}
    for name in ARCHIVES:
        if archive_dir:
            archives[name] = (Path(archive_dir) / f'{name}.zip').read_bytes()
        else:
            archives[name] = fetch(recovery['source_urls'][name], recovery['files'][f'{name}.zip'])
    built, vendor = build_models(archives, expected)
    work = Path(work)
    (work / 'tracking').mkdir(parents=True)
    (work / 'lib').mkdir()
    for target, data in built.items():
        (work / target).write_bytes(data)
    (work / 'tracking/.spiceinit').write_text(INIT)
    manifest = {'source_revision': os.environ.get('GITHUB_SHA'), 'vendor_sha256': vendor,
                'spiceinit_sha256': sha(INIT.encode()), 'cases': {}}
    for name, deck in decks.items():
        (work / 'tracking' / f'{name}.cir').write_text(deck['executed'])
        manifest['cases'][name] = {'refined_deck_sha256': sha(deck['refined'].encode()),
                                   'executed_deck_sha256': sha(deck['executed'].encode()),
                                   'added_output_only_lines': deck['added_lines']}
    return manifest


def single_run(work):
    runs = sorted(Path(work).glob('ladder-*'))
    if len(runs) != 1:
        raise ValueError(f'{work}: expected exactly one runner directory, found {len(runs)}')
    return runs[0]


def attempt_dir(run, name):
    """Runner layout name/0/tracking; the uploaded evidence flattens it to name/ (collect)."""
    nested = Path(run) / name / '0' / 'tracking'
    return nested if nested.exists() or not (Path(run) / name / f'{name}.cir').exists() else Path(run) / name


def identity(run, manifest):
    """Byte identity of the executed decks and the retained primary/supplemental outputs."""
    _, refinement = records()
    receipt = json.loads((Path(run) / 'receipt.json').read_text())
    result = {'cases': {}}
    prepared = {k: v for k, v in refinement['preparation']['inputs'].items() if k.startswith('lib/')}
    solver = {refinement['cases'][name]['solver_version_output'] for name in CASES}
    ok = (receipt.get('status') == 'COMPLETE' and receipt.get('image') == IMAGE and receipt.get('platform') == 'linux/amd64'
          and receipt.get('variant_policy') == 'original-only' and len(solver) == 1
          and receipt.get('solver_version_output') in solver)
    result['solver_identity_matches'] = ok
    result['source_revision'] = manifest.get('source_revision')
    for name in CASES:
        work = attempt_dir(run, name)
        retained = refinement['cases'][name]
        observed = {'executed_deck': sha((work / f'{name}.cir').read_bytes()),
                    'main_waveform': sha((work / f'{name}.dat').read_bytes()),
                    'supplemental_waveform': sha((work / f'{name}-osc-cap.txt').read_bytes())}
        wanted = {'executed_deck': manifest['cases'][name]['executed_deck_sha256'],
                  'main_waveform': retained['main_waveform_sha256'],
                  'supplemental_waveform': retained['supplemental_waveform_sha256']}
        matches = {k: observed[k] == wanted[k] for k in observed}
        try:
            executed = verify_executed_inputs(Path(run) / name / '0', receipt['input_sha256'])
            matches['executed_models_and_settings'] = (
                {k: v for k, v in executed.items() if k.startswith('lib/')} == prepared
                and executed['tracking/.spiceinit'] == refinement['preparation']['inputs']['tracking/.spiceinit'])
        except (ValueError, KeyError, OSError) as error:
            matches['executed_models_and_settings'] = False
            observed['executed_inputs_error'] = str(error)
        ok = ok and all(matches.values())
        result['cases'][name] = {'observed_sha256': observed, 'expected_sha256': wanted, 'matches': matches}
    result['status'] = 'REPRODUCED' if ok else 'NOT REPRODUCED'
    return result


def load_reference(path, rows, vectors=REFERENCE_VECTORS):
    data = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        values = [float(x) for x in line.split()]
        if len(values) != 2 * len(vectors):
            raise ValueError(f'{path}:{number}: expected {2 * len(vectors)} columns')
        if any(abs(x - values[0]) > 1e-10 for x in values[::2]):
            raise ValueError(f'{path}:{number}: wrdata time columns disagree')
        data.append(dict(zip(('t',) + tuple(vectors), (values[0], *values[1::2]))))
    if len(data) != len(rows) or any(abs(a['t'] - b[0]) > 1e-12 for a, b in zip(data, rows)):
        raise ValueError(f'{path}: reference and main waveform time coordinates differ')
    return data


def deck_gain(deck, rail):
    """Ideal tracking gain from the drawn feedback resistors of the executed deck."""
    values = {}
    for line in deck.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] in ('RT5A', 'RT5B', 'RT12NA', 'RT12NB'):
            values[parts[0]] = float(parts[3].lower().replace('k', 'e3'))
    if rail == '+5':
        return 1 + values['RT5A'] / values['RT5B']
    return values['RT12NB'] / values['RT12NA']


def slopes(times, values, gain):
    """Signed adjacent-sample slopes in V/ms, multiplied by gain (use the sign to select the excursion direction)."""
    return [gain * (values[i + 1] - values[i]) / (times[i + 1] - times[i]) / 1e3 for i in range(len(times) - 1)]


def integral_at(times, values, cumulative, t):
    """Exact integral of the piecewise-linear waveform from times[0] to t, for t inside the record."""
    k = min(max(bisect.bisect_right(times, t), 1), len(times) - 1) - 1
    v = values[k] + (values[k + 1] - values[k]) * (t - times[k]) / (times[k + 1] - times[k])
    return cumulative[k] + (t - times[k]) * (values[k] + v) / 2


def grid_slopes(times, values, gain, start, end):
    """Signed slopes in V/ms between adjacent GRID_S bin averages, bins anchored at start over the +/-NEIGHBOURHOOD_S window.

    Bin averaging (not point resampling) bounds a nanosecond ring's effect by its area, so a grid point
    that happens to land inside a solver-timestep ring cannot fire the rule.
    """
    cumulative = [0.0]
    for i in range(len(times) - 1):
        cumulative.append(cumulative[-1] + (times[i + 1] - times[i]) * (values[i] + values[i + 1]) / 2)
    first = -int(round(NEIGHBOURHOOD_S / GRID_S)) - 1
    last = int(round((end - start + NEIGHBOURHOOD_S) / GRID_S)) + 1
    edges = [t for t in (start + k * GRID_S for k in range(first, last + 1)) if times[0] <= t <= times[-1]]
    area = [integral_at(times, values, cumulative, t) for t in edges]
    means = [(area[i + 1] - area[i]) / GRID_S for i in range(len(edges) - 1)]
    return [(edges[i + 1], gain * (means[i + 1] - means[i]) / GRID_S / 1e3) for i in range(len(means) - 1)]


def cluster(times, values, peak):
    """Sub-grid solver-timestep cluster (steps shorter than GRID_S/100) containing adjacent interval peak, or None."""
    short = lambda i: times[i + 1] - times[i] < GRID_S / 100
    if not short(peak):
        return None
    first = last = peak
    while first > 0 and short(first - 1):
        first -= 1
    while last + 1 < len(times) - 1 and short(last + 1):
        last += 1
    flips = sum(1 for i in range(first, last) if (values[i + 1] - values[i]) * (values[i + 2] - values[i + 1]) < 0)
    return first, last, flips


def timestep_artefact(adjacent_peak, grid_peak, ceiling, ring):
    """D1-H7: the adjacent-sample rule fires only on a sub-grid ring (short steps with alternating increments)."""
    if adjacent_peak < ceiling:
        return 'NOT APPLICABLE (the adjacent-sample rule did not fire)'
    if grid_peak >= ceiling:
        return REFUTED
    return SUPPORTED if ring is not None and ring[2] >= 2 else UNRESOLVED


def classify(peak, ideal, ceiling, competing=None):
    """Pre-registered rule on signed slopes in the excursion direction.

    SUPPORTED needs the scaled slope to reach the failed ceiling and, when a competing source
    is named (the common RAMP for the per-rail reference), to exceed that source's peak by the
    same band, so a reference that only follows a steep common RAMP is not attributed to the clamp.
    """
    if peak <= ideal * IDEAL_BAND:
        return REFUTED
    if peak >= ceiling and (competing is None or peak > competing * IDEAL_BAND):
        return SUPPORTED
    return UNRESOLVED


def bin_mean(times, values):
    """Callable (t0, t1) -> mean of the piecewise-linear waveform over [t0, t1]."""
    cumulative = [0.0]
    for i in range(len(times) - 1):
        cumulative.append(cumulative[-1] + (times[i + 1] - times[i]) * (values[i] + values[i + 1]) / 2)

    def mean(t0, t1):
        if not times[0] <= t0 < t1 <= times[-1]:
            raise ValueError(f'bin {t0}..{t1} lies outside the waveform record')
        return (integral_at(times, values, cumulative, t1) - integral_at(times, values, cumulative, t0)) / (t1 - t0)
    return mean


def servo_analysis(work, name, rail, rows, ref_name, gain, sign, start, end):
    """Pre-registered servo/dead-zone criteria (servo_criteria.py, d1-servo-criteria.md) on 2 us bin means."""
    path = work / f'{name}-servo.txt'
    if not path.exists():
        return servo_criteria.unresolved('servo vectors were not saved by this run', status=NOT_RUN)
    try:
        spec = servo_criteria.SERVO[rail]
        deck = (work / f'{name}.cir').read_text()
        topo = servo_criteria.topology(deck, rail)
        servo = load_reference(path, rows, servo_criteria.SERVO_VECTORS)
        ref = load_reference(work / f'{name}-ref.txt', rows)
        times = [r[0] for r in rows]
        nodes = {v: [x[v] for x in servo] for v in servo_criteria.SERVO_VECTORS}
        nodes.update({v: [x[v] for x in ref] for v in REFERENCE_VECTORS})
        nodes.update({v: [r[i + 1] for r in rows] for i, v in enumerate(servo_criteria.MAIN_VECTORS)})
        if 'trk12n' in (topo['plus_input'], topo['minus_input']):
            elements = servo_criteria.deck_elements(deck)
            ra = float(elements['RT12NA'][3].lower().replace('k', 'e3'))
            rb = float(elements['RT12NB'][3].lower().replace('k', 'e3'))
            nodes['trk12n'] = [rm + (o - rm) * ra / (ra + rb) for rm, o in zip(nodes['ramp_m12'], nodes['m12_out'])]
        error = [p - m for p, m in zip(nodes[topo['plus_input']], nodes[topo['minus_input']])]
        driver = nodes[spec['driver']]
        driver_mean = bin_mean(times, driver)
        settled = [servo_criteria.SETTLED_S + k * servo_criteria.BIN_S
                   for k in range(int((times[-1] - servo_criteria.SETTLED_S) / servo_criteria.BIN_S))]
        lower = topo['supplies_v'][0]
        reached = any(abs(driver_mean(a, b) - lower) <= servo_criteria.RAIL_BAND_V for a, b in zip(settled, settled[1:]))
        series = {'out': bin_mean(times, nodes[('p5_out', 'm12_out')[rail == '-12']]),
                  'ref': bin_mean(times, nodes[ref_name]),
                  'current': bin_mean(times, [r[spec['current_column']] for r in rows]),
                  'gate': bin_mean(times, nodes[spec['gate_node']]),
                  'driver': bin_mean(times, driver),
                  'source': bin_mean(times, nodes[spec['source']]),
                  'error': bin_mean(times, error)}
        result = servo_criteria.evaluate(series, start, end, gain, sign, topo['supplies_v'], topo['gate_offset_v'], reached)
    except (ValueError, KeyError, IndexError, OSError, ArithmeticError) as error_:
        return servo_criteria.unresolved(f'servo analysis failed: {error_}', status='FAILED')
    result['topology'] = {'driver': spec['driver'], 'amplifier': spec['amplifier'], **topo,
                          'lower_supply_band_reachable_after_settling': reached}
    return result


def analyze(run):
    _, refinement = records()
    calc_spec = importlib.util.spec_from_file_location('interface_diagnostics', HERE / 'interface_diagnostics.py')
    diag = importlib.util.module_from_spec(calc_spec)
    calc_spec.loader.exec_module(diag)
    ideal = diag.ideal_tracking_slopes(diag.calculator())
    result = {'scope': 'D1 reference extraction; diagnostic only', 'electrical_acceptance': 'NOT ESTABLISHED',
              'classification_rule': f'Signed slopes in the excursion direction within +/-{NEIGHBOURHOOD_S * 1e6:g} us of the '
                                     f'recorded excursion, taken between adjacent {GRID_S * 1e6:g} us bin averages and scaled by the deck '
                                     f'tracking gain. REFUTED if the peak stays at or below {IDEAL_BAND} x the ideal tracking slope. '
                                     f'SUPPORTED if it reaches the failed exception ceiling and, for the per-rail reference, also '
                                     f'exceeds {IDEAL_BAND} x the scaled common-RAMP peak. Otherwise UNRESOLVED. Clamp-diode release '
                                     f'is REFUTED when the diode stays reverse-biased across the window. SUPPORTED means consistent '
                                     f'with the hypothesis in this model, not proof of cause.',
              'rails': {}}
    for rail, (name, column, ref_name, clamp, sign) in FAILED.items():
        work = attempt_dir(run, name)
        rows = load(work / f'{name}.dat')
        ref = load_reference(work / f'{name}-ref.txt', rows)
        recorded = refinement['cases'][name]['rails'][rail]
        worst = recorded['worst_recorded_bound_exceedance']
        ceiling = recorded['exception']['slope_ceiling_v_per_ms']
        gain = deck_gain((work / f'{name}.cir').read_text(), rail)
        start, end = worst['start_ms'] / 1e3, worst['end_ms'] / 1e3
        index = min(range(len(rows) - 1), key=lambda i: abs(rows[i][0] - start) + abs(rows[i + 1][0] - end))
        near = [i for i in range(len(rows) - 1) if start - NEIGHBOURHOOD_S <= rows[i][0] <= end + NEIGHBOURHOOD_S]
        times = [r[0] for r in rows]
        out = slopes(times, [r[column] for r in rows], sign)
        if abs(out[index] - worst['slope_v_per_ms']) > 1e-9 * worst['slope_v_per_ms']:
            raise ValueError(f'{rail}: selected segment slope {out[index]} differs from recorded {worst["slope_v_per_ms"]}')
        reference_values = [x[ref_name] for x in ref]
        reference = slopes(times, reference_values, gain)
        common = slopes(times, [x['ramp'] for x in ref], gain)
        reference_grid = grid_slopes(times, reference_values, gain, start, end)
        common_grid = grid_slopes(times, [x['ramp'] for x in ref], gain, start, end)
        diode = [ref[i][ref_name] - ref[i][clamp] for i in near + [near[-1] + 1]]
        adjacent_peak_at = max(near, key=lambda i: reference[i])
        ring = cluster(times, reference_values, adjacent_peak_at)
        reference_peak_at, reference_peak = max(reference_grid, key=lambda x: x[1])
        common_peak = max(slope for _, slope in common_grid)
        ideal_slope = ideal[rail]
        result['rails'][rail] = {
            'case': name, 'tracking_gain_from_deck': round(gain, 6),
            'excursion_segment_ms': [round(rows[index][0] * 1e3, 9), round(rows[index + 1][0] * 1e3, 9)],
            'output_slope_at_segment_v_per_ms': out[index], 'recorded_slope_v_per_ms': worst['slope_v_per_ms'],
            'scaled_reference_slope_at_segment_v_per_ms': reference[index],
            'scaled_reference_peak_near_segment_v_per_ms': reference_peak,
            'scaled_reference_peak_offset_from_segment_us': round((reference_peak_at - rows[index][0]) * 1e6, 3),
            'scaled_common_ramp_slope_at_segment_v_per_ms': common[index],
            'scaled_common_ramp_peak_near_segment_v_per_ms': common_peak,
            'adjacent_sample_scaled_reference_peak_v_per_ms': reference[adjacent_peak_at],
            'adjacent_sample_peak_offset_from_segment_us': round((rows[adjacent_peak_at][0] - rows[index][0]) * 1e6, 3),
            'adjacent_sample_peak_dt_s': times[adjacent_peak_at + 1] - times[adjacent_peak_at],
            'adjacent_sample_peak_cluster_sign_reversals': None if ring is None else ring[2],
            'minimum_timestep_in_window_s': min(times[i + 1] - times[i] for i in near),
            'ideal_tracking_max_slope_v_per_ms': ideal_slope,
            'exception_slope_ceiling_v_per_ms': ceiling,
            'clamp_diode_voltage_v': {'window_start': diode[0], 'segment': diode[near.index(index)],
                                      'window_end': diode[-1], 'window_min': min(diode), 'window_max': max(diode)},
            'hypotheses': {
                'D1-H6 reference-side edge': classify(reference_peak, ideal_slope, ceiling, common_peak),
                'D1-H6 clamp-diode release': REFUTED if max(diode) < 0 else UNRESOLVED,
                'D1-H1 recorded common RAMP too steep': classify(common_peak, ideal_slope, ceiling),
                'D1-H7 adjacent-sample trigger is a solver-timestep artefact':
                    timestep_artefact(reference[adjacent_peak_at], reference_peak, ceiling, ring),
                'D1-H4 pre-bias overshoot': UNRESOLVED + ' (needs the paired variant run)'},
        }
        result['rails'][rail]['servo'] = servo_analysis(work, name, rail, rows, ref_name, gain, sign, start, end)
    return result


def timestep_ring(run, rail='-12'):
    """Describe the sub-grid solver-timestep cluster behind the adjacent-sample reference peak."""
    name, _, ref_name, clamp, _ = FAILED[rail]
    work = attempt_dir(run, name)
    ref = load_reference(work / f'{name}-ref.txt', load(work / f'{name}.dat'))
    times = [x['t'] for x in ref]
    worst = records()[1]['cases'][name]['rails'][rail]['worst_recorded_bound_exceedance']
    low, high = worst['start_ms'] / 1e3 - NEIGHBOURHOOD_S, worst['end_ms'] / 1e3 + NEIGHBOURHOOD_S
    gain = deck_gain((work / f'{name}.cir').read_text(), rail)
    values = [x[ref_name] for x in ref]
    adjacent = slopes(times, values, gain)
    peak = max((i for i in range(len(adjacent)) if low <= times[i] <= high), key=lambda i: adjacent[i])
    found = cluster(times, values, peak)
    if found is None:
        raise ValueError(f'{rail}: the adjacent-sample peak is not inside a sub-grid timestep cluster')
    first, last, flips = found
    span = range(first, last + 2)
    return {'rail': rail, 'node': ref_name, 'peak_time_ms': round(times[peak] * 1e3, 9),
            'adjacent_scaled_peak_v_per_ms': adjacent[peak], 'adjacent_peak_dv_v': values[peak + 1] - values[peak],
            'adjacent_peak_dt_s': times[peak + 1] - times[peak],
            'cluster_start_ms': round(times[first] * 1e3, 9), 'cluster_end_ms': round(times[last + 1] * 1e3, 9),
            'cluster_samples': len(span), 'cluster_min_dt_s': min(times[i + 1] - times[i] for i in range(first, last + 1)),
            'node_peak_to_peak_in_cluster_v': max(values[i] for i in span) - min(values[i] for i in span),
            'node_sign_reversals_in_cluster': flips,
            'clamp_output_at_cluster_start_v': ref[first][clamp], 'clamp_output_at_cluster_end_v': ref[last + 1][clamp]}


RECORD = HERE / 'd1-reference-20261111.json'
RECORD_MD = HERE / 'd1-reference-20261111.md'
MISREADING = ('Before adoption, the −12 V in-job result was first reported as a 0.85 V reference-side step. That was a '
              'misreading: the 0.85 V is the gradual rise of the XU16A clamp output (clpm12) across the window, and the '
              'reference jump is the millivolt-scale timestep ring described under timestep_artefact. The report was '
              'corrected and nothing was adopted from it.')


def verified_artifact(evidence):
    """Check every file listed in the artifact's hashes.json; refuse anything unlisted or changed."""
    evidence = Path(evidence)
    listed = json.loads((evidence / 'hashes.json').read_text())
    present = {str(p.relative_to(evidence)) for p in evidence.rglob('*') if p.is_file()} - {'hashes.json'}
    if present != set(listed):
        raise ValueError(f'artifact files differ from hashes.json: {sorted(present ^ set(listed))}')
    for name, digest in listed.items():
        if sha((evidence / name).read_bytes()) != digest:
            raise ValueError(f'{name}: hash differs from hashes.json')
    runs = sorted(p for p in evidence.glob('ladder-*') if p.is_dir())
    if len(runs) != 1:
        raise ValueError(f'{evidence}: expected exactly one runner directory, found {len(runs)}')
    return listed, runs[0]


def verified_reproduction(evidence):
    """Hash-checked artifact whose identity control reproduced; waveforms re-checked locally."""
    evidence = Path(evidence)
    listed, run = verified_artifact(evidence)
    _, refinement = records()
    identity_result = json.loads((evidence / 'identity.json').read_text())
    if identity_result['status'] != 'REPRODUCED' or not all(
            all(case['matches'].values()) for case in identity_result['cases'].values()):
        raise ValueError('identity control did not reproduce; nothing is adopted')
    for name in CASES:  # re-check the waveform identity locally instead of trusting identity.json alone
        work = attempt_dir(run, name)
        retained = refinement['cases'][name]
        if (sha((work / f'{name}.dat').read_bytes()) != retained['main_waveform_sha256']
                or sha((work / f'{name}-osc-cap.txt').read_bytes()) != retained['supplemental_waveform_sha256']):
            raise ValueError(f'{name}: waveforms differ from the retained refinement')
    manifest = json.loads((evidence / 'manifest.json').read_text())
    return listed, run, refinement, identity_result, manifest


def failures_preserved(analysis, refinement):
    for rail, (name, *_rest) in FAILED.items():
        recorded = refinement['cases'][name]['rails'][rail]
        slope = recorded['worst_recorded_bound_exceedance']['slope_v_per_ms']
        if analysis['rails'][rail]['output_slope_at_segment_v_per_ms'] != slope:
            raise ValueError(f'{rail}: output slope no longer equals the recorded failure')
        if not slope > recorded['exception']['slope_ceiling_v_per_ms']:
            raise ValueError(f'{rail}: the recorded slope is no longer a failure; the record wording would be false')
    return {rail: refinement['cases'][name]['rails'][rail]['worst_recorded_bound_exceedance']['slope_v_per_ms']
            for rail, (name, *_rest) in FAILED.items()}


def run_header(listed, identity_result, manifest, run_id, artifact_id, artifact_zip):
    return {
        'run': {'workflow': '.github/workflows/phase33-d1-reference.yml', 'run_id': run_id,
                'source_revision': manifest['source_revision'], 'artifact_id': artifact_id,
                'artifact_zip_sha256': sha(Path(artifact_zip).read_bytes()), 'artifact_files_sha256': listed},
        'inputs': {'vendor_sha256': manifest['vendor_sha256'], 'spiceinit_sha256': manifest['spiceinit_sha256'],
                   'cases': manifest['cases']},
        'identity': {'status': identity_result['status'], 'source_revision': identity_result['source_revision'],
                     'solver_identity_matches': identity_result['solver_identity_matches'],
                     'cases': {name: case['matches'] for name, case in identity_result['cases'].items()}},
    }


def build_record(evidence, run_id, artifact_id, artifact_zip):
    listed, run, refinement, identity_result, manifest = verified_reproduction(evidence)
    in_job = json.loads((Path(evidence) / 'analysis.json').read_text())
    analysis = analyze(run)
    return {
        'scope': 'D1 reference extraction adoption (#235); diagnostic only',
        'electrical_acceptance': 'NOT ESTABLISHED',
        'recorded_failures_preserved': failures_preserved(analysis, refinement),
        **run_header(listed, identity_result, manifest, run_id, artifact_id, artifact_zip),
        'superseded_in_job_analysis': {
            'sha256': listed['analysis.json'],
            'rule': 'adjacent-sample slopes',
            'hypotheses': {rail: row['hypotheses'] for rail, row in in_job['rails'].items()},
            'reason': 'Adjacent-sample differentiation is replaced by 2 us bin averages so a sub-grid solver-timestep '
                      'ring cannot fire the reference rule (see D1-H7).',
            'corrected_attempt': MISREADING},
        'analysis': analysis,
        'timestep_artefact': timestep_ring(run),
    }


def _fmt(x, digits=4):
    return f'{x:.{digits}f}'


def render_markdown(record):
    a, ring, run = record['analysis']['rails'], record['timestep_artefact'], record['run']
    hyp = lambda rail, key: next(v for k, v in a[rail]['hypotheses'].items() if k.startswith(key))
    lines = [
        '# D1 reference extraction — 2026-11-11',
        '',
        f"**Diagnostic only. electrical_acceptance: {record['electrical_acceptance']}.** The recorded 2 us failures stay "
        'failures: ' + ', '.join(f"{rail.replace('-', '−')} V {v:.9f} V/ms" for rail, v in record['recorded_failures_preserved'].items()) + '.',
        '',
        f"Run `{run['run_id']}` of `{run['workflow']}` at `{run['source_revision']}`; artifact `{run['artifact_id']}` "
        f"(zip sha256 `{run['artifact_zip_sha256']}`). Identity control: **{record['identity']['status']}** "
        '(executed decks, primary and supplemental waveforms byte-identical to the 2026-11-09 refinement). '
        'Each executed deck differs from the refined deck by one output-only line:',
        '',
    ]
    lines += [f"- {name}: `{case['added_output_only_line']}`" for name, case in record['inputs']['cases'].items()]
    lines += [
        '',
        f"Reference slopes are taken between adjacent {GRID_S * 1e6:g} us bin averages (the refined maximum step) within "
        f"±{NEIGHBOURHOOD_S * 1e6:g} us of each excursion and scaled by the deck tracking gain.",
        '',
        '| Hypothesis | +5 V (nom) | −12 V (adv) |',
        '| --- | --- | --- |',
    ]
    for key, label in (('D1-H6 reference-side', 'Reference-side edge (D1-H6)'),
                       ('D1-H6 clamp-diode', 'Clamp-diode release (D1-H6)'),
                       ('D1-H1', 'Recorded common RAMP too steep (D1-H1)'),
                       ('D1-H7', 'Adjacent-sample trigger is a solver-timestep artefact (D1-H7)'),
                       ('D1-H4', 'Pre-bias overshoot (D1-H4)')):
        lines.append(f"| {label} | {hyp('+5', key)} | {hyp('-12', key)} |")
    lines += ['', '| Quantity | +5 V | −12 V |', '| --- | ---: | ---: |']
    for key, label, digits in (('output_slope_at_segment_v_per_ms', 'Output slope at the failed segment (V/ms)', 9),
                               ('scaled_reference_peak_near_segment_v_per_ms', 'Scaled reference peak, 2 us bins (V/ms)', 4),
                               ('scaled_common_ramp_peak_near_segment_v_per_ms', 'Scaled common RAMP peak, 2 us bins (V/ms)', 4),
                               ('ideal_tracking_max_slope_v_per_ms', 'Ideal tracking slope (V/ms)', 4),
                               ('exception_slope_ceiling_v_per_ms', 'Exception ceiling (V/ms)', 2),
                               ('adjacent_sample_scaled_reference_peak_v_per_ms', 'Adjacent-sample scaled reference peak (V/ms)', 4)):
        lines.append(f"| {label} | {_fmt(a['+5'][key], digits)} | {_fmt(a['-12'][key], digits)} |")
    lines.append('| Clamp-diode voltage across window (V) | '
                 + ' | '.join(f"{_fmt(a[r]['clamp_diode_voltage_v']['window_min'], 3)} to "
                              f"{_fmt(a[r]['clamp_diode_voltage_v']['window_max'], 3)}" for r in ('+5', '-12')) + ' |')
    lines += [
        '',
        f"The −12 V adjacent-sample peak is {ring['adjacent_peak_dv_v'] * 1e3:.3f} mV over "
        f"{ring['adjacent_peak_dt_s'] * 1e9:.2f} ns at {ring['peak_time_ms']:.6f} ms, inside a cluster of "
        f"{ring['cluster_samples']} samples ({ring['cluster_start_ms']:.6f}–{ring['cluster_end_ms']:.6f} ms, minimum step "
        f"{ring['cluster_min_dt_s'] * 1e9:.3f} ns) where {ring['node']} rings {ring['node_peak_to_peak_in_cluster_v'] * 1e3:.3f} mV "
        f"peak to peak with {ring['node_sign_reversals_in_cluster']} sign reversals, as the XU16A clamp output reaches "
        f"{ring['clamp_output_at_cluster_start_v']:.3f} V. "
        + ('On 2 us bins the reference stays within the ideal tracking band on both rails, so the reference side '
           'does not explain either excursion; the excursions lie downstream of the reference.'
           if all(hyp(r, 'D1-H6 reference-side') == REFUTED for r in a) else
           'The reference side is not refuted on every rail; see the hypothesis table.'),
        '',
        '**Corrected attempt.** The in-job analysis used adjacent-sample slopes and classified the reference edge as '
        + ', '.join(f"{v.get('D1-H6 clamp-release reference edge')} ({rail.replace('-', '−')} V)"
                    for rail, v in record['superseded_in_job_analysis']['hypotheses'].items())
        + '. ' + record['superseded_in_job_analysis']['corrected_attempt'],
        '',
        'No pre-bias variant, correction candidate, contract change or tolerance is adopted. '
        '`d1-reference-20261111.json` holds every hash and value.',
        '',
    ]
    return '\n'.join(lines)


SERVO_RECORD = HERE / 'd1-servo-20261111.json'
SERVO_RECORD_MD = HERE / 'd1-servo-20261111.md'
SERVO_CRITERIA = 'd1-servo-criteria.md'
# Predictions stated in d1-servo-criteria.md before the run; the record compares each verdict with them.
SERVO_PREDICTIONS = {
    'servo wound up at a supply before conduction': (SUPPORTED,),
    'windup released when the reference passes the pre-bias floor': (REFUTED, UNRESOLVED),
    'peak slope coincides with driver recovery': ('NO',),
    'dead zone set by': ('CONDUCTION THRESHOLD AFTER WINDUP',),
}


def prediction_met(question, verdict):
    return any(verdict.startswith(p) for p in SERVO_PREDICTIONS[question])


def build_servo_record(evidence, run_id, artifact_id, artifact_zip):
    """Adopt the servo-node run: the in-job servo evaluation must equal a local re-evaluation of the same files."""
    listed, run, refinement, identity_result, manifest = verified_reproduction(evidence)
    in_job = json.loads((Path(evidence) / 'analysis.json').read_text())
    analysis = analyze(run)
    servo = {rail: row['servo'] for rail, row in analysis['rails'].items()}
    if json.dumps({rail: row['servo'] for rail, row in in_job['rails'].items()}, sort_keys=True) != json.dumps(servo, sort_keys=True):
        raise ValueError('the in-job servo evaluation differs from the local re-evaluation; nothing is adopted')
    if any(row['status'] != 'EVALUATED' for row in servo.values()):
        raise ValueError('a rail was not evaluated; the run is reported, not adopted')
    return {
        'scope': 'D1 servo-node extraction adoption (#235); diagnostic only',
        'electrical_acceptance': 'NOT ESTABLISHED',
        'criteria': {'document': SERVO_CRITERIA, 'implementation': 'servo_criteria.py',
                     'predictions': {q: list(v) for q, v in SERVO_PREDICTIONS.items()}},
        'recorded_failures_preserved': failures_preserved(analysis, refinement),
        **run_header(listed, identity_result, manifest, run_id, artifact_id, artifact_zip),
        'in_job_analysis_sha256': listed['analysis.json'],
        'servo': servo,
        'predictions_met': {rail: {q: prediction_met(q, v) for q, v in row['verdicts'].items()}
                            for rail, row in servo.items()},
    }


def render_servo_markdown(record):
    s, run = record['servo'], record['run']
    rails = ('+5', '-12')
    head = lambda r: f"{r.replace('-', '−')} V ({s[r]['topology']['amplifier']} `{s[r]['topology']['driver']}`)"
    ms = lambda x: '—' if x is None else f'{x:.3f} ms'
    us = lambda x: '—' if x is None else f'{x / 1e3:.3f} ms' if abs(x) >= 1000 else f'{x:.0f} µs'
    lines = [
        '# D1 servo-node extraction — 2026-11-11',
        '',
        f"**Diagnostic only. electrical_acceptance: {record['electrical_acceptance']}.** The recorded 2 us failures stay "
        'failures: ' + ', '.join(f"{rail.replace('-', '−')} V {v:.9f} V/ms" for rail, v in record['recorded_failures_preserved'].items()) + '.',
        '',
        f"Run `{run['run_id']}` of `{run['workflow']}` at `{run['source_revision']}`; artifact `{run['artifact_id']}` "
        f"(zip sha256 `{run['artifact_zip_sha256']}`). Identity control: **{record['identity']['status']}** "
        '(primary and supplemental waveforms byte-identical to the 2026-11-09 refinement). '
        'Each executed deck differs from the refined deck only by output-only lines:',
        '',
    ]
    for name, case in record['inputs']['cases'].items():
        lines += [f'- {name}: `{line}`' for line in case.get('added_output_only_lines', [case.get('added_output_only_line')])]
    lines += [
        '',
        f"Verdicts follow the rules pre-registered in [{SERVO_CRITERIA}]({SERVO_CRITERIA}) on 2 us bin means; the in-job "
        'evaluation equals a local re-evaluation of the same files.',
        '',
        f'| Question | {head("+5")} | {head("-12")} | Predicted |',
        '| --- | --- | --- | --- |',
    ]
    for q, predicted in SERVO_PREDICTIONS.items():
        cells = [f"{s[r]['verdicts'][q]}{'' if record['predictions_met'][r][q] else ' (not as predicted)'}" for r in rails]
        lines.append(f"| {q[0].upper() + q[1:]} | {cells[0]} | {cells[1]} | {' or '.join(predicted)} |")
    rows = (
        ('Driver parked before conduction (inside the 20 ms window)', lambda r: us(s[r]['driver_parked_in_window_before_conduction_us'])),
        ('Last exit from the supply', lambda r: ms(s[r]['driver_last_supply_exit_ms'])),
        ('Exit to conduction onset', lambda r: us(s[r]['exit_to_conduction_us'])),
        ('Exit to failed segment', lambda r: us(s[r]['exit_to_segment_us'])),
        ('Servo error last rises through zero', lambda r: ms(s[r]['servo_error_last_rise_through_zero_before_conduction_ms'])),
        ('Conduction onset (≥ 5 mA)', lambda r: ms(s[r]['conduction_onset_ms'])),
        ('Conduction onset to failed segment', lambda r: us(s[r]['conduction_onset_to_segment_us'])),
        ('Ideal-lag start (> 50 mV)', lambda r: ms(s[r]['ideal_lag_start_ms'])),
        ('Output at driver exit', lambda r: f"{s[r]['output_at_driver_exit_v']:+.4f} V".replace('-', '−')),
        ('Vgs at climb start / onset / segment', lambda r: ' / '.join(f"{s[r]['vgs_v'][k]:.3f}".replace('-', '−') for k in ('climb_start', 'conduction_onset', 'segment')) + ' V'),
        ('Maximum lag / lag at segment', lambda r: f"{s[r]['maximum_lag_v']:.3f} / {s[r]['lag_at_segment_v']:.3f} V"),
    )
    lines += ['', '| Quantity | +5 V | −12 V |', '| --- | ---: | ---: |']
    lines += [f'| {label} | {f("+5")} | {f("-12")} |' for label, f in rows]
    threshold = all(s[r]['verdicts']['dead zone set by'].startswith('CONDUCTION THRESHOLD') for r in rails)
    lines += [
        '',
        ('On both rails the driver leaves its supply long before the excursion and the pass pair conducts only after '
         'Vgs has climbed through its threshold; the output waits on its pre-bias floor meanwhile and then catches up. '
         'The dead zone is set by the conduction threshold, not by the windup or by the floor value.'
         if threshold else 'The dead-zone class differs between rails or is unresolved; see the table.'),
        '',
        'No correction, contract change or tolerance is adopted. `d1-servo-20261111.json` holds every hash and value.',
        '',
    ]
    return '\n'.join(lines)


EVIDENCE_SUFFIXES = ('.cir', '.dat', '.log', '-osc-cap.txt', '-ref.txt', '-servo.txt', '-gap.txt', '-t2.txt', '-a2.txt')
EVIDENCE_CASES = CASES + ('nomR', 'reR6', 'reR20')  # the loaded decks of the T2 evaluation (d1-t2-criteria.md)
VENDOR_SUFFIXES = ('.lib', '.zip', '.olb')


def collect(work, evidence, extra_dir=None):
    """Copy decks, logs, waveforms, receipts and reports; never vendor model bytes. Returns the hash list."""
    evidence = Path(evidence)
    evidence.mkdir(parents=True)
    work = Path(work)
    runs = sorted(work.glob('ladder-*')) + sorted(work.glob('gaps/*/ladder-*')) + sorted(work.glob('t2/*/ladder-*')) + sorted(work.glob('itl4/*/ladder-*')) + sorted(work.glob('bank/*/ladder-*')) + sorted(work.glob('ceiling/*/ladder-*')) + sorted(work.glob('xcheck/*/ladder-*')) + sorted(work.glob('r10/*/ladder-*')) + sorted(work.glob('d2fd/*/ladder-*')) + sorted(work.glob('d2sq/*/ladder-*'))
    sources = []
    for run in runs:
        prefix = run.relative_to(work).as_posix()
        sources.append((run / 'receipt.json', f'{prefix}/receipt.json'))
        for name in EVIDENCE_CASES:
            for suffix in EVIDENCE_SUFFIXES:
                path = attempt_dir(run, name) / f'{name}{suffix}'
                if path.is_file():
                    sources.append((path, f'{prefix}/{name}/{name}{suffix}'))
    if extra_dir and Path(extra_dir).is_dir():
        sources += [(p, p.name) for p in sorted(Path(extra_dir).iterdir()) if p.is_file()]
    hashes = {}
    for source, relative in sources:
        if source.suffix.lower() in VENDOR_SUFFIXES or 'lib' in Path(relative).parts:
            raise ValueError(f'refusing to collect vendor model bytes: {relative}')
        target = evidence / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        hashes[relative] = sha(target.read_bytes())
    (evidence / 'hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n')
    return hashes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('work', type=Path); p.add_argument('--archives', type=Path)
    p.add_argument('--manifest', type=Path, required=True)
    i = sub.add_parser('identity'); i.add_argument('work', type=Path); i.add_argument('--manifest', type=Path, required=True)
    i.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('analyze'); a.add_argument('work', type=Path); a.add_argument('--output', type=Path, required=True)
    c = sub.add_parser('collect'); c.add_argument('work', type=Path); c.add_argument('--evidence', type=Path, required=True)
    c.add_argument('--extra-dir', type=Path)
    r = sub.add_parser('record'); r.add_argument('evidence', type=Path); r.add_argument('--run-id', type=int, required=True)
    r.add_argument('--artifact-id', type=int, required=True); r.add_argument('--artifact-zip', type=Path, required=True)
    r.add_argument('--servo', action='store_true', help='adopt a servo-node run as the D1 servo record')
    k = sub.add_parser('check-record')
    args = parser.parse_args(argv)
    if args.command == 'record':
        build, path, md, render = ((build_servo_record, SERVO_RECORD, SERVO_RECORD_MD, render_servo_markdown) if args.servo
                                   else (build_record, RECORD, RECORD_MD, render_markdown))
        record = build(args.evidence, args.run_id, args.artifact_id, args.artifact_zip)
        path.write_text(json.dumps(record, indent=2) + '\n')
        md.write_text(render(record))
        return 0
    if args.command == 'check-record':
        for path, md, render in ((RECORD, RECORD_MD, render_markdown), (SERVO_RECORD, SERVO_RECORD_MD, render_servo_markdown)):
            if md.read_text() != render(json.loads(path.read_text())):
                print(f'FAIL: {md.name} does not match {path.name}', file=sys.stderr)
                return 1
        print('PASS: D1 reference and servo records agree with their prose (not electrical acceptance)')
        return 0
    if args.command == 'prepare':
        try:
            manifest = prepare(args.work, args.archives)
        except NotRun as error:
            args.manifest.write_text(json.dumps({'status': NOT_RUN, 'reason': str(error)}, indent=2) + '\n')
            print(f'NOT RUN: {error}', file=sys.stderr)
            return 2
        except ValueError as error:
            args.manifest.write_text(json.dumps({'status': 'FAILED', 'reason': str(error)}, indent=2) + '\n')
            print(f'FAILED: {error}', file=sys.stderr)
            return 2
        manifest['status'] = 'PREPARED'
        args.manifest.write_text(json.dumps(manifest, indent=2) + '\n')
        return 0
    if args.command == 'identity':
        result = identity(single_run(args.work), json.loads(args.manifest.read_text()))
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(result['status'])
        return 0 if result['status'] == 'REPRODUCED' else 3
    if args.command == 'collect':
        collect(args.work, args.evidence, args.extra_dir)
        return 0
    result = analyze(single_run(args.work))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
