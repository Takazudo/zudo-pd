"""Phase 30 desk current/width check of the B20 high-current paths on the JLC7628 4-layer stackup (nothing measured).

usage: python3 current-check.py <geom.json> <routes.json> <out.json>

For every trunk route.py laid (routes.json "trunks"), the widest path between its two pads through the routed copper
of the net (tracks, vias, pads, T-junctions) and the narrowest segment on it. The IPC-2221 chart formula
I = k x dT^0.44 x A^0.725 (A in mil^2; k 0.048 outer, 0.024 inner) gives the rise of that narrowest segment at the
rated load and at the limiter maximum, with 0.035 mm outer and 0.0175 mm inner copper. It treats the segment as a
long isolated conductor, which overstates the rise of short necks between large pads; parallel copper is not credited. Each layer change is also rated per via barrel (count of same-net vias within 1.3 mm).
"""
import heapq
import json
import math
import sys

CU_MM = {'F': 0.035, 'B': 0.035, 'In2': 0.0175}   # JLC7628: 1 oz outer, 0.5 oz inner (2 oz outer UNKNOWN)
K = {'F': 0.048, 'B': 0.048, 'In2': 0.024}
VIN = 19.0
# DC current of each path, A: rated load (1.2 / 0.8 / 0.5) and limiter maximum (2.1 / 2.0 / 0.5). VIN branches carry
# each stage's input power at VIN 19 V from thermal-check.py (maximum RDS corner); the inverter's D3-L6 path carries
# the inductor current, the rest the rail current.
RAIL = {'P12': (1.2, 2.1), 'P5': (0.5, 0.5), 'M12': (0.8, 2.0)}
VIN_BRANCH = {('J5.1', 'C1.1'): (1.54, 3.08), ('C1.1', 'C3.1'): (0.81, 1.44), ('C1.1', 'C7.1'): (0.15, 0.15),
              ('C1.1', 'CCIN1.1'): (0.57, 1.47)}
M12_RAW_A = (1.34, 3.35)
# Via barrel: 0.3 mm drill (route.py VIA_DRILL). Hole-wall copper 0.020 mm, the low end of "~20-25 um" in JLCPCB's blog
# "PCB plating thickness" (jlcpcb.com/blog/pcb-plating-thickness, read 2026-11-02; not a capabilities-page value). The
# barrel is rated as an outer conductor of its wall cross-section, a convention for a short, plane-coupled conductor.
VIA_DRILL_MM, VIA_WALL_MM, TWIN_R = 0.3, 0.020, 1.3


def via_rise(i):
    a_mil2 = math.pi * VIA_DRILL_MM * VIA_WALL_MM / 0.0254 ** 2
    return (i / (K['F'] * a_mil2 ** 0.725)) ** (1 / 0.44)


# Stage hot-loop copper (route.py stage templates). Every branch of a switching cell carries at most the inductor RMS
# current, sqrt(IL^2 + dI^2/12): IL is the rail current (buck) or the inverter inductor current, dI the
# calculate-board-b20-draft.py ripple maximum. A bound, not each branch's own RMS.
STAGE_CELLS = {'+12': ('U1', 'C3', 'D1', 'L1'), '+5': ('U2', 'C7', 'D2', 'L3'), '-12': ('U3', 'CCIN1', 'D3', 'L5')}
IL = {'+12': (1.2, 2.1), '+5': (0.5, 0.5), '-12': (1.335, 3.348)}
RIPPLE_PP = {'+12': 1.2562, '+5': 0.809, '-12': 1.4754}


def cell_paths():
    for stage, (ic, cin, d, ind) in STAGE_CELLS.items():
        irms = tuple(round(math.sqrt(i * i + RIPPLE_PP[stage] ** 2 / 12), 3) for i in IL[stage])
        for name, a, b in (('SW pin to diode', f'{ic}.8', f'{d}.1'), ('diode to inductor', f'{d}.1', f'{ind}.1'),
                           ('diode return to CIN', f'{d}.2', f'{cin}.2'), ('CIN return to IC pad', f'{cin}.2', f'{ic}.9'),
                           ('CIN to VIN pin', f'{cin}.1', f'{ic}.2')):
            yield stage, name, a, b, irms


def current(net, a, b):
    if net == 'VIN':
        return VIN_BRANCH[(a, b)]
    if net == 'M12_RAW':
        return M12_RAW_A
    return RAIL[net.split('_')[0]]


def rise(i, w_mm, layer):
    a_mil2 = (w_mm / 0.0254) * (CU_MM[layer] / 0.0254)
    return (i / (K[layer] * a_mil2 ** 0.725)) ** (1 / 0.44)


def seg_dist(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    t = 0 if n == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / n))
    return math.dist(q, (a[0] + t * dx, a[1] + t * dy))


def key(p):
    return (round(p[0], 3), round(p[1], 3))


