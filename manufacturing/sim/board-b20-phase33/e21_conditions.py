#!/usr/bin/env python3
"""Read the identity nom / adv waveforms against OSC E21 (zudo-osc-hole-field 512e1ec, pd-interface-20v.md section 5).

E21 replaces the no-load in-region slope ceilings with a current limit (-12 V <= 350 mA while |V| <= 0.75 V, +5 V
<= 180 mA while V <= 0.45 V) under four conditions. This reads condition 3 from the waveforms, under two readings
of "ramp start" because E21 does not define it:
  rail start       the first sample where the rail's magnitude exceeds 0.2 V (above the pre-start bias of
                   about 0.05-0.15 V that the rails sit at before the ramp);
  reference start  the first sample where the rail's ideal tracking target (gain x per-rail RAMP reference) exceeds
                   50 mV.
The "normal tracking difference" is the median rail-minus-target over 15-25 ms after the rail start.
SIMULATION reading of recorded decks; judges no circuit margin by itself.

usage: e21_conditions.py LADDER_DIR --output PATH   (LADDER_DIR holds nom/ and adv/ from an identity run)
"""

import argparse
import json
from pathlib import Path
import statistics
import sys

from analysis_inputs import load
from extract_reference import deck_gain, load_reference

WINDOW_S = (40e-3, 234.5e-3)
RAIL_START_V = 0.2
REFERENCE_START_V = 0.050
NORMAL_WINDOW_S = (15e-3, 25e-3)
RETURN_TOLERANCE_V = 0.010
LEAD_LIMIT_V = 0.25
RETURN_LIMIT_S = 15e-3
CURRENT_LIMIT_A = {'+5': 0.180, '-12': 0.350}
RAILS = (('+12', 1, 1, 'ramp_p12'), ('+5', 2, 1, 'ramp_p5'), ('-12', 3, -1, 'ramp_m12'))


def plus12_gain(deck):
    values = {}
    for line in deck.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] in ('RT12A', 'RT12B'):
            values[parts[0]] = float(parts[3].lower().replace('k', 'e3'))
    return 1 + values['RT12A'] / values['RT12B']


def gains(deck):
    return {'+12': plus12_gain(deck), '+5': deck_gain(deck, '+5'), '-12': deck_gain(deck, '-12')}


def first(times, flags):
    return next((t for t, f in zip(times, flags) if f), None)


def rail_reading(times, volts, targets):
    """volts and targets are rail magnitudes; returns the condition 3 quantities for one rail."""
    lo, hi = WINDOW_S
    keep = [k for k, t in enumerate(times) if lo <= t < hi]
    t = [times[k] for k in keep]
    v = [volts[k] for k in keep]
    e = [volts[k] - targets[k] for k in keep]
    tg = [targets[k] for k in keep]
    rail_start = first(t, [x > RAIL_START_V for x in v])
    reference_start = first(t, [x > REFERENCE_START_V for x in tg])
    out = {'rail_start_ms': rail_start * 1e3, 'reference_start_ms': reference_start * 1e3,
           'largest_reversal_v': max([0.0] + [a - b for a, b in zip(v, v[1:])])}
    normal = statistics.median(x for s, x in zip(t, e)
                               if rail_start + NORMAL_WINDOW_S[0] <= s <= rail_start + NORMAL_WINDOW_S[1])
    after = [(s, x) for s, x in zip(t, e) if rail_start <= s <= rail_start + NORMAL_WINDOW_S[1]]
    lead_t, lead = max(after, key=lambda p: p[1])
    off = [s for s, x in after if s >= lead_t and abs(x - normal) > RETURN_TOLERANCE_V]
    returned = off[-1] if off else lead_t
    out.update({'largest_lead_v': lead, 'largest_lead_at_ms': lead_t * 1e3, 'normal_difference_v': normal,
                'returned_at_ms': returned * 1e3,
                'return_after_rail_start_ms': (returned - rail_start) * 1e3,
                'return_after_reference_start_ms': (returned - reference_start) * 1e3})
    out['lead_within'] = lead <= LEAD_LIMIT_V
    out['return_within_from_rail_start'] = returned - rail_start <= RETURN_LIMIT_S
    out['return_within_from_reference_start'] = returned - reference_start <= RETURN_LIMIT_S
    return out


def case(directory, name):
    rows = load(Path(directory) / f'{name}.dat')
    ref = load_reference(Path(directory) / f'{name}-ref.txt', rows)
    g = gains((Path(directory) / f'{name}.cir').read_text())
    times = [r[0] for r in rows]
    out = {}
    for rail, index, sign, vector in RAILS:
        volts = [sign * r[index] for r in rows]
        targets = [g[rail] * x[vector] for x in ref]
        out[rail] = rail_reading(times, volts, targets)
    return out


def currents(metrics):
    """E21 current rows from recorded osc_bank.rail_metrics rows: {deck: {rail: metrics}}."""
    out = {}
    for deck, rails in metrics.items():
        for rail, limit in CURRENT_LIMIT_A.items():
            value = rails[rail]['peak_current_in_region_a']
            out[f'{deck} {rail}'] = {'peak_current_in_region_a': value, 'limit_a': limit, 'within': value <= limit}
    return out


def analyze(ladder, metrics):
    cases = {name: case(Path(ladder) / name, name) for name in ('nom', 'adv')}
    rails = [r for c in cases.values() for rail, r in c.items() if rail != '+12']
    return {'record': 'E21 condition 3 and current rows on the identity nom / adv decks (SIMULATION)',
            'e21_source': 'Takazudo/zudo-osc-hole-field 512e1ec2db2c4e344d56a4c6d985fcc3a209cbfb',
            'cases': cases, 'currents': currents(metrics),
            'condition3_rail_start_reading': all(r['lead_within'] and r['return_within_from_rail_start']
                                                 and r['largest_reversal_v'] < 1e-3 for r in rails),
            'condition3_reference_start_reading': all(r['lead_within'] and r['return_within_from_reference_start']
                                                      and r['largest_reversal_v'] < 1e-3 for r in rails)}


def pinned_metrics(cross_check_json):
    data = json.loads(Path(cross_check_json).read_text())
    out = {}
    for lbl, deck in (('abstol-nom', 'nom'), ('abstol-adv', 'adv')):
        diff = data['pairs'][lbl]['difference']
        out[deck] = {rail: {k: row['pinned'] for k, row in values.items()} for rail, values in diff.items()}
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('ladder')
    parser.add_argument('--metrics', default=Path(__file__).with_name('d1-variant-cross-check-20261113.json'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    out = analyze(args.ladder, pinned_metrics(args.metrics))
    Path(args.output).write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('condition3_rail_start_reading', 'condition3_reference_start_reading')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
