#!/usr/bin/env python3
"""D2 passive discharge across OSC's independent per-rail load corners (OSC reply 2026-11-14 JST, Q6/Q7).

OSC commits only to a per-rail load between 0 mA and the contract maximum, independently per rail. This evaluates
the existing closed-form, ideal-simultaneous-disconnect decay (interface_diagnostics.evaluate_discharge) at
0 / planning / maximum load per analog rail and 0 / maximum on +5 V, with "absent" at the per-rail discharge level
OSC recommended (+12 V <= 0.5 V, -12 V <= 0.6 V). Loads are resistive equivalents at nominal voltage: an
ASSUMPTION, because IC behaviour below supply minimum is unspecified. CALCULATED, not simulated or measured.

usage: d2_load_corners.py [--output PATH]
"""

import argparse
import itertools
import json
import sys

import interface_diagnostics as idg

ABSENT_V = {'+12': 0.5, '-12': 0.6}               # OSC Q7 recommendation (per-rail discharge level); not yet recorded
PLANNING_A = {'+12': 1.5348, '-12': 1.4356}        # OSC Q6, AGND-referred planning totals at nominal (information only)
MAXIMUM_A = {'+12': 2.1, '-12': 2.0, '+5': 0.5}    # contract maxima (OSC Q6 commitment upper bound)
NOMINAL_V = {'+12': 12.0, '-12': 12.0, '+5': 5.0}
CORNERS = {'+12': ('0', 'planning', 'maximum'), '-12': ('0', 'planning', 'maximum'), '+5': ('0', 'maximum')}


def load_ohm(rail, corner):
    amps = {'0': None, 'planning': PLANNING_A.get(rail), 'maximum': MAXIMUM_A[rail]}[corner]
    return None if amps is None else NOMINAL_V[rail] / amps


def rvee(v12, vn):
    return ((abs(vn) <= ABSENT_V['-12'] and v12 > idg.P12_WHILE_M12_ABSENT_MAX)
            or (abs(v12) <= ABSENT_V['+12'] and abs(vn) > idg.M12_WHILE_P12_ABSENT_MAX))


def hazard(v12, vn, v5):
    one = ((abs(v12) <= ABSENT_V['+12'] and abs(vn) >= idg.ADG_OTHER_RAIL_MIN)
           or (abs(vn) <= ABSENT_V['-12'] and abs(v12) >= idg.ADG_OTHER_RAIL_MIN))
    return one and v5 > idg.P5_HOLD_MAX


def corners(calc=None):
    calc = idg.calculator() if calc is None else calc
    resistors = idg.discharge_resistors(calc)
    saved = idg.rvee_violation, idg.direct_hazard
    idg.rvee_violation = lambda v12, vn, _absent: rvee(v12, vn)
    idg.direct_hazard = lambda v12, vn, v5, _absent: hazard(v12, vn, v5)
    try:
        rows = []
        for a, b, c in itertools.product(CORNERS['+12'], CORNERS['-12'], CORNERS['+5']):
            loads = {r: load_ohm(r, k) for r, k in (('+12', a), ('-12', b), ('+5', c)) if load_ohm(r, k)}
            result = idg.evaluate_discharge(calc, loads, 'per-rail', resistors=resistors)
            rows.append({'corner': {'+12': a, '-12': b, '+5': c}, 'loads_ohm': {r: round(x, 4) for r, x in loads.items()},
                         'time_to_discharge_level_s': result['time_to_discharge_level_s'],
                         'first_rvee_violation': result['first_rvee_violation'],
                         'first_direct_hazard': result['first_direct_hazard']})
    finally:
        idg.rvee_violation, idg.direct_hazard = saved
    failing = [r for r in rows if r['first_rvee_violation'] or r['first_direct_hazard']]
    return {'record': 'D2 passive discharge across OSC per-rail load corners (CALCULATED; resistive-load ASSUMPTION; '
                      'ideal simultaneous disconnect)',
            'absent_v': ABSENT_V, 'discharge_resistors_ohm': resistors, 'corners': rows,
            'corners_total': len(rows), 'corners_failing': len(failing),
            'conclusion': ('Passive uncoupled discharge does not meet the voltage-form rows across OSC\'s committed '
                           'per-rail load range' if failing else 'No corner fails')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output')
    args = parser.parse_args(argv)
    out = corners()
    text = json.dumps(out, indent=2) + '\n'
    if args.output:
        open(args.output, 'w').write(text)
    print(f"{out['corners_failing']} of {out['corners_total']} corners fail: {out['conclusion']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