def graph(net, geom, routes):
    adj = {}

    def add(u, v, w, info):
        adj.setdefault(u, []).append((v, w, info))
        adj.setdefault(v, []).append((u, w, info))
    tr = [t for t in routes['tracks'] if t['net'] == net]
    for t in tr:
        add(('n', t['layer'], key(t['a'])), ('n', t['layer'], key(t['b'])), t['w'], (t['layer'], t['w'], math.dist(t['a'], t['b'])))
    nodes = list(adj)
    for n in nodes:   # a branch that starts on another segment's body joins both of its ends
        for t in tr:
            if t['layer'] == n[1] and seg_dist(n[2], t['a'], t['b']) <= t['w'] / 2 + 0.01:
                for e in (t['a'], t['b']):
                    m = ('n', t['layer'], key(e))
                    if m != n:
                        add(n, m, t['w'], (t['layer'], t['w'], math.dist(n[2], e)))
    for v in routes['vias']:
        if v['net'] == net:
            for n in nodes:
                if math.dist(n[2], v['at']) < 0.05:
                    add(('v', key(v['at'])), n, 99.0, ('via', 99.0, 0.0, tuple(v['at'])))
    for p in geom['pads']:
        if p['net'] != net:
            continue
        b = p['bbox']
        for n in nodes:
            if (n[1] in p['layers'] or p['drill']) and b[0] - 0.15 <= n[2][0] <= b[2] + 0.15 and b[1] - 0.15 <= n[2][1] <= b[3] + 0.15:
                add(('p', p['ref'], p['num']), n, 99.0, ('pad', 99.0, 0.0))
    return adj


def widest(adj, src, dst):
    best, prev, pq, k = {src: 99.0}, {}, [(-99.0, 0, src)], 0
    while pq:
        w, _, u = heapq.heappop(pq)
        w = -w
        if u == dst:
            break
        if w < best.get(u, -1):
            continue
        for v, ww, info in adj.get(u, []):
            nw = min(w, ww)
            if nw > best.get(v, -1):
                best[v], prev[v] = nw, (u, info)
                k += 1
                heapq.heappush(pq, (-nw, k, v))
    if dst not in best:
        return None
    segs, u = [], dst
    while u in prev:
        u, info = prev[u]
        segs.append(info)
    bw = best[dst]
    neck = [s for s in segs if s[1] == bw]
    via_at = sorted({s[3] for s in segs if s[0] == 'via'})
    return {'via_at': via_at, 'narrowest_mm': bw, 'layers': sorted({s[0] for s in neck}), 'narrow_length_mm': round(sum(s[2] for s in neck), 2),
            'path_layers': sorted({s[0] for s in segs if s[0] != 'pad' and s[0] != 'via'}),
            'path_length_mm': round(sum(s[2] for s in segs), 2)}


def main():
    geom, routes = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
    pads = {}
    for p in geom['pads']:
        k = (p['ref'], p['num'])
        if k not in pads or (p['bbox'][2] - p['bbox'][0]) * (p['bbox'][3] - p['bbox'][1]) > \
                (pads[k]['bbox'][2] - pads[k]['bbox'][0]) * (pads[k]['bbox'][3] - pads[k]['bbox'][1]):
            pads[k] = p
    rows, graphs = [], {}
    for t in routes.get('trunks', []):
        net = t['net']
        adj = graphs.setdefault(net, graph(net, geom, routes))
        a, b = t['from'].split('.'), t['to'].split('.')
        res = widest(adj, ('p', *a), ('p', *b))
        i_rated, i_max = current(net, t['from'], t['to'])
        row = {'net': net, 'from': t['from'], 'to': t['to'], 'trunk_width_mm': t['width_mm'],
               'current_a': {'rated': i_rated, 'limiter_max': i_max}}
        if res is None:
            row['status'] = 'NOT CONNECTED'
        else:
            lay = 'In2' if 'In2' in res['layers'] else res['layers'][0]
            via_at = res.pop('via_at')
            row.update(res)
            # each layer change on the path, with the same-net vias the router twinned beside it (route.py via_twins)
            counts = [sum(1 for v in routes['vias'] if v['net'] == net and math.dist(v['at'], c) <= TWIN_R) for c in via_at]
            if counts:
                row['via_transitions'] = [{'at': list(c), 'vias': n} for c, n in zip(via_at, counts)]
                worst = min(counts)
                row['via_rise_k'] = {'rated': round(via_rise(i_rated / worst), 1), 'limiter_max': round(via_rise(i_max / worst), 1)}
            row['rise_k'] = {'rated': round(rise(i_rated, res['narrowest_mm'], lay), 1),
                             'limiter_max': round(rise(i_max, res['narrowest_mm'], lay), 1)}
        rows.append(row)
    cells = []
    for stage, name, a, b, (i_rated, i_max) in cell_paths():
        net = pads[tuple(a.split('.'))]['net']
        adj = graphs.setdefault(net, graph(net, geom, routes))
        res = widest(adj, ('p', *a.split('.')), ('p', *b.split('.')))
        row = {'stage': stage, 'branch': name, 'net': net, 'from': a, 'to': b, 'current_bound_a': {'rated': i_rated, 'limiter_max': i_max}}
        if res is None:
            row['status'] = 'NO TRACK PATH (pads abut or join through a pour)'
        else:
            res.pop('via_at')
            row.update(res)
            lay = 'In2' if 'In2' in res['layers'] else res['layers'][0]
            row['rise_k'] = {'rated': round(rise(i_rated, res['narrowest_mm'], lay), 1),
                             'limiter_max': round(rise(i_max, res['narrowest_mm'], lay), 1)}
        cells.append(row)
    json.dump({'_comment': __doc__.strip().splitlines()[0], 'copper_mm': CU_MM, 'paths': rows, 'stage_cells': cells},
              open(sys.argv[3], 'w'), indent=1)
    for c in cells:
        print(c['stage'], c['branch'], c['net'], c['from'], c['to'], c.get('narrowest_mm'), c.get('narrow_length_mm'), c.get('rise_k', c.get('status')))
    for r in rows:
        print(r['net'], r['from'], r['to'], r.get('narrowest_mm'), r.get('layers'), r.get('narrow_length_mm'), r.get('rise_k', r.get('status')),
              [v['vias'] for v in r.get('via_transitions', [])], r.get('via_rise_k', ''))


if __name__ == '__main__':
    main()
