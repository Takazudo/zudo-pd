#!/usr/bin/env python3
"""Post-hoc, NOT pre-registered: the reviewer's routed-parasitic resistance corners on the worst decks of set G.

usage: d2_threshold_posthoc.py prepare|run|analyze   (work/posthoc, output work/posthoc.json)
"""
import json
import sys
from pathlib import Path

import d2_threshold_band as tb
import d2_threshold_sets as ts

R = json.load(open(__import__('pathlib').Path(__file__).resolve().parents[3] / 'manufacturing/verification/pd20-native-d2-layout-20261114/review-20261120/sensitivity.json'))['resistance_corners']
WORST = [('hlrh', 'phnlfl', 'zmz', 'pl-ne'), ('hlrl', 'phnlfl', 'zmz', 'pl-ne'), ('hhrh', 'phnlfl', 'zmz', 'pl-ne'),
         ('hlrh', 'phnlfh', 'zmm', 'pl-ne'), ('hhrl', 'plnhfh', 'mzm', 'pe-nl'), ('hhrl', 'ceil', 'mzp', 'pe-nl'),
         ('hhrh', 'plnhfl', 'mzz', 'pe-nl'), ('hlrl', 'plnhfh', 'mzm', 'pe-nl')]
RSTATE = {'pl-ne': {'+12': 'slow', '-12': 'fast', '+5': 'fast'}, 'pe-nl': {'+12': 'fast', '-12': 'slow', '+5': 'fast'}}
KEY = {'fast': 'switch_min_ohm', 'slow': 'switch_max_ohm'}


def parasitic(text, edge):
    for rail, rx, rcl in (('+12', 'RXD12 d12a d12b 0.5', 'RCL12 cl12 0 50m'), ('+5', 'RXD5 d5a d5b 0.5', 'RCL5 cl5 0 50m'),
                          ('-12', 'RXDN dna dnb 1.5', 'RCLN cln m12_out 50m')):
        state = RSTATE[edge][rail]
        text = tb.rep(text, rx, rx.rsplit(' ', 1)[0] + f' {R[rail][KEY[state]]:.6g}')
        if state == 'slow':
            text = tb.rep(text, rcl, rcl.rsplit(' ', 1)[0] + f" {0.05 + R[rail]['bank_side_hot_ohm']['J11']:.6g}")
    return text


def cases():
    out = {}
    for combo, bank, loads, edge in WORST:
        label, c = tb.case('C1', combo, bank, loads, edge, ts.DRIVE, tag='-par')
        out[label] = c
    return out


if __name__ == '__main__':
    run = Path(tb.HERE / 'work' / 'posthoc')
    if sys.argv[1] == 'prepare':
        tb.SETS['posthoc'] = cases
        tb.prepare(run, 'posthoc')
        for label, c in cases().items():
            p = run / label / 'nomR.cir'
            p.write_text(parasitic(p.read_text(), c['edge']))
    elif sys.argv[1] == 'run':
        sys.exit(tb.run(run))
    else:
        out = tb.analyze(run)
        (tb.HERE / 'work' / 'posthoc.json').write_text(json.dumps(out, indent=1, default=str) + '\n')
        for k, r in out['cases'].items():
            print(k, r['status'], r.get('pass'), round(r['min_abs_m12_while_p12_present'], 3), round(r['max_abs_m12_once_p12_absent'], 3))
