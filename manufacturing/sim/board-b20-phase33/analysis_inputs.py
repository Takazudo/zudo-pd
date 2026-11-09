"""Validate phase33 wrdata inputs; successful analysis is not simulation qualification."""
import argparse
import math
from pathlib import Path
import re
import sys

START_CASES = ('nom', 'adv', 'rev', 'nomR', 'advR', 'revR')
REENTRY_CASES = tuple(f're{k}{n}' for k in ('R', 'B') for n in (6, 10, 14, 20))


def selected_files(expected):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if not args.directory.is_dir():
        raise ValueError(f'{args.directory}: input directory does not exist')
    found = {p.stem for p in args.directory.glob('*.dat')}
    missing = set(expected) - found
    unknown = found - set(START_CASES + REENTRY_CASES)
    if missing or unknown:
        raise ValueError(f'{args.directory}: missing cases {sorted(missing)}; unknown cases {sorted(unknown)}')
    return [args.directory / f'{name}.dat' for name in sorted(expected)]


def spice_time(value):
    match = re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)([munp]?)', value.lower())
    if not match:
        raise ValueError(f'unsupported SPICE time {value!r}')
    return float(match[1]) * {'': 1, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12}[match[2]]


def load(path):
    path = Path(path)
    deck = path.with_suffix('.cir').read_text()
    tran = re.search(r'^\.tran\s+\S+\s+(\S+)\s+0\s+(\S+)(?:\s|$)', deck, re.M | re.I)
    if not tran:
        raise ValueError(f'{path.with_suffix(".cir")}: missing supported .tran stop/maxstep')
    stop, step = map(spice_time, tran.groups())
    if not (math.isfinite(stop) and math.isfinite(step) and stop > 0 and step > 0):
        raise ValueError(f'{path}: invalid .tran duration or step')
    if step > 50e-6:
        raise ValueError(f'{path}: .tran maxstep exceeds 50 us slope-analysis resolution')
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            values = [float(x) for x in line.split()]
        except ValueError as error:
            raise ValueError(f'{path}:{number}: nonnumeric waveform row') from error
        if len(values) != 22 or not all(map(math.isfinite, values)):
            raise ValueError(f'{path}:{number}: expected 22 finite wrdata columns')
        t = values[0]
        if any(abs(x - t) > 1e-10 for x in values[::2]):
            raise ValueError(f'{path}:{number}: wrdata time columns disagree')
        if rows and (t <= rows[-1][0] or t - rows[-1][0] > step * 1.01 + 1e-10):
            raise ValueError(f'{path}:{number}: time is not increasing or exceeds .tran maxstep')
        rows.append((t, *values[1::2]))
    if len(rows) < 2 or rows[0][0] > step or rows[-1][0] < stop - 1e-8:
        raise ValueError(f'{path}: empty or truncated waveform; expected coverage through {stop:g} s')
    return rows


def window(rows, start, stop, label):
    selected = [x for x in rows if start <= x[0] < stop]
    if len(selected) < 2:
        raise ValueError(f'{label}: required time window [{start:g}, {stop:g}) has fewer than two samples')
    return selected


def run(main):
    try:
        main()
    except (ValueError, OSError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)


def adjacent_slope_screen(rows, index, sign, normal_limit, no_load=False, exception=None):
    """Retain short excursions instead of treating a 50-100 us average as steepest slew.

    exception is (voltage ceiling, slope ceiling, capacitive-current ceiling).
    Source current is deliberately not used to approve a capacitive-current condition.
    A segment straddling the voltage boundary is unresolved, not silently waived.
    """
    peak = None
    negative_steps = []
    normal_exceedances = 0
    bound_exceedances = []
    boundary_segments = []
    for a, b in zip(rows, rows[1:]):
        dt = b[0] - a[0]
        require_increasing = dt > 0
        if not require_increasing:
            raise ValueError('adjacent slope requires increasing times')
        v0, v1 = sign * a[index], sign * b[index]
        delta = v1 - v0
        row = {'slope_v_per_ms': abs(delta) / dt / 1000,
               'start_ms': a[0] * 1000, 'end_ms': b[0] * 1000, 'interval_us': dt * 1e6,
               'voltage_start_v': v0, 'voltage_end_v': v1}
        if peak is None or row['slope_v_per_ms'] > peak['slope_v_per_ms']:
            peak = row
        if delta < 0:
            negative_steps.append(delta)
        if row['slope_v_per_ms'] <= normal_limit:
            continue
        normal_exceedances += 1
        if not no_load or exception is None:
            bound_exceedances.append(row)
        elif max(v0, v1) <= exception[0]:
            if row['slope_v_per_ms'] > exception[1]:
                bound_exceedances.append(row)
        elif min(v0, v1) >= exception[0]:
            bound_exceedances.append(row)
        else:
            boundary_segments.append(row)
    return {'method': 'absolute voltage difference / elapsed time on every adjacent saved sample; not a continuous-time bound',
            'normal_limit_v_per_ms': normal_limit, 'no_external_resistive_load_case': no_load,
            'exception': None if not no_load or exception is None else {
                'voltage_ceiling_v': exception[0], 'slope_ceiling_v_per_ms': exception[1],
                'capacitive_current_ceiling_a': exception[2], 'capacitive_current_evidence': 'NOT LOGGED in the main waveform; source current is not a substitute'},
            'maximum': peak, 'normal_limit_exceeding_segments': normal_exceedances,
            'recorded_bound_exceeding_segments': len(bound_exceedances),
            'worst_recorded_bound_exceedance': max(bound_exceedances, key=lambda r: r['slope_v_per_ms']) if bound_exceedances else None,
            'voltage_boundary_straddling_segments': len(boundary_segments),
            'largest_negative_step_v': min(negative_steps, default=0), 'negative_step_count': len(negative_steps),
            'disposition': ('EXCEEDS RECORDED SLOPE BOUND (SIM); convergence and design disposition required' if bound_exceedances else
                            'BOUNDARY STRADDLE REQUIRES REVIEW' if boundary_segments else
                            'NO ADJACENT-SAMPLE SLOPE EXCEEDANCE; not electrical acceptance')}
