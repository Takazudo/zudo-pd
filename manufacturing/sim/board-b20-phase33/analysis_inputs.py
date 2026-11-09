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
