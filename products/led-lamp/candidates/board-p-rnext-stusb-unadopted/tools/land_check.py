"""Compare the r-next footprints of the 9 new parts with the manufacturer land drawings.

Expected values are transcribed from the hashed primary datasheets (see LANDS below:
document, PDF page, drawing). Every check is pad geometry read from the .kicad_mod;
nothing is fitted or rounded beyond TOL. Result per check: MATCH or DIFF.
Pin identity (pad numbers present = datasheet pins) is checked separately in pin maps.
Usage: python3 .../tools/land_check.py > .../checks/land-check.json
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
LIBS = {
    'zudo-pd': os.path.join(HERE, 'footprints/zudo-pd.pretty'),
    'rnext-mfr': os.path.join(HERE, 'footprints/rnext-mfr.pretty'),
    'zudo-led-lamp': os.path.join(ROOT, 'footprints/kicad/zudo-led-lamp.pretty'),
    'husb-candidate': os.path.join(ROOT, 'candidates/board-p-v196-unadopted/libraries/husb-candidate.pretty'),
    'monitor-candidate': os.path.join(ROOT, 'candidates/board-p-v196-unadopted/libraries/monitor-candidate.pretty'),
}
TOL = 0.011  # mm; drawings give 0.01 mm resolution at best
PAD = re.compile(r'\(pad "?([^"\s]*)"? (smd|thru_hole|np_thru_hole|connect) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\(size ([-\d.]+) ([-\d.]+)\)')


def pads(fp):
    lib, name = fp.split(':', 1)
    text = open(os.path.join(LIBS[lib], name + '.kicad_mod')).read()
    out = {}
    for m in PAD.finditer(text):
        num, _kind, shape, x, y, rot, w, h = m.groups()
        if not num:
            continue  # unnumbered helper pads of a custom pad
        rot = float(rot or 0) % 180
        w, h = float(w), float(h)
        if abs(rot - 90) < 1e-6:
            w, h = h, w
        out.setdefault(num, []).append({'x': float(x), 'y': float(y), 'w': w, 'h': h, 'shape': shape})
    return {k: v[0] for k, v in out.items()}


def size(p):
    return sorted((round(p['w'], 4), round(p['h'], 4)))


def dist(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])


# (refdes, footprint, source, locator, checks). Each check: (label, kind, args, expected)
# kinds: size (pad -> sorted [short, long]); pitch (pad a, pad b -> centre distance);
# outer (pad a, pad b -> outer-edge distance along their joining axis); count (number of numbered pads)
LANDS = [
    ('U4', 'husb-candidate:TPS259474_RPW0010A_TI_EXAMPLE', 'TI SLVSFC9C sha256 8f96de38', 'PDF page 73, RPW0010A EXAMPLE BOARD LAYOUT 4225183/A', [
        ('pad count', 'count', (), 10),
        ('pads 2,3,8,9 length 8X (0.6) x width (0.25)', 'size', ('2',), [0.25, 0.6]),
        ('IN/OUT pads 5,6 2X (0.3) x (2.4)', 'size', ('5',), [0.3, 2.4]),
        ('pad columns 1-4 to 7-10 centre span (1.8)', 'pitch', ('2', '9'), 1.8),
        ('pads 5-6 centre spacing 2X (0.25)', 'pitch', ('5', '6'), 0.5),
        ('pads 2-3 centre spacing 2X (0.225)', 'pitch', ('2', '3'), 0.45),
    ]),
    ('U5', 'monitor-candidate:TPS3701_DDC0006A_DRAFT', 'TI SBVS240C sha256 27c94a6c', 'PDF page 26, DDC0006A EXAMPLE BOARD LAYOUT 4214841/E', [
        ('pad count', 'count', (), 6),
        ('pad 6X (1.1) x 6X (0.6)', 'size', ('1',), [0.6, 1.1]),
        ('pitch 4X (0.95)', 'pitch', ('1', '2'), 0.95),
        ('row centre span (2.7)', 'pitch', ('1', '6'), 2.7),
    ]),
    ('U3', 'zudo-pd:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL', 'TI SNOSD17G sha256 e16b3a8c', 'PDF page 34, DBV0006A EXAMPLE BOARD LAYOUT 4214840/G', [
        ('pad count', 'count', (), 6),
        ('pad 6X (1.1) x 6X (0.6)', 'size', ('1',), [0.6, 1.1]),
        ('pitch 2X (0.95)', 'pitch', ('1', '2'), 0.95),
        ('row centre span (2.6)', 'pitch', ('1', '6'), 2.6),
    ]),
    ('U2', 'zudo-pd:HTSSOP-20_PWP0020T_P0.65_EP2.96_TI-DRAFT', 'TI SLVSET9G sha256 8f91a0db', 'PDF page 42, PWP0020T EXAMPLE BOARD LAYOUT', [
        ('pad count', 'count', (), 21),
        ('pad 20X (1.5) x 20X (0.45)', 'size', ('1',), [0.45, 1.5]),
        ('pitch 18X (0.65)', 'pitch', ('1', '2'), 0.65),
        ('row centre span (5.8)', 'pitch', ('1', '20'), 5.8),
        ('thermal pad (2.96) x (2.96)', 'size', ('21',), [2.96, 2.96]),
    ]),
    ('D5', 'zudo-pd:WSON-6_L2.0-W2.0-P0.65-BL-EP', 'TI SLVSED5C sha256 84c986c9', 'PDF page 19, DRV0006A EXAMPLE BOARD LAYOUT 4222173/C', [
        ('pad count', 'count', (), 7),
        ('pad 6X (0.45) x 6X (0.3)', 'size', ('1',), [0.3, 0.45]),
        ('pitch 4X (0.65)', 'pitch', ('1', '2'), 0.65),
        ('row centre span (1.95)', 'pitch', ('1', '6'), 1.95),
        ('exposed pad 7 (1) x (1.6)', 'size', ('7',), [1.0, 1.6]),
    ]),
    ('Q3', 'zudo-pd:VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A', 'TI SLPS633 sha256 119cdef2', 'PDF page 9, 7.2 Q3A Recommended PCB Pattern', [
        ('pad count', 'count', (), 9),
        ('pads 1-4 4X (0.6) x 4X (0.3)', 'size', ('1',), [0.3, 0.6]),
        ('pitch 3X (0.65)', 'pitch', ('1', '2'), 0.65),
        ('drain pad 9 (1.775) x (2.45)', 'size', ('9',), [1.775, 2.45]),
    ]),
    ('Q1', 'zudo-pd:PowerDI3333-8_DMP3036SFG', 'Diodes DS37038 Rev. 6-2 sha256 7d68df47', 'PDF page 7, Suggested Pad Layout PowerDI3333-8 table', [
        ('pad count', 'count', (), 9),
        ('pad Y 0.700 x X 0.420', 'size', ('1',), [0.42, 0.7]),
        ('pitch C 0.650', 'pitch', ('1', '2'), 0.65),
        ('outer extent Y3 3.700', 'outer', ('1', '8'), 3.7),
        ('drain pad Y2 2.250 x X3 2.370', 'size', ('9',), [2.25, 2.37]),
    ]),
    ('Q5', 'zudo-pd:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR', 'Diodes DS30144 Rev. 25-2 sha256 c93dcb33', 'PDF page 5, Suggested Pad Layout SOT23 (Standard) table', [
        ('pad count', 'count', (), 3),
        ('pad X 0.8 x Y 0.9', 'size', ('1',), [0.8, 0.9]),
        ('row centre span C 2.0', 'rowspan', ('1', '3'), 2.0),
        ('outer extent Y1 2.9', 'outer', ('1', '3'), 2.9),
    ]),
    ('D8', 'zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD', 'Diodes DS18004 Rev. 38-2 sha256 0fbd7d13', 'PDF page 4, Suggested Pad Layout SOD123 table', [
        ('pad count', 'count', (), 2),
        ('pad X 0.900 x Y 0.950', 'size', ('1',), [0.9, 0.95]),
        ('outer extent X1 4.050', 'outer', ('1', '2'), 4.05),
    ]),
]
# The drafted replacements selected by board_p_rnext_spec.py, checked against the same drawings.
SELECTED = {'U3': 'rnext-mfr:SOT-23-6_DBV0006A_TI-EXAMPLE', 'D5': 'rnext-mfr:WSON-6_DRV0006A_TI-EXAMPLE',
            'D8': 'rnext-mfr:SOD-123_DIODES-SUGGESTED'}
LANDS += [(ref + ' (selected draft)', SELECTED[ref], src, loc, checks)
          for ref, _fp, src, loc, checks in list(LANDS) if ref in SELECTED]


def measure(p, kind, args):
    if kind == 'count':
        return len(p)
    if kind == 'size':
        return size(p[args[0]])
    a, b = p[args[0]], p[args[1]]
    if kind == 'pitch':
        return round(dist(a, b), 4)
    if kind == 'rowspan':
        return round(max(abs(a['x'] - b['x']), abs(a['y'] - b['y'])), 4)
    if kind == 'outer':
        dx, dy = abs(a['x'] - b['x']), abs(a['y'] - b['y'])
        return round(dx + (a['w'] + b['w']) / 2, 4) if dx >= dy else round(dy + (a['h'] + b['h']) / 2, 4)
    raise ValueError(kind)


def ok(got, want):
    if isinstance(want, list):
        return all(abs(g - w) <= TOL for g, w in zip(got, want))
    return abs(got - want) <= TOL


def main():
    out, diffs = [], 0
    for ref, fp, source, locator, checks in LANDS:
        p = pads(fp)
        rows = []
        for label, kind, args, want in checks:
            got = measure(p, kind, args)
            res = 'MATCH' if ok(got, want) else 'DIFF'
            diffs += res == 'DIFF'
            rows.append({'check': label, 'expected': want, 'footprint': got, 'result': res})
        out.append({'refdes': ref, 'footprint': fp, 'source': source, 'locator': locator,
                    'verdict': 'MATCH' if all(r['result'] == 'MATCH' for r in rows) else 'DIFF', 'checks': rows})
    json.dump({'tolerance_mm': TOL, 'diff_count': diffs, 'lands': out}, sys.stdout, indent=1)
    print()


if __name__ == '__main__':
    main()
